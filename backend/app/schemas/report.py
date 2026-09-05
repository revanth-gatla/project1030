"""Report, LabResult, and processing schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LabResultResponse(BaseModel):
    id: int
    report_id: int
    original_name: str
    canonical_name: str
    observed_value: str
    value_numeric: float | None = None
    unit: str | None = None
    reference_range_text: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    reference_status: str
    confidence: float | None = None
    source_text: str | None = None
    page_number: int | None = None
    verified: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class LabResultUpdate(BaseModel):
    original_name: str | None = None
    canonical_name: str | None = None
    observed_value: str | None = None
    unit: str | None = None
    reference_range_text: str | None = None
    verified: bool | None = None


class ReportResponse(BaseModel):
    id: int
    patient_id: int
    report_type: str | None = None
    original_filename: str | None = None
    mime_type: str | None = None
    report_date: datetime | None = None
    source_name: str | None = None
    processing_status: str
    extraction_version: str | None = None
    created_at: datetime
    updated_at: datetime
    lab_results: list[LabResultResponse] = []

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    id: int
    patient_id: int
    original_filename: str | None = None
    report_date: datetime | None = None
    source_name: str | None = None
    processing_status: str
    result_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class PasteReportRequest(BaseModel):
    text: str = Field(min_length=10, max_length=100000)
    report_date: str | None = None
    source_name: str | None = None


# ── AI extraction schema (for validating AI output) ─────────

class ExtractedParameter(BaseModel):
    original_name: str
    observed_value: str
    unit: str | None = None
    reference_range: str | None = None
    source_text: str | None = None
    page_number: int | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class ExtractionResult(BaseModel):
    report_date: str | None = None
    source_name: str | None = None
    parameters: list[ExtractedParameter] = []
