"""Patient & intake schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    identifier: str | None = None
    age: int | None = Field(default=None, ge=0, le=200)
    sex: str = "UNKNOWN"
    symptoms: str | None = None
    existing_conditions: str | None = None
    allergies: str | None = None
    medications: str | None = None
    notes: str | None = None


class PatientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    identifier: str | None = None
    age: int | None = Field(default=None, ge=0, le=200)
    sex: str | None = None


class IntakeCreate(BaseModel):
    symptoms: str | None = None
    existing_conditions: str | None = None
    allergies: str | None = None
    medications: str | None = None
    notes: str | None = None


class IntakeResponse(BaseModel):
    id: int
    patient_id: int
    symptoms: str | None = None
    existing_conditions: str | None = None
    allergies: str | None = None
    medications: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


from app.schemas.report import ReportResponse


class PatientResponse(BaseModel):
    id: int
    owner_user_id: int
    identifier: str | None = None
    name: str
    age: int | None = None
    sex: str
    created_at: datetime
    updated_at: datetime
    intake: IntakeResponse | None = None
    report_count: int = 0
    reports: list[ReportResponse] = []

    model_config = {"from_attributes": True}


class PatientListResponse(BaseModel):
    id: int
    name: str
    identifier: str | None = None
    age: int | None = None
    sex: str
    created_at: datetime
    intake: IntakeResponse | None = None
    report_count: int = 0
    open_conflicts: int = 0
    pending_reviews: int = 0

    model_config = {"from_attributes": True}
