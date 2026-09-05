"""Report API routes — upload, paste, process, results."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import authorize_patient_access, get_current_user
from app.core.errors import NotFoundError
from app.models.report import LabResult, Report
from app.models.user import User
from app.schemas.report import (
    LabResultResponse,
    LabResultUpdate,
    PasteReportRequest,
    ReportResponse,
)
from app.services.analysis_service import update_lab_result
from app.services.report_service import (
    create_report_from_file,
    create_report_from_text,
    generate_report_insights,
    get_report_with_results,
    list_patient_reports,
    process_report,
)

logger = structlog.get_logger()

router = APIRouter(tags=["reports"])


@router.post("/patients/{patient_id}/reports", response_model=ReportResponse, status_code=201)
async def upload_report(
    patient_id: int,
    file: UploadFile = File(...),
    report_date: str | None = Form(None),
    source_name: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await authorize_patient_access(patient_id, user, db)
    content = await file.read()
    await file.seek(0)
    settings = get_settings()

    logger.info(
        "api_report_upload_received",
        patient_id=patient.id,
        filename=file.filename,
        content_type=file.content_type,
        file_size=len(content),
    )

    report = await create_report_from_file(
        patient_id=patient.id,
        filename=file.filename or "upload",
        content=content,
        mime_type=file.content_type,
        max_size_bytes=settings.max_upload_bytes,
        db=db,
        report_date=report_date,
        source_name=source_name,
    )
    return ReportResponse.model_validate(report)


@router.post("/patients/{patient_id}/reports/paste", response_model=ReportResponse, status_code=201)
async def paste_report(
    patient_id: int,
    body: PasteReportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await authorize_patient_access(patient_id, user, db)
    report = await create_report_from_text(
        patient_id=patient.id,
        text=body.text,
        report_date=body.report_date,
        source_name=body.source_name,
        db=db,
    )
    return ReportResponse.model_validate(report)


@router.post("/reports/{report_id}/process", response_model=ReportResponse)
async def process(
    report_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_authorized_report(report_id, user, db)
    processed = await process_report(report, db)
    await db.commit()

    results_query = await db.execute(
        select(LabResult).where(LabResult.report_id == processed.id).order_by(LabResult.id)
    )
    labs = results_query.scalars().all()
    resp = ReportResponse.model_validate(processed)
    resp.lab_results = [LabResultResponse.model_validate(lab) for lab in labs]
    return resp


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_authorized_report(report_id, user, db)
    full = await get_report_with_results(report.id, db)
    return ReportResponse.model_validate(full)


@router.get("/patients/{patient_id}/reports", response_model=list[ReportResponse])
async def list_reports(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    reports = await list_patient_reports(patient_id, db)
    return [ReportResponse.model_validate(r) for r in reports]


@router.get("/reports/{report_id}/results", response_model=list[LabResultResponse])
async def get_results(
    report_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_authorized_report(report_id, user, db)
    full = await get_report_with_results(report.id, db)
    if not full:
        return []
    return [LabResultResponse.model_validate(lr) for lr in full.lab_results]


@router.patch("/lab-results/{lab_result_id}", response_model=LabResultResponse)
async def edit_lab_result(
    lab_result_id: int,
    body: LabResultUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership through report → patient chain
    from app.models.report import LabResult
    lr_result = await db.execute(
        select(LabResult).where(LabResult.id == lab_result_id)
    )
    lr = lr_result.scalar_one_or_none()
    if not lr:
        raise NotFoundError("Lab result not found.")

    await _get_authorized_report(lr.report_id, user, db)

    updated = await update_lab_result(
        lab_result_id,
        body.model_dump(exclude_unset=True),
        user.id,
        db,
    )
    return LabResultResponse.model_validate(updated)


@router.post("/reports/{report_id}/insights")
async def generate_insights(
    report_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await _get_authorized_report(report_id, user, db)
    full = await get_report_with_results(report.id, db)

    from app.models.patient import Patient, PatientIntake
    patient_res = await db.execute(select(Patient).where(Patient.id == report.patient_id))
    patient = patient_res.scalar_one_or_none()
    intake_res = await db.execute(select(PatientIntake).where(PatientIntake.patient_id == report.patient_id))
    intake = intake_res.scalar_one_or_none()

    # Build structured data for AI with full patient clinical context
    patient_data = {
        "patient": {
            "name": patient.name if patient else "Unknown",
            "identifier": patient.identifier if patient else None,
            "age": patient.age if patient else None,
            "sex": patient.sex if patient else None,
        },
        "intake": {
            "symptoms": intake.symptoms if intake else None,
            "existing_conditions": intake.existing_conditions if intake else None,
            "allergies": intake.allergies if intake else None,
            "medications": intake.medications if intake else None,
            "notes": intake.notes if intake else None,
        },
        "report_id": full.id,
        "report_date": str(full.report_date) if full.report_date else None,
        "source_name": full.source_name,
        "lab_results": [
            {
                "canonical_name": lr.canonical_name,
                "observed_value": lr.observed_value,
                "unit": lr.unit,
                "reference_range": lr.reference_range_text,
                "reference_status": lr.reference_status,
            }
            for lr in (full.lab_results or [])
        ],
    }

    insight = await generate_report_insights(full, patient_data, db)
    from app.schemas.analysis import InsightResponse
    return InsightResponse.model_validate(insight)


@router.get("/reports/{report_id}/provenance", response_model=list[dict])
async def get_report_provenance(
    report_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve provenance audit trail for all parameters in a report."""
    report = await _get_authorized_report(report_id, user, db)
    from app.models.analysis import Provenance
    from app.schemas.analysis import ProvenanceResponse

    result = await db.execute(
        select(Provenance).where(Provenance.source_report_id == report.id).order_by(Provenance.created_at.asc())
    )
    items = result.scalars().all()
    return [ProvenanceResponse.model_validate(p).model_dump(mode="json") for p in items]


@router.post("/reports/{report_id}/review")
async def submit_report_review(
    report_id: int,
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record clinician review decision and audit trail."""
    report = await _get_authorized_report(report_id, user, db)
    from app.models.analysis import ReviewHistory
    from app.models.report import ProcessingStatus
    from app.schemas.analysis import ReviewResponse

    new_status = body.get("status", "ACCEPTED")
    prev_status = report.processing_status
    if new_status in ["ACCEPTED", "VALIDATED"]:
        report.processing_status = ProcessingStatus.VALIDATED.value
    elif new_status in ["FLAGGED", "REVIEW_REQUIRED"]:
        report.processing_status = ProcessingStatus.REVIEW_REQUIRED.value
    elif new_status in ["REJECTED", "FAILED"]:
        report.processing_status = ProcessingStatus.FAILED.value

    review = ReviewHistory(
        patient_id=report.patient_id,
        entity_type="REPORT",
        entity_id=report.id,
        action="CLINICIAN_REVIEW",
        previous_value=prev_status,
        new_value=new_status,
        user_id=user.id,
    )
    db.add(review)
    await db.flush()
    return ReviewResponse.model_validate(review).model_dump(mode="json")


async def _get_authorized_report(report_id: int, user: User, db: AsyncSession) -> Report:
    """Load report and verify user owns the patient."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundError("Report not found.")
    await authorize_patient_access(report.patient_id, user, db)
    return report
