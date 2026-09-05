"""Analysis-related schemas: conflicts, comparisons, insights, provenance, review."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, computed_field, model_validator

# ── Conflicts ───────────────────────────────────────────────

class ConflictResponse(BaseModel):
    id: int
    patient_id: int
    conflict_type: str
    description: str
    source_a: str | None = None
    source_b: str | None = None
    severity: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConflictUpdate(BaseModel):
    status: str  # ACKNOWLEDGED, RESOLVED, DISMISSED


class QuestionResponse(BaseModel):
    id: int
    patient_id: int
    question: str
    reason: str | None = None
    category: str | None = None
    answer: str | None = None
    answered: bool = False
    answered_by: int | None = None
    answered_at: datetime | None = None
    priority: int = 0
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_answered(self):
        self.answered = (self.status == "ANSWERED" or bool(self.answer))
        return self


class QuestionUpdate(BaseModel):
    status: str  # ANSWERED, DISMISSED
    answer: str | None = None


class QuestionAnswerRequest(BaseModel):
    answer: str


# ── Comparisons ─────────────────────────────────────────────

class ComparisonResultResponse(BaseModel):
    id: int
    canonical_name: str
    previous_value: str | None = None
    current_value: str | None = None
    previous_unit: str | None = None
    current_unit: str | None = None
    unit: str | None = None
    previous_reference_range: str | None = None
    current_reference_range: str | None = None
    direction: str
    change_direction: str | None = None
    absolute_change: float | None = None
    change_delta: float | None = None
    percentage_change: float | None = None
    change_percent: float | None = None
    is_significant: bool = False

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def populate_compatibility_fields(self):
        if not self.unit:
            self.unit = self.current_unit or self.previous_unit
        if not self.change_direction:
            self.change_direction = self.direction
        if self.change_delta is None:
            self.change_delta = self.absolute_change
        if self.change_percent is None:
            self.change_percent = self.percentage_change
        if not self.is_significant and self.percentage_change is not None:
            self.is_significant = abs(self.percentage_change) >= 15.0
        return self


class ComparisonResponse(BaseModel):
    id: int
    patient_id: int
    previous_report_id: int
    current_report_id: int
    created_at: datetime
    results: list[ComparisonResultResponse] = []

    model_config = {"from_attributes": True}


class ComparisonCreate(BaseModel):
    previous_report_id: int
    current_report_id: int


# ── Insights ────────────────────────────────────────────────

class InsightResponse(BaseModel):
    id: int
    patient_id: int
    report_id: int | None = None
    summary: str
    key_findings: str | None = None
    clarification_questions_text: str | None = None
    generated_at: datetime
    model_name: str | None = None
    prompt_version: str | None = None

    model_config = {"from_attributes": True}


# ── Provenance ──────────────────────────────────────────────

class ProvenanceResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    source_type: str
    source_report_id: int | None = None
    source_text: str | None = None
    page_number: int | None = None
    location_hint: str | None = None
    extraction_method: str | None = None
    confidence: float | None = None
    verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Review ──────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    patient_id: int
    entity_type: str
    entity_id: int
    action: str
    previous_value: str | None = None
    new_value: str | None = None


class ReviewResponse(BaseModel):
    id: int
    patient_id: int
    entity_type: str
    entity_id: int
    action: str
    previous_value: str | None = None
    new_value: str | None = None
    user_id: int
    created_at: datetime
    notes: str | None = None

    @computed_field
    def new_status(self) -> str | None:
        return self.new_value

    @computed_field
    def report_id(self) -> int | None:
        return self.entity_id

    @computed_field
    def reviewer_user_id(self) -> int:
        return self.user_id

    model_config = {"from_attributes": True}


# ── Dashboard / Analytics ───────────────────────────────────

class DashboardStats(BaseModel):
    total_patients: int = 0
    total_reports: int = 0
    total_lab_results: int = 0
    within_range: int = 0
    below_range: int = 0
    above_range: int = 0
    unknown_range: int = 0
    open_conflicts: int = 0
    pending_questions: int = 0
    unverified_results: int = 0
    verified_results: int = 0


class ParameterTrend(BaseModel):
    canonical_name: str
    values: list[TrendPoint] = []


class TrendPoint(BaseModel):
    date: datetime | None = None
    value: float | None = None
    unit: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    reference_status: str = "UNKNOWN"
    report_id: int


# Fix forward reference
ParameterTrend.model_rebuild()
