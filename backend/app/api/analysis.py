"""Analysis API routes — conflicts, comparisons, questions, insights, provenance, review, analytics."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import authorize_patient_access, get_current_user
from app.core.errors import NotFoundError
from app.models.analysis import (
    ClarificationQuestion,
    Conflict,
    Insight,
    Provenance,
    QuestionStatus,
    ReviewHistory,
)
from app.models.user import User
from app.schemas.analysis import (
    ComparisonCreate,
    ComparisonResponse,
    ConflictResponse,
    ConflictUpdate,
    DashboardStats,
    InsightResponse,
    ProvenanceResponse,
    QuestionAnswerRequest,
    QuestionResponse,
    QuestionUpdate,
    ReviewCreate,
    ReviewResponse,
)
from app.services.analysis_service import (
    create_comparison,
    get_comparison,
    get_dashboard_stats,
    get_parameter_trends,
)

router = APIRouter(tags=["analysis"])


# ── Dashboard ───────────────────────────────────────────────

@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_dashboard_stats(user.id, db)
    return DashboardStats(**stats)


# ── Conflicts ───────────────────────────────────────────────

@router.get("/patients/{patient_id}/conflicts", response_model=list[ConflictResponse])
async def get_conflicts(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    result = await db.execute(
        select(Conflict).where(Conflict.patient_id == patient_id)
        .order_by(Conflict.created_at.desc())
    )
    conflicts = result.scalars().all()
    seen = set()
    deduped = []
    for c in conflicts:
        key = (c.conflict_type, c.description, c.status)
        if key not in seen:
            seen.add(key)
            deduped.append(c)
    return [ConflictResponse.model_validate(c) for c in deduped]


@router.patch("/conflicts/{conflict_id}", response_model=ConflictResponse)
async def update_conflict(
    conflict_id: int,
    body: ConflictUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Conflict).where(Conflict.id == conflict_id))
    conflict = result.scalar_one_or_none()
    if not conflict:
        raise NotFoundError("Conflict not found.")
    await authorize_patient_access(conflict.patient_id, user, db)
    conflict.status = body.status
    await db.flush()
    return ConflictResponse.model_validate(conflict)


@router.post("/conflicts/{conflict_id}/resolve", response_model=ConflictResponse)
async def resolve_conflict_action(
    conflict_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Conflict).where(Conflict.id == conflict_id))
    conflict = result.scalar_one_or_none()
    if not conflict:
        raise NotFoundError("Conflict not found.")
    await authorize_patient_access(conflict.patient_id, user, db)
    conflict.status = "RESOLVED"
    await db.flush()
    return ConflictResponse.model_validate(conflict)


# ── Clarification Questions ─────────────────────────────────

@router.get("/patients/{patient_id}/questions", response_model=list[QuestionResponse])
@router.get("/patients/{patient_id}/clarification-questions", response_model=list[QuestionResponse])
async def get_questions(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    result = await db.execute(
        select(ClarificationQuestion)
        .where(ClarificationQuestion.patient_id == patient_id)
        .order_by(ClarificationQuestion.priority.desc(), ClarificationQuestion.id.asc())
    )
    all_qs = result.scalars().all()
    # Deduplicate questions by normalized question text
    seen_texts = set()
    deduped = []
    for q in all_qs:
        norm = (q.question or "").strip().lower()
        if norm and norm not in seen_texts:
            seen_texts.add(norm)
            deduped.append(q)
    return [QuestionResponse.model_validate(q) for q in deduped]


@router.patch("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    body: QuestionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClarificationQuestion).where(ClarificationQuestion.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise NotFoundError("Question not found.")
    await authorize_patient_access(q.patient_id, user, db)
    q.status = body.status
    if body.answer is not None:
        q.answer = body.answer.strip()
        q.answered_by = user.id
        q.answered_at = datetime.now(timezone.utc)
    await db.flush()
    return QuestionResponse.model_validate(q)


@router.post("/clarification-questions/{question_id}/answer", response_model=QuestionResponse)
async def answer_question_action(
    question_id: int,
    body: QuestionAnswerRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ClarificationQuestion).where(ClarificationQuestion.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise NotFoundError("Question not found.")
    await authorize_patient_access(q.patient_id, user, db)

    answer_val = body.answer.strip() if (body and body.answer and body.answer.strip()) else "Confirmed and reviewed by clinician."
    q.answer = answer_val
    q.status = QuestionStatus.ANSWERED
    q.answered_by = user.id
    q.answered_at = datetime.now(timezone.utc)

    rev = ReviewHistory(
        patient_id=q.patient_id,
        user_id=user.id,
        action="ANSWERED_QUESTION",
        entity_type="clarification_question",
        entity_id=q.id,
        new_value=answer_val,
    )
    db.add(rev)
    await db.flush()
    return QuestionResponse.model_validate(q)


# ── Comparisons ─────────────────────────────────────────────

@router.get("/patients/{patient_id}/comparisons", response_model=ComparisonResponse | None)
async def get_patient_comparisons(
    patient_id: int,
    previous_report_id: int | None = None,
    current_report_id: int | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    from app.models.analysis import Comparison
    query = select(Comparison).where(Comparison.patient_id == patient_id)
    if previous_report_id and current_report_id:
        query = query.where(
            Comparison.previous_report_id == previous_report_id,
            Comparison.current_report_id == current_report_id,
        )
    query = query.order_by(Comparison.created_at.desc())
    result = await db.execute(query)
    comp = result.scalars().first()
    if not comp and previous_report_id and current_report_id:
        comp = await create_comparison(patient_id, previous_report_id, current_report_id, db)
    if comp:
        full = await get_comparison(comp.id, db)
        return ComparisonResponse.model_validate(full)
    return None


@router.post("/patients/{patient_id}/comparisons", response_model=ComparisonResponse, status_code=201)
async def compare_reports(
    patient_id: int,
    body: ComparisonCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    comparison = await create_comparison(
        patient_id, body.previous_report_id, body.current_report_id, db
    )
    full = await get_comparison(comparison.id, db)
    return ComparisonResponse.model_validate(full)


@router.get("/comparisons/{comparison_id}", response_model=ComparisonResponse)
async def get_comp(
    comparison_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comp = await get_comparison(comparison_id, db)
    if not comp:
        raise NotFoundError("Comparison not found.")
    await authorize_patient_access(comp.patient_id, user, db)
    return ComparisonResponse.model_validate(comp)


# ── Insights ────────────────────────────────────────────────

@router.get("/patients/{patient_id}/insights", response_model=list[InsightResponse])
async def get_insights(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    result = await db.execute(
        select(Insight).where(Insight.patient_id == patient_id)
        .order_by(Insight.generated_at.desc())
    )
    return [InsightResponse.model_validate(i) for i in result.scalars().all()]


# ── Provenance ──────────────────────────────────────────────

@router.get("/provenance/{entity_type}/{entity_id}", response_model=list[ProvenanceResponse])
async def get_provenance(
    entity_type: str,
    entity_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Provenance).where(
            Provenance.entity_type == entity_type,
            Provenance.entity_id == entity_id,
        ).order_by(Provenance.created_at.desc())
    )
    return [ProvenanceResponse.model_validate(p) for p in result.scalars().all()]


# ── Review History ──────────────────────────────────────────

@router.post("/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(
    body: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(body.patient_id, user, db)
    review = ReviewHistory(
        patient_id=body.patient_id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        action=body.action,
        previous_value=body.previous_value,
        new_value=body.new_value,
        user_id=user.id,
    )
    db.add(review)
    await db.flush()
    return ReviewResponse.model_validate(review)


@router.get("/patients/{patient_id}/review-history", response_model=list[ReviewResponse])
async def get_review_history(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    result = await db.execute(
        select(ReviewHistory).where(ReviewHistory.patient_id == patient_id)
        .order_by(ReviewHistory.created_at.desc())
    )
    return [ReviewResponse.model_validate(r) for r in result.scalars().all()]


# ── Parameter Trends (Analytics) ────────────────────────────

@router.get("/patients/{patient_id}/trends")
async def trends(
    patient_id: int,
    parameter: str = Query(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await authorize_patient_access(patient_id, user, db)
    data = await get_parameter_trends(patient_id, parameter, db)
    return data


# ── Demo Mode Seed ──────────────────────────────────────────

@router.post("/demo/seed")
async def seed_demo():
    """Seed synthetic clinical demonstration dataset for competition review."""
    from app.seed import seed_data
    await seed_data()
    return {
        "status": "success",
        "message": "Demo data ready",
        "email": "doctor@medlens.health",
        "password": "DemoPassword123!",
    }
