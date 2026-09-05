"""PDF Generation endpoint for clinical reports using ReportLab."""

from __future__ import annotations

import io
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import authorize_patient_access, get_current_user
from app.models.analysis import ClarificationQuestion, Conflict, Insight, ReviewHistory
from app.models.patient import PatientIntake
from app.models.report import LabResult, Report
from app.models.user import User

router = APIRouter(prefix="/patients", tags=["pdf"])


@router.get("/{patient_id}/report/pdf")
async def generate_patient_pdf_report(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a comprehensive, publication-grade clinical intelligence PDF dossier."""
    patient = await authorize_patient_access(patient_id, user, db)

    # 1. Fetch intake
    intake_res = await db.execute(
        select(PatientIntake).where(PatientIntake.patient_id == patient_id)
    )
    intake = intake_res.scalar_one_or_none()

    # 2. Fetch reports with lab results
    reports_res = await db.execute(
        select(Report)
        .options(selectinload(Report.lab_results))
        .where(Report.patient_id == patient_id)
        .order_by(Report.report_date.desc().nullslast(), Report.created_at.desc())
    )
    reports = reports_res.scalars().all()

    # 3. Fetch conflicts
    conflicts_res = await db.execute(
        select(Conflict)
        .where(Conflict.patient_id == patient_id)
        .order_by(Conflict.created_at.desc())
    )
    conflicts = conflicts_res.scalars().all()

    # 4. Fetch clarification questions
    questions_res = await db.execute(
        select(ClarificationQuestion)
        .where(ClarificationQuestion.patient_id == patient_id)
        .order_by(ClarificationQuestion.created_at.desc())
    )
    questions = questions_res.scalars().all()

    # 5. Fetch latest insight across reports
    insights_res = await db.execute(
        select(Insight)
        .where(Insight.patient_id == patient_id)
        .order_by(Insight.generated_at.desc())
    )
    insights = list(insights_res.scalars().all())

    # 6. Fetch review history
    reviews_res = await db.execute(
        select(ReviewHistory)
        .where(ReviewHistory.patient_id == patient_id)
        .order_by(ReviewHistory.created_at.desc())
    )
    reviews = reviews_res.scalars().all()

    # Build PDF buffer
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0284c7")
    dark_slate = colors.HexColor("#0f172a")
    text_muted = colors.HexColor("#475569")
    light_bg = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#cbd5e1")
    danger_color = colors.HexColor("#dc2626")
    success_color = colors.HexColor("#16a34a")
    warning_color = colors.HexColor("#d97706")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=text_muted,
    )
    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=dark_slate,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_slate,
    )
    body_bold = ParagraphStyle(
        "Body_Bold_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=dark_slate,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=text_muted,
    )

    story = []

    # --- Header ---
    header_data = [
        [
            Paragraph("<b>MedLens Clinical Intelligence</b>", title_style),
            Paragraph(f"<b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}<br/><b>Status:</b> Official Clinical Record", subtitle_style),
        ]
    ]
    t_header = Table(header_data, colWidths=[3.5 * inch, 3.9 * inch])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=12))

    # --- Patient Summary Box ---
    p_name = patient.name or "N/A"
    p_mrn = patient.identifier or f"PAT-{patient.id:05d}"
    p_age = f"{patient.age} yrs" if patient.age else "Unspecified"
    p_sex = patient.sex or "Unspecified"

    demographics_table_data = [
        [
            Paragraph("<b>Patient Name:</b>", body_bold),
            Paragraph(p_name, body_style),
            Paragraph("<b>Patient ID / Identifier:</b>", body_bold),
            Paragraph(p_mrn, body_style),
        ],
        [
            Paragraph("<b>Age / Sex:</b>", body_bold),
            Paragraph(f"{p_age} / {p_sex}", body_style),
            Paragraph("<b>Managing Clinician:</b>", body_bold),
            Paragraph(getattr(user, "full_name", None) or user.email, body_style),
        ]
    ]
    t_demographics = Table(demographics_table_data, colWidths=[1.4 * inch, 2.3 * inch, 1.8 * inch, 1.9 * inch])
    t_demographics.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("BOX", (0, 0), (-1, -1), 1, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_demographics)
    story.append(Spacer(1, 14))

    # --- Clinical Intake Context ---
    story.append(Paragraph("1. Clinical Intake & Context", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))

    if intake:
        intake_rows = [
            [Paragraph("<b>Chief Symptoms:</b>", body_bold), Paragraph(intake.symptoms or "None noted", body_style)],
            [Paragraph("<b>Existing Diagnoses:</b>", body_bold), Paragraph(intake.existing_conditions or "None recorded", body_style)],
            [Paragraph("<b>Documented Allergies:</b>", body_bold), Paragraph(f"<font color='{danger_color.hexval()}'><b>{intake.allergies}</b></font>" if intake.allergies else "No known drug allergies (NKDA)", body_style)],
            [Paragraph("<b>Current Medications:</b>", body_bold), Paragraph(intake.medications or "None documented", body_style)],
        ]
        if intake.notes:
            intake_rows.append([Paragraph("<b>Clinical Notes:</b>", body_bold), Paragraph(intake.notes, body_style)])

        t_intake = Table(intake_rows, colWidths=[1.8 * inch, 5.6 * inch])
        t_intake.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t_intake)
    else:
        story.append(Paragraph("<i>No clinical intake context recorded for this patient.</i>", body_style))
    story.append(Spacer(1, 14))

    # --- Diagnostic Reports on Record ---
    story.append(Paragraph(f"2. Diagnostic Reports on Record ({len(reports)})", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))

    if reports:
        report_table_data = [
            [
                Paragraph("<b>Report Date</b>", body_bold),
                Paragraph("<b>Document Title / Type</b>", body_bold),
                Paragraph("<b>Source Facility</b>", body_bold),
                Paragraph("<b>Tests</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
            ]
        ]
        for r in reports:
            r_date = r.report_date.strftime("%Y-%m-%d") if r.report_date else "N/A"
            r_title = r.original_filename or f"Report #{r.id}"
            r_tests = str(len(r.lab_results)) if r.lab_results else "0"
            report_table_data.append([
                Paragraph(r_date, body_style),
                Paragraph(f"{r_title} ({r.report_type or 'General'})", body_style),
                Paragraph(r.source_name or "Standard Lab", body_style),
                Paragraph(r_tests, body_style),
                Paragraph(f"<b>{r.processing_status}</b>", body_style),
            ])
        t_reports = Table(report_table_data, colWidths=[1.1 * inch, 2.7 * inch, 1.8 * inch, 0.7 * inch, 1.1 * inch])
        t_reports.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), light_bg),
            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t_reports)
    else:
        story.append(Paragraph("<i>No diagnostic reports ingested yet.</i>", body_style))
    story.append(Spacer(1, 14))

    # --- Structured Lab Results Table ---
    all_labs: list[LabResult] = []
    for r in reports:
        if r.lab_results:
            all_labs.extend(r.lab_results)

    story.append(Paragraph(f"3. Extracted & Normalized Lab Results ({len(all_labs)})", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))

    if all_labs:
        labs_table_data = [
            [
                Paragraph("<b>Biomarker / Test</b>", body_bold),
                Paragraph("<b>Result Value</b>", body_bold),
                Paragraph("<b>Units</b>", body_bold),
                Paragraph("<b>Reference Interval</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
                Paragraph("<b>Verified</b>", body_bold),
            ]
        ]
        for lab in all_labs:
            status_text = lab.reference_status or "UNKNOWN"
            if status_text == "WITHIN":
                status_formatted = f"<font color='{success_color.hexval()}'><b>NORMAL</b></font>"
            elif status_text in ("ABOVE", "HIGH", "CRITICAL_HIGH"):
                status_formatted = f"<font color='{danger_color.hexval()}'><b>HIGH</b></font>"
            elif status_text in ("BELOW", "LOW", "CRITICAL_LOW"):
                status_formatted = f"<font color='{danger_color.hexval()}'><b>LOW</b></font>"
            else:
                status_formatted = f"<font color='{text_muted.hexval()}'>{status_text}</font>"

            ref_range = "—"
            if lab.reference_low is not None and lab.reference_high is not None:
                ref_range = f"{lab.reference_low} - {lab.reference_high}"
            elif lab.reference_range_text:
                ref_range = lab.reference_range_text

            val_display = str(lab.value_numeric) if lab.value_numeric is not None else (lab.observed_value or "—")
            is_verified = "Yes" if lab.verified else "Pending"

            labs_table_data.append([
                Paragraph(f"<b>{lab.canonical_name}</b><br/><font size=7.5 color='{text_muted.hexval()}'>{lab.original_name or ''}</font>", body_style),
                Paragraph(val_display, body_style),
                Paragraph(lab.unit or "—", body_style),
                Paragraph(ref_range, body_style),
                Paragraph(status_formatted, body_style),
                Paragraph(is_verified, body_style),
            ])

        t_labs = Table(labs_table_data, colWidths=[2.2 * inch, 1.1 * inch, 1.0 * inch, 1.4 * inch, 1.0 * inch, 0.7 * inch])
        t_labs.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), light_bg),
            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t_labs)
    else:
        story.append(Paragraph("<i>No structured lab results available.</i>", body_style))
    story.append(Spacer(1, 14))

    # --- Safety Conflicts ---
    from app.models.analysis import ConflictStatus
    open_conflicts = [
        c for c in conflicts
        if (getattr(c, "status", None) != ConflictStatus.RESOLVED and str(getattr(c, "status", "")).upper() != "RESOLVED")
    ]
    story.append(Paragraph(f"4. Clinical Safety & Reconciliation Alerts ({len(open_conflicts)} Active)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))

    if conflicts:
        for idx, conf in enumerate(conflicts, 1):
            sev_color = danger_color if conf.severity in ("CRITICAL", "HIGH") else warning_color
            is_resolved = (getattr(conf, "status", None) == ConflictStatus.RESOLVED or str(getattr(conf, "status", "")).upper() == "RESOLVED")
            status_lbl = "RESOLVED" if is_resolved else "OPEN / REQUIRES ACTION"
            story.append(Paragraph(
                f"<b>Alert {idx} [{conf.severity}] — {conf.conflict_type} ({status_lbl})</b>",
                ParagraphStyle("AlertH", parent=body_bold, textColor=sev_color)
            ))
            story.append(Paragraph(conf.description or "No description provided.", body_style))
            res_notes = getattr(conf, "resolution_notes", None)
            if res_notes:
                story.append(Paragraph(f"<b>Resolution:</b> {res_notes}", ParagraphStyle("Res", parent=body_style, textColor=success_color)))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("<i>No clinical safety conflicts detected. All findings reconciled.</i>", body_style))
    story.append(Spacer(1, 10))

    # --- AI Insights ---
    if insights:
        story.append(Paragraph("5. AI-Assisted Clinical Summary & Observations", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))
        for ins in insights:
            if ins.summary:
                story.append(Paragraph(f"<b>Synthesis:</b> {ins.summary}", body_style))
                story.append(Spacer(1, 4))
            if ins.key_findings:
                clean_kf = ins.key_findings.replace("\n", "<br/>")
                story.append(Paragraph(f"<b>Key Findings:</b><br/>{clean_kf}", body_style))
                story.append(Spacer(1, 4))
            if ins.clarification_questions_text:
                q_text = ins.clarification_questions_text.strip()
                if q_text.startswith("[") and q_text.endswith("]"):
                    import ast
                    try:
                        parsed_list = ast.literal_eval(q_text)
                        if isinstance(parsed_list, list):
                            clean_items = []
                            for it in parsed_list:
                                if isinstance(it, dict):
                                    clean_items.append(it.get("question", ""))
                                elif isinstance(it, str):
                                    clean_items.append(it)
                            q_text = "<br/>".join([f"• <i>{it}</i>" for it in clean_items if it])
                    except Exception:
                        pass
                else:
                    q_text = q_text.replace("\n", "<br/>")
                if q_text:
                    story.append(Paragraph(f"<b>Suggested Considerations:</b><br/>{q_text}", body_style))
                    story.append(Spacer(1, 4))
        story.append(Spacer(1, 10))

    # --- Clarification Questions ---
    deduped_questions = []
    seen_q_texts = set()
    for q in (questions or []):
        norm_t = (q.question or "").strip().lower()
        if norm_t and norm_t not in seen_q_texts:
            seen_q_texts.add(norm_t)
            deduped_questions.append(q)

    if deduped_questions:
        pending_count = sum(1 for q in deduped_questions if str(getattr(q.status, "value", q.status)).upper() != "ANSWERED" and not getattr(q, "answer", None))
        ans_count = len(deduped_questions) - pending_count
        hdr_lbl = f"6. Clinical Clarification Inquiries ({len(deduped_questions)} Total — {ans_count} Attested, {pending_count} Pending)"
        story.append(Paragraph(hdr_lbl, h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))
        for q in deduped_questions:
            is_ans = (str(getattr(q.status, "value", q.status)).upper() == "ANSWERED" or bool(getattr(q, "answer", None)))
            status_badge = "ATTESTED / ANSWERED" if is_ans else "PENDING CLINICIAN REVIEW"
            status_col = "#047857" if is_ans else "#2563eb"
            cat_str = f" <i>[{q.category}]</i>" if getattr(q, "category", None) else ""

            story.append(Paragraph(
                f"• <b>Inquiry:</b> {q.question} <font color='{status_col}'><b>[{status_badge}]</b></font>{cat_str}",
                body_style
            ))
            if q.reason and q.reason.strip() and q.reason.strip() != "Generated from AI analysis of structured report data.":
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Clinical Rationale:</b> {q.reason}", ParagraphStyle("QRat", parent=body_style, textColor=colors.HexColor("#334155"))))

            if is_ans and getattr(q, "answer", None):
                story.append(Paragraph(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Clinician Attestation / Findings:</b> {q.answer}",
                    ParagraphStyle("QAns", parent=body_style, textColor=colors.HexColor("#047857"))
                ))
            else:
                story.append(Paragraph(
                    "&nbsp;&nbsp;&nbsp;&nbsp;<b>Clinician Attestation:</b> <i>[Awaiting clinical consultation review]</i>",
                    ParagraphStyle("QPend", parent=body_style, textColor=text_muted)
                ))
            story.append(Spacer(1, 5))
        story.append(Spacer(1, 10))

    # --- Review & Sign-Off ---
    if reviews:
        story.append(Paragraph("7. Clinician Review & Attestation History", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))
        for rev in reviews:
            rev_date = rev.created_at.strftime("%Y-%m-%d %H:%M") if rev.created_at else "N/A"
            action_desc = f"{rev.action} ({rev.entity_type} #{rev.entity_id})"
            story.append(Paragraph(f"• <b>{action_desc}</b> on {rev_date} by Provider ID #{rev.user_id}: {rev.new_value or 'No attestation notes'}", body_style))
        story.append(Spacer(1, 10))

    # --- Footer & Legal Disclaimer ---
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceAfter=6))
    disclaimer_text = (
        "CONFIDENTIAL MEDICAL INTELLIGENCE DOCUMENT. FOR CLINICAL DECISION SUPPORT USE ONLY. "
        "MedLens applies deterministic lab verification, verified range checks, and audit provenance. "
        "All AI-assisted syntheses require review and authorization by a licensed healthcare provider before clinical diagnosis or treatment."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    # Build document
    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()

    filename = f"medlens_report_{p_mrn}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
