"""Patient service — CRUD with ownership enforcement."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.models.analysis import (
    Conflict,
    ConflictStatus,
)
from app.models.patient import Patient, PatientIntake
from app.models.report import LabResult, Report
from app.models.user import User


async def create_patient(
    user: User,
    name: str,
    identifier: str | None,
    age: int | None,
    sex: str,
    db: AsyncSession,
) -> Patient:
    patient = Patient(
        owner_user_id=user.id,
        name=name,
        identifier=identifier,
        age=age,
        sex=sex,
    )
    db.add(patient)
    await db.flush()
    return patient


async def get_patient(patient_id: int, db: AsyncSession) -> Patient:
    result = await db.execute(
        select(Patient).options(selectinload(Patient.intake)).where(Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise NotFoundError("Patient not found.")
    return patient


async def list_patients(user: User, db: AsyncSession) -> list[dict]:
    """List patients for user with computed counts."""
    result = await db.execute(
        select(Patient)
        .options(selectinload(Patient.intake))
        .where(Patient.owner_user_id == user.id)
        .order_by(Patient.updated_at.desc())
    )
    patients = result.scalars().all()

    patient_data = []
    for p in patients:
        # Count reports
        rpt_count = await db.execute(
            select(func.count()).select_from(Report).where(Report.patient_id == p.id)
        )
        report_count = rpt_count.scalar() or 0

        # Count open conflicts
        conf_count = await db.execute(
            select(func.count()).select_from(Conflict)
            .where(Conflict.patient_id == p.id, Conflict.status == ConflictStatus.OPEN)
        )
        open_conflicts = conf_count.scalar() or 0

        # Count unverified lab results
        unverified = await db.execute(
            select(func.count()).select_from(LabResult)
            .join(Report)
            .where(Report.patient_id == p.id, LabResult.verified.is_(False))
        )
        pending_reviews = unverified.scalar() or 0

        patient_data.append({
            "id": p.id,
            "name": p.name,
            "identifier": p.identifier,
            "age": p.age,
            "sex": p.sex,
            "created_at": p.created_at,
            "intake": p.intake,
            "report_count": report_count,
            "open_conflicts": open_conflicts,
            "pending_reviews": pending_reviews,
        })

    return patient_data


async def update_patient(
    patient: Patient,
    data: dict,
    db: AsyncSession,
) -> Patient:
    for key, value in data.items():
        if value is not None and hasattr(patient, key):
            setattr(patient, key, value)
    await db.flush()
    return patient


async def delete_patient(patient: Patient, db: AsyncSession) -> None:
    await db.delete(patient)
    await db.flush()


async def upsert_intake(
    patient: Patient,
    symptoms: str | None,
    existing_conditions: str | None,
    allergies: str | None,
    medications: str | None,
    notes: str | None,
    db: AsyncSession,
) -> PatientIntake:
    result = await db.execute(
        select(PatientIntake).where(PatientIntake.patient_id == patient.id)
    )
    intake = result.scalar_one_or_none()

    if intake:
        intake.symptoms = symptoms
        intake.existing_conditions = existing_conditions
        intake.allergies = allergies
        intake.medications = medications
        intake.notes = notes
    else:
        intake = PatientIntake(
            patient_id=patient.id,
            symptoms=symptoms,
            existing_conditions=existing_conditions,
            allergies=allergies,
            medications=medications,
            notes=notes,
        )
        db.add(intake)

    await db.flush()
    return intake


async def get_intake(patient_id: int, db: AsyncSession) -> PatientIntake | None:
    result = await db.execute(
        select(PatientIntake).where(PatientIntake.patient_id == patient_id)
    )
    return result.scalar_one_or_none()
