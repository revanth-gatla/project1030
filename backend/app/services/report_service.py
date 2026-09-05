"""Report processing service — the full pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.conflict_detector import detect_duplicate_parameters
from app.analysis.reference_engine import (
    calculate_reference_status,
    parse_numeric_value,
    parse_reference_range,
)
from app.core.errors import (
    DatabasePersistenceFailedError,
    EmptyPdfTextError,
    ExtractionError,
    NoLabParametersFoundError,
    PdfTextExtractionFailedError,
    ProcessingError,
    StructuredExtractionFailedError,
    UploadFailedError,
)
from app.extraction.ai_provider import (
    EXTRACTION_PROMPT_VERSION,
    SUMMARY_PROMPT_VERSION,
    extract_report_date,
    extract_source_name,
    get_ai_provider,
)
from app.extraction.document_processor import (
    clean_text,
    compute_content_hash,
    extract_text,
    sanitize_filename,
    validate_file,
)
from app.models.analysis import (
    ClarificationQuestion,
    Conflict,
    ConflictStatus,
    Insight,
    Provenance,
    SourceType,
)
from app.models.report import LabResult, ProcessingStatus, Report
from app.normalization.normalizer import is_disallowed_parameter_name, normalize_parameter_name
from app.schemas.report import ExtractionResult

logger = structlog.get_logger()


async def create_report_from_file(
    patient_id: int,
    filename: str,
    content: bytes,
    mime_type: str | None,
    max_size_bytes: int,
    db: AsyncSession,
    report_date: str | None = None,
    source_name: str | None = None,
) -> Report:
    """Validate and store uploaded file as a report."""
    safe_name = sanitize_filename(filename)
    is_valid, error = validate_file(safe_name, content, mime_type, max_size_bytes)
    if not is_valid:
        raise UploadFailedError(error or "Invalid file.")

    # Extract text
    try:
        raw_text = extract_text(safe_name, content)
    except (EmptyPdfTextError, PdfTextExtractionFailedError):
        raise
    except ValueError as e:
        raise ExtractionError(str(e))

    if not raw_text.strip():
        raise EmptyPdfTextError("PDF text extraction returned no text.")

    cleaned = clean_text(raw_text)
    content_hash = compute_content_hash(cleaned)

    # Temporary backend diagnostics (safe, non-sensitive)
    logger.info(
        "report_upload_diagnostics",
        filename=safe_name,
        content_type=mime_type,
        file_size=len(content),
        extracted_text_length=len(cleaned),
    )

    # Date precedence: 1. document date, 2. user-entered date, 3. None (fallback on process)
    doc_date = extract_report_date(cleaned)
    parsed_date = None
    if doc_date:
        try:
            parsed_date = datetime.fromisoformat(doc_date).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass
    elif report_date:
        try:
            parsed_date = datetime.fromisoformat(report_date).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass

    doc_source = extract_source_name(cleaned)
    final_source = doc_source or source_name

    # Check idempotency — same content already processed for this patient
    existing = await db.execute(
        select(Report).where(
            Report.patient_id == patient_id,
            Report.content_hash == content_hash,
            Report.processing_status.in_([
                ProcessingStatus.EXTRACTED,
                ProcessingStatus.VALIDATED,
            ]),
        )
    )
    existing_report = existing.scalar_one_or_none()
    if existing_report:
        if parsed_date and not existing_report.report_date:
            existing_report.report_date = parsed_date
            await db.flush()
        return existing_report

    report = Report(
        patient_id=patient_id,
        original_filename=safe_name,
        mime_type=mime_type,
        raw_text=cleaned,
        content_hash=content_hash,
        report_date=parsed_date,
        source_name=final_source,
        processing_status=ProcessingStatus.UPLOADED,
    )
    db.add(report)
    try:
        await db.flush()
    except Exception as exc:
        raise DatabasePersistenceFailedError(f"Failed to persist report: {exc}")
    return await get_report_with_results(report.id, db) or report


async def create_report_from_text(
    patient_id: int,
    text: str,
    report_date: str | None,
    source_name: str | None,
    db: AsyncSession,
) -> Report:
    """Create a report from pasted text."""
    cleaned = clean_text(text)
    content_hash = compute_content_hash(cleaned)

    # Idempotency check
    from sqlalchemy.orm import selectinload
    existing = await db.execute(
        select(Report).options(selectinload(Report.lab_results)).where(
            Report.patient_id == patient_id,
            Report.content_hash == content_hash,
            Report.processing_status.in_([
                ProcessingStatus.EXTRACTED,
                ProcessingStatus.VALIDATED,
            ]),
        )
    )
    existing_rep = existing.scalar_one_or_none()
    if existing_rep:
        return existing_rep

    parsed_date = None
    if report_date:
        try:
            parsed_date = datetime.fromisoformat(report_date).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass

    report = Report(
        patient_id=patient_id,
        report_type="TEXT",
        raw_text=cleaned,
        content_hash=content_hash,
        report_date=parsed_date,
        source_name=source_name,
        processing_status=ProcessingStatus.UPLOADED,
    )
    db.add(report)
    await db.flush()
    return await get_report_with_results(report.id, db) or report


async def process_report(report: Report, db: AsyncSession) -> Report:
    """Full processing pipeline: extract → validate → normalize → analyze."""
    if not report.raw_text:
        report.processing_status = ProcessingStatus.FAILED
        await db.flush()
        raise ProcessingError("Report has no text content to process.")

    report.processing_status = ProcessingStatus.PROCESSING
    await db.flush()

    # ── AI / Rule Extraction ───────────────────────────────────────
    try:
        provider = get_ai_provider()
        extraction: ExtractionResult = await provider.extract_report(report.raw_text)
    except (
        NoLabParametersFoundError,
        StructuredExtractionFailedError,
        EmptyPdfTextError,
        PdfTextExtractionFailedError,
    ):
        report.processing_status = ProcessingStatus.FAILED
        await db.flush()
        raise
    except Exception as e:
        logger.error("ai_extraction_failed", report_id=report.id, error=str(e))
        report.processing_status = ProcessingStatus.FAILED
        await db.flush()
        raise StructuredExtractionFailedError(f"Extraction failed: {e}")

    # Date precedence:
    # 1. Explicit report date extracted from document
    # 2. User-entered report date if intentionally provided/overridden
    # 3. Current date only as a last fallback when no report date exists
    if extraction.report_date:
        try:
            report.report_date = datetime.fromisoformat(extraction.report_date).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            pass
    elif not report.report_date:
        report.report_date = datetime.now(timezone.utc)

    if extraction.source_name and (not report.source_name or report.source_name == "Clinical Diagnostics"):
        report.source_name = extraction.source_name

    report.extraction_version = EXTRACTION_PROMPT_VERSION
    report.processing_status = ProcessingStatus.EXTRACTED

    # ── Clean up any previous results/provenance for idempotent reprocessing ──
    existing_lrs = await db.execute(select(LabResult.id).where(LabResult.report_id == report.id))
    lr_ids = list(existing_lrs.scalars().all())
    if lr_ids:
        await db.execute(
            delete(Provenance).where(
                Provenance.entity_type == "lab_result",
                Provenance.entity_id.in_(lr_ids),
            )
        )
        await db.execute(delete(LabResult).where(LabResult.report_id == report.id))
        await db.flush()

    # ── Validate, Normalize, Analyze each parameter ─────────
    lab_results_data = []
    created_lrs: list[LabResult] = []

    for param in extraction.parameters:
        if is_disallowed_parameter_name(param.original_name):
            # If this disallowed label contains range data and previous test has no reference range, rescue it
            norm_name = param.original_name.strip().lower()
            is_ref = any(term in norm_name for term in ("reference", "normal range", "expected range", "interval", "ref range"))
            if is_ref and created_lrs and not created_lrs[-1].reference_range_text:
                recovered_ref = param.reference_range or param.observed_value or ""
                if param.unit and not recovered_ref.endswith(param.unit):
                    recovered_ref = f"{recovered_ref} {param.unit}".strip()
                created_lrs[-1].reference_range_text = recovered_ref
                low, high = parse_reference_range(recovered_ref)
                created_lrs[-1].reference_low = low
                created_lrs[-1].reference_high = high
                created_lrs[-1].reference_status = calculate_reference_status(created_lrs[-1].value_numeric, low, high)
            continue

        canonical = normalize_parameter_name(param.original_name)
        if is_disallowed_parameter_name(canonical):
            continue

        value_numeric = parse_numeric_value(param.observed_value)
        ref_low, ref_high = parse_reference_range(param.reference_range)
        ref_status = calculate_reference_status(value_numeric, ref_low, ref_high)

        # Ensure genuine confidence or None (never fabricated universal defaults)
        conf_val = None
        if param.confidence is not None:
            try:
                conf_float = float(param.confidence)
                if 0.0 <= conf_float <= 1.0:
                    conf_val = conf_float
            except (ValueError, TypeError):
                conf_val = None

        lr = LabResult(
            report_id=report.id,
            original_name=param.original_name,
            canonical_name=canonical,
            observed_value=param.observed_value,
            value_numeric=value_numeric,
            unit=param.unit,
            reference_range_text=param.reference_range,
            reference_low=ref_low,
            reference_high=ref_high,
            reference_status=ref_status,
            confidence=conf_val,
            source_text=param.source_text,
            page_number=param.page_number,
        )
        db.add(lr)
        created_lrs.append(lr)

        # Create provenance record
        await db.flush()
        prov = Provenance(
            entity_type="lab_result",
            entity_id=lr.id,
            source_type=SourceType.AI_EXTRACTED if conf_val is not None else SourceType.USER_PROVIDED,
            source_report_id=report.id,
            source_text=param.source_text,
            page_number=param.page_number,
            extraction_method="ai_structured_extraction" if conf_val is not None else "deterministic_rule_extraction",
            confidence=conf_val,
        )
        db.add(prov)

        lab_results_data.append({
            "original_name": param.original_name,
            "canonical_name": canonical,
            "observed_value": param.observed_value,
        })


    # ── Duplicate parameter detection with conflict deduplication ──
    dup_conflicts = detect_duplicate_parameters(lab_results_data)
    for dc in dup_conflicts:
        # Prevent creating identical open conflict records
        existing_conflict = await db.execute(
            select(Conflict).where(
                Conflict.patient_id == report.patient_id,
                Conflict.conflict_type == dc["conflict_type"],
                Conflict.description == dc["description"],
                Conflict.status == ConflictStatus.OPEN,
            )
        )
        if existing_conflict.scalar_one_or_none():
            continue

        conflict = Conflict(
            patient_id=report.patient_id,
            conflict_type=dc["conflict_type"],
            description=dc["description"],
            source_a=dc["source_a"],
            source_b=dc["source_b"],
            severity=dc["severity"],
            status=ConflictStatus.OPEN,
        )
        db.add(conflict)

    try:
        report.processing_status = ProcessingStatus.VALIDATED
        await db.flush()
    except Exception as exc:
        logger.error("database_persistence_failed", report_id=report.id, error=str(exc))
        raise DatabasePersistenceFailedError(f"Failed to persist report and lab results to database: {exc}")

    return report


async def generate_report_insights(
    report: Report,
    patient_data: dict,
    db: AsyncSession,
) -> Insight:
    """Generate AI insights from structured data — called AFTER deterministic processing."""
    from app.core.config import get_settings

    settings = get_settings()
    provider = get_ai_provider()

    try:
        result = await provider.generate_insights(patient_data)
    except Exception as e:
        logger.error("ai_insights_failed", report_id=report.id, error=str(e))
        raise ExtractionError(f"Failed to generate insights: {e}")

    # Format clarification questions text cleanly
    raw_qs = result.get("clarification_questions", [])
    q_bullet_list = []
    for item in raw_qs:
        if isinstance(item, dict):
            q_bullet_list.append(f"• {item.get('question', '').strip()}")
        elif isinstance(item, str) and item.strip():
            q_bullet_list.append(f"• {item.strip()}")
    formatted_qs_text = "\n".join(q_bullet_list)

    insight = Insight(
        patient_id=report.patient_id,
        report_id=report.id,
        summary=result.get("summary", ""),
        key_findings=result.get("key_findings", ""),
        clarification_questions_text=formatted_qs_text,
        model_name=settings.ai_model,
        prompt_version=SUMMARY_PROMPT_VERSION,
    )
    db.add(insight)

    # Fetch existing questions for this patient to prevent duplicates
    existing_res = await db.execute(
        select(ClarificationQuestion).where(ClarificationQuestion.patient_id == report.patient_id)
    )
    existing_map = {
        q.question.strip().lower(): q
        for q in existing_res.scalars().all()
        if q.question
    }

    # Create / update clarification questions
    for item in raw_qs:
        if isinstance(item, dict):
            q_text = item.get("question", "").strip()
            q_reason = item.get("reason", "").strip() or "Identified from out-of-range clinical biomarker evaluation."
            q_cat = item.get("category", "").strip() or "Clinical Decision Support"
            q_pri = int(item.get("priority", 1))
        elif isinstance(item, str) and item.strip():
            q_text = item.strip()
            q_reason = "Identified from out-of-range clinical biomarker evaluation."
            q_cat = "Clinical Decision Support"
            q_pri = 1
        else:
            continue

        if not q_text:
            continue

        norm_key = q_text.lower()
        if norm_key in existing_map:
            existing_q = existing_map[norm_key]
            # If existing question has a generic or empty reason, upgrade it to the specific clinical rationale
            if not existing_q.reason or existing_q.reason == "Generated from AI analysis of structured report data.":
                existing_q.reason = q_reason
            if not getattr(existing_q, "category", None) or existing_q.category == "Clinical Decision Support":
                existing_q.category = q_cat
        else:
            cq = ClarificationQuestion(
                patient_id=report.patient_id,
                question=q_text,
                reason=q_reason,
                category=q_cat,
                priority=q_pri,
            )
            db.add(cq)
            existing_map[norm_key] = cq

    await db.flush()
    return insight


async def get_report_with_results(report_id: int, db: AsyncSession) -> Report | None:
    """Get report with lab results loaded."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Report).options(selectinload(Report.lab_results)).where(Report.id == report_id)
    )
    return result.scalar_one_or_none()


async def list_patient_reports(patient_id: int, db: AsyncSession) -> list[Report]:
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.lab_results))
        .where(Report.patient_id == patient_id)
        .order_by(Report.report_date.desc().nullslast(), Report.created_at.desc())
    )
    return list(result.scalars().all())


async def cleanup_corrupted_lab_results(db: AsyncSession) -> int:
    """Scan and delete corrupted lab results where metadata labels became parameter names."""
    from app.normalization.normalizer import is_disallowed_parameter_name

    lrs_res = await db.execute(select(LabResult))
    all_lrs = lrs_res.scalars().all()
    corrupted_ids = [
        lr.id
        for lr in all_lrs
        if is_disallowed_parameter_name(lr.original_name)
        or is_disallowed_parameter_name(lr.canonical_name)
    ]
    if corrupted_ids:
        await db.execute(
            delete(Provenance).where(
                Provenance.entity_type == "lab_result",
                Provenance.entity_id.in_(corrupted_ids),
            )
        )
        await db.execute(delete(LabResult).where(LabResult.id.in_(corrupted_ids)))
        await db.flush()
        logger.info("cleaned_corrupted_lab_results", count=len(corrupted_ids))
    return len(corrupted_ids)

