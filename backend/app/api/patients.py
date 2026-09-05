"""Patient API routes with ownership authorization."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import authorize_patient_access, get_current_user
from app.models.user import User
from app.schemas.patient import (
    IntakeCreate,
    IntakeResponse,
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)
from app.services.patient_service import (
    create_patient,
    delete_patient,
    get_intake,
    list_patients,
    update_patient,
    upsert_intake,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientListResponse])
async def list_all(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await list_patients(user, db)
    return data


@router.post("", response_model=PatientResponse, status_code=201)
async def create(
    body: PatientCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await create_patient(user, body.name, body.identifier, body.age, body.sex, db)
    intake_record = None
    if any([body.symptoms, body.existing_conditions, body.allergies, body.medications, body.notes]):
        intake_record = await upsert_intake(
            patient,
            body.symptoms,
            body.existing_conditions,
            body.allergies,
            body.medications,
            body.notes,
            db,
        )
    return PatientResponse(
        id=patient.id,
        owner_user_id=patient.owner_user_id,
        identifier=patient.identifier,
        name=patient.name,
        age=patient.age,
        sex=patient.sex,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
        intake=IntakeResponse.model_validate(intake_record) if intake_record else None,
        report_count=0,
        reports=[],
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_one(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await authorize_patient_access(patient_id, user, db)
    intake_data = await get_intake(patient_id, db)
    from app.schemas.report import ReportResponse
    from app.services.report_service import list_patient_reports

    patient_reports = await list_patient_reports(patient_id, db)
    return PatientResponse(
        id=patient.id,
        owner_user_id=patient.owner_user_id,
        identifier=patient.identifier,
        name=patient.name,
        age=patient.age,
        sex=patient.sex,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
        intake=IntakeResponse.model_validate(intake_data) if intake_data else None,
        report_count=len(patient_reports),
        reports=[ReportResponse.model_validate(r) for r in patient_reports],
    )


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update(
    patient_id: int,
    body: PatientUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await authorize_patient_access(patient_id, user, db)
    updated = await update_patient(patient, body.model_dump(exclude_unset=True), db)
    return PatientResponse(
        id=updated.id,
        owner_user_id=updated.owner_user_id,
        identifier=updated.identifier,
        name=updated.name,
        age=updated.age,
        sex=updated.sex,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/{patient_id}", status_code=204)
async def delete(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await authorize_patient_access(patient_id, user, db)
    await delete_patient(patient, db)


@router.post("/{patient_id}/intake", response_model=IntakeResponse)
@router.put("/{patient_id}/intake", response_model=IntakeResponse)
async def save_intake(
    patient_id: int,
    body: IntakeCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    patient = await authorize_patient_access(patient_id, user, db)
    intake = await upsert_intake(
        patient, body.symptoms, body.existing_conditions,
        body.allergies, body.medications, body.notes, db,
    )
    return IntakeResponse.model_validate(intake)


@router.get("/{patient_id}/intake", response_model=IntakeResponse | None)
async def get_patient_intake(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    intake = await get_intake(patient_id, db)
    return IntakeResponse.model_validate(intake) if intake else None
