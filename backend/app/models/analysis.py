"""Provenance, Conflict, ClarificationQuestion, Comparison, Insight, ReviewHistory, NormalizationDictionary models."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ── Provenance ──────────────────────────────────────────────

class SourceType(str, enum.Enum):
    USER_PROVIDED = "USER_PROVIDED"
    AI_EXTRACTED = "AI_EXTRACTED"
    AI_GENERATED = "AI_GENERATED"
    HUMAN_VERIFIED = "HUMAN_VERIFIED"


class Provenance(Base):
    __tablename__ = "provenance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(
        SAEnum(SourceType, name="source_type_enum", create_constraint=True), nullable=False
    )
    source_report_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("reports.id"), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


# ── Conflicts ───────────────────────────────────────────────

class ConflictSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ConflictStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Conflict(Base):
    __tablename__ = "conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_a: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_b: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        SAEnum(ConflictSeverity, name="conflict_severity_enum", create_constraint=True),
        default=ConflictSeverity.MEDIUM,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(ConflictStatus, name="conflict_status_enum", create_constraint=True),
        default=ConflictStatus.OPEN,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("Patient", back_populates="conflicts")


# ── Clarification Questions ─────────────────────────────────

class QuestionStatus(str, enum.Enum):
    PENDING = "PENDING"
    ANSWERED = "ANSWERED"
    DISMISSED = "DISMISSED"


class ClarificationQuestion(Base):
    __tablename__ = "clarification_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum(QuestionStatus, name="question_status_enum", create_constraint=True),
        default=QuestionStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("Patient", back_populates="clarification_questions")


# ── Comparisons ─────────────────────────────────────────────

class ChangeDirection(str, enum.Enum):
    INCREASED = "INCREASED"
    DECREASED = "DECREASED"
    STABLE = "STABLE"
    NEW = "NEW"
    MISSING = "MISSING"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class Comparison(Base):
    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    previous_report_id: Mapped[int] = mapped_column(Integer, ForeignKey("reports.id"), nullable=False)
    current_report_id: Mapped[int] = mapped_column(Integer, ForeignKey("reports.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    results = relationship("ComparisonResult", back_populates="comparison", lazy="selectin", cascade="all, delete-orphan")


class ComparisonResult(Base):
    __tablename__ = "comparison_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    comparison_id: Mapped[int] = mapped_column(Integer, ForeignKey("comparisons.id"), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    previous_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    previous_reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    direction: Mapped[str] = mapped_column(
        SAEnum(ChangeDirection, name="change_direction_enum", create_constraint=True),
        default=ChangeDirection.NOT_COMPARABLE,
        nullable=False,
    )
    absolute_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage_change: Mapped[float | None] = mapped_column(Float, nullable=True)


    comparison = relationship("Comparison", back_populates="results")


# ── Insights ────────────────────────────────────────────────

class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    report_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("reports.id"), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    clarification_questions_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    patient = relationship("Patient", back_populates="insights")


# ── Review History ──────────────────────────────────────────

class ReviewHistory(Base):
    __tablename__ = "review_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


# ── Normalization Dictionary ────────────────────────────────

class NormalizationDictionary(Base):
    __tablename__ = "normalization_dictionary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alias: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
