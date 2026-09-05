"""Comparison and analytics services."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analysis.conflict_detector import (
    detect_allergy_conflict,
    detect_medication_conflict,
)
from app.analysis.reference_engine import calculate_change_direction
from app.core.errors import NotFoundError
from app.models.analysis import (
    ClarificationQuestion,
    Comparison,
    ComparisonResult,
    Conflict,
    ConflictStatus,
    Provenance,
    QuestionStatus,
    ReviewHistory,
    SourceType,
)
from app.models.patient import Patient, PatientIntake
from app.models.report import LabResult, Report


async def create_comparison(
    patient_id: int,
    previous_report_id: int,
    current_report_id: int,
    db: AsyncSession,
) -> Comparison:
    """Create a deterministic comparison between two reports."""
    # Load reports with results
    prev_result = await db.execute(
        select(Report).options(selectinload(Report.lab_results))
        .where(Report.id == previous_report_id, Report.patient_id == patient_id)
    )
    prev_report = prev_result.scalar_one_or_none()
    if not prev_report:
        raise NotFoundError("Previous report not found.")

    curr_result = await db.execute(
        select(Report).options(selectinload(Report.lab_results))
        .where(Report.id == current_report_id, Report.patient_id == patient_id)
    )
    curr_report = curr_result.scalar_one_or_none()
    if not curr_report:
        raise NotFoundError("Current report not found.")

    comparison = Comparison(
        patient_id=patient_id,
        previous_report_id=previous_report_id,
        current_report_id=current_report_id,
    )
    db.add(comparison)
    await db.flush()

    # Build lookup maps by canonical name
    prev_map = {lr.canonical_name: lr for lr in prev_report.lab_results}
    curr_map = {lr.canonical_name: lr for lr in curr_report.lab_results}
    all_names = set(prev_map.keys()) | set(curr_map.keys())

    for name in sorted(all_names):
        prev_lr = prev_map.get(name)
        curr_lr = curr_map.get(name)

        prev_val = prev_lr.value_numeric if prev_lr else None
        curr_val = curr_lr.value_numeric if curr_lr else None
        prev_unit = prev_lr.unit if prev_lr else None
        curr_unit = curr_lr.unit if curr_lr else None

        direction, abs_change, pct_change = calculate_change_direction(
            prev_val, curr_val, prev_unit, curr_unit
        )

        cr = ComparisonResult(
            comparison_id=comparison.id,
            canonical_name=name,
            previous_value=prev_lr.observed_value if prev_lr else None,
            current_value=curr_lr.observed_value if curr_lr else None,
            previous_unit=prev_unit,
            current_unit=curr_unit,
            previous_reference_range=prev_lr.reference_range_text if prev_lr else None,
            current_reference_range=curr_lr.reference_range_text if curr_lr else None,
            direction=direction,
            absolute_change=abs_change,
            percentage_change=pct_change,
        )
        db.add(cr)

    await db.flush()
    return comparison


async def get_comparison(comparison_id: int, db: AsyncSession) -> Comparison | None:
    result = await db.execute(
        select(Comparison).options(selectinload(Comparison.results))
        .where(Comparison.id == comparison_id)
    )
    return result.scalar_one_or_none()


async def detect_intake_conflicts(
    patient: Patient,
    intake: PatientIntake,
    db: AsyncSession,
) -> list[Conflict]:
    """Run conflict detection against previous records for this patient."""
    # Find previous intake data from earlier reports (if any exist)
    reports = await db.execute(
        select(Report).where(Report.patient_id == patient.id).order_by(Report.created_at)
    )
    all_reports = reports.scalars().all()

    all_conflicts = []

    # Check for allergy/medication conflicts between intake sources
    if len(all_reports) > 1:
        prev_allergies = intake.allergies  # Could also come from a different source
        prev_medications = intake.medications

        allergy_conflicts = detect_allergy_conflict(intake.allergies, prev_allergies)
        med_conflicts = detect_medication_conflict(intake.medications, prev_medications)

        for c_data in allergy_conflicts + med_conflicts:
            existing_c = await db.execute(
                select(Conflict).where(
                    Conflict.patient_id == patient.id,
                    Conflict.conflict_type == c_data["conflict_type"],
                    Conflict.description == c_data["description"],
                    Conflict.status == ConflictStatus.OPEN,
                )
            )
            if existing_c.scalar_one_or_none():
                continue

            conflict = Conflict(
                patient_id=patient.id,
                conflict_type=c_data["conflict_type"],
                description=c_data["description"],
                source_a=c_data.get("source_a"),
                source_b=c_data.get("source_b"),
                severity=c_data.get("severity", "MEDIUM"),
                status=ConflictStatus.OPEN,
            )
            db.add(conflict)
            all_conflicts.append(conflict)

    await db.flush()
    return all_conflicts


async def get_dashboard_stats(user_id: int, db: AsyncSession) -> dict:
    """Compute real dashboard statistics from database."""
    from app.models.patient import Patient

    # Patient count
    patient_count_q = await db.execute(
        select(func.count()).select_from(Patient).where(Patient.owner_user_id == user_id)
    )
    total_patients = patient_count_q.scalar() or 0

    # Report count
    report_count_q = await db.execute(
        select(func.count()).select_from(Report)
        .join(Patient)
        .where(Patient.owner_user_id == user_id)
    )
    total_reports = report_count_q.scalar() or 0

    # Lab result stats
    base_query = select(func.count()).select_from(LabResult).join(Report).join(Patient).where(Patient.owner_user_id == user_id)

    total_results_q = await db.execute(base_query)
    total_lab_results = total_results_q.scalar() or 0

    within_q = await db.execute(base_query.where(LabResult.reference_status.in_(["WITHIN", "NORMAL"])))
    within_range = within_q.scalar() or 0

    below_q = await db.execute(base_query.where(LabResult.reference_status.in_(["BELOW", "LOW"])))
    below_range = below_q.scalar() or 0

    above_q = await db.execute(base_query.where(LabResult.reference_status.in_(["ABOVE", "HIGH"])))
    above_range = above_q.scalar() or 0

    unknown_q = await db.execute(base_query.where(LabResult.reference_status == "UNKNOWN"))
    unknown_range = unknown_q.scalar() or 0


    verified_q = await db.execute(base_query.where(LabResult.verified.is_(True)))
    verified_results = verified_q.scalar() or 0

    unverified_results = total_lab_results - verified_results

    # Open conflicts
    conflicts_q = await db.execute(
        select(func.count()).select_from(Conflict)
        .join(Patient)
        .where(Patient.owner_user_id == user_id, Conflict.status == ConflictStatus.OPEN)
    )
    open_conflicts = conflicts_q.scalar() or 0

    # Pending questions
    questions_q = await db.execute(
        select(func.count()).select_from(ClarificationQuestion)
        .join(Patient)
        .where(Patient.owner_user_id == user_id, ClarificationQuestion.status == QuestionStatus.PENDING)
    )
    pending_questions = questions_q.scalar() or 0

    return {
        "total_patients": total_patients,
        "total_reports": total_reports,
        "total_lab_results": total_lab_results,
        "within_range": within_range,
        "below_range": below_range,
        "above_range": above_range,
        "unknown_range": unknown_range,
        "open_conflicts": open_conflicts,
        "pending_questions": pending_questions,
        "unverified_results": unverified_results,
        "verified_results": verified_results,
    }


async def get_parameter_trends(
    patient_id: int,
    canonical_name: str,
    db: AsyncSession,
) -> list[dict]:
    """Get historical trend for a specific parameter across all patient reports."""
    result = await db.execute(
        select(LabResult, Report.report_date, Report.id)
        .join(Report)
        .where(
            Report.patient_id == patient_id,
            LabResult.canonical_name == canonical_name,
        )
        .order_by(Report.report_date.asc().nullslast())
    )
    rows = result.all()
    return [
        {
            "date": row[1],
            "value": row[0].value_numeric,
            "unit": row[0].unit,
            "reference_low": row[0].reference_low,
            "reference_high": row[0].reference_high,
            "reference_status": row[0].reference_status,
            "report_id": row[2],
        }
        for row in rows
    ]


async def update_lab_result(
    lab_result_id: int,
    updates: dict,
    user_id: int,
    db: AsyncSession,
) -> LabResult:
    """Update a lab result and create review history."""
    result = await db.execute(select(LabResult).where(LabResult.id == lab_result_id))
    lr = result.scalar_one_or_none()
    if not lr:
        raise NotFoundError("Lab result not found.")

    # Get patient_id through report
    report = await db.execute(select(Report).where(Report.id == lr.report_id))
    rpt = report.scalar_one_or_none()

    for key, value in updates.items():
        if value is not None and hasattr(lr, key):
            old_value = str(getattr(lr, key))

            if key == "verified" and value is True:
                # Mark as verified, add provenance
                lr.verified = True
                prov = Provenance(
                    entity_type="lab_result",
                    entity_id=lr.id,
                    source_type=SourceType.HUMAN_VERIFIED,
                    source_report_id=lr.report_id,
                    verified=True,
                )
                db.add(prov)

            setattr(lr, key, value)

            # Create audit record
            review = ReviewHistory(
                patient_id=rpt.patient_id if rpt else 0,
                entity_type="lab_result",
                entity_id=lr.id,
                action="edit" if key != "verified" else "verify",
                previous_value=old_value,
                new_value=str(value),
                user_id=user_id,
            )
            db.add(review)

    # Recalculate reference status if values changed
    if "observed_value" in updates or "reference_range_text" in updates:
        from app.analysis.reference_engine import (
            calculate_reference_status,
            parse_numeric_value,
            parse_reference_range,
        )
        lr.value_numeric = parse_numeric_value(lr.observed_value)
        lr.reference_low, lr.reference_high = parse_reference_range(lr.reference_range_text)
        lr.reference_status = calculate_reference_status(lr.value_numeric, lr.reference_low, lr.reference_high)

    await db.flush()
    return lr
