"""Automated tests for Reference Range extraction fix, validation, and conflict deduplication."""

import pytest
from app.extraction.ai_provider import _fallback_rule_extraction
from app.normalization.normalizer import is_disallowed_parameter_name, normalize_parameter_name
from app.analysis.reference_engine import parse_reference_range, calculate_reference_status
from app.analysis.conflict_detector import (
    detect_duplicate_parameters,
    detect_allergy_conflict,
    detect_medication_conflict,
)


def test_exact_user_test_case_extraction():
    """Verify exact test case specified in user requirements.

    Report content:
    Hemoglobin (Hb): 13.8 g/dL
    Reference Range: 13.0 - 17.0 g/dL

    Fasting Blood Glucose: 142 mg/dL
    Reference Range: 70 - 99 mg/dL

    HbA1c: 7.2 %
    Reference Range: 4.0 - 5.6 %
    """
    report_text = """
    Hemoglobin (Hb): 13.8 g/dL
    Reference Range: 13.0 - 17.0 g/dL

    Fasting Blood Glucose: 142 mg/dL
    Reference Range: 70 - 99 mg/dL

    HbA1c: 7.2 %
    Reference Range: 4.0 - 5.6 %
    """

    res = _fallback_rule_extraction(report_text)

    # 1. Verify exactly 3 parameters are extracted
    assert len(res.parameters) == 3, f"Expected 3 parameters, got {len(res.parameters)}"

    p0, p1, p2 = res.parameters

    # 2. Verify Hemoglobin parameter
    assert p0.original_name == "Hemoglobin (Hb)"
    assert normalize_parameter_name(p0.original_name) == "Hemoglobin"
    assert p0.observed_value == "13.8"
    assert p0.unit == "g/dL"
    assert p0.reference_range == "13.0 - 17.0 g/dL"
    low0, high0 = parse_reference_range(p0.reference_range)
    assert (low0, high0) == (13.0, 17.0)
    assert calculate_reference_status(float(p0.observed_value), low0, high0) == "WITHIN"

    # 3. Verify Fasting Blood Glucose parameter
    assert p1.original_name == "Fasting Blood Glucose"
    assert normalize_parameter_name(p1.original_name) == "Fasting Blood Sugar"
    assert p1.observed_value == "142"
    assert p1.unit == "mg/dL"
    assert p1.reference_range == "70 - 99 mg/dL"
    low1, high1 = parse_reference_range(p1.reference_range)
    assert (low1, high1) == (70.0, 99.0)
    assert calculate_reference_status(float(p1.observed_value), low1, high1) == "ABOVE"

    # 4. Verify HbA1c parameter
    assert p2.original_name == "HbA1c"
    assert normalize_parameter_name(p2.original_name) == "Glycated Hemoglobin (HbA1c)"
    assert p2.observed_value == "7.2"
    assert p2.unit == "%"
    assert p2.reference_range == "4.0 - 5.6 %"
    low2, high2 = parse_reference_range(p2.reference_range)
    assert (low2, high2) == (4.0, 5.6)
    assert calculate_reference_status(float(p2.observed_value), low2, high2) == "ABOVE"

    # 5. Verify "Reference Range" itself is NEVER extracted as a parameter
    for p in res.parameters:
        assert "reference range" not in p.original_name.lower()
        assert not is_disallowed_parameter_name(p.original_name)

    # 6. Verify duplicate conflict detection finds 0 false duplicate conflicts
    lab_data = [
        {
            "original_name": p.original_name,
            "canonical_name": normalize_parameter_name(p.original_name),
            "observed_value": p.observed_value,
        }
        for p in res.parameters
    ]
    conflicts = detect_duplicate_parameters(lab_data)
    assert len(conflicts) == 0, f"Expected 0 duplicate parameter conflicts, got: {conflicts}"


def test_disallowed_parameter_validation():
    """Verify validation strictly rejects field labels/headers while preserving legitimate tests."""
    disallowed = [
        "Reference Range",
        "Reference Range:",
        "Reference",
        "Normal Range",
        "Normal Range:",
        "Reference Interval",
        "Biological Reference Interval",
        "Result",
        "Results",
        "Unit",
        "Units",
        "Value",
        "Values",
        "Test Name",
        "Test Name:",
        "Flag",
        "Status",
        "Observations",
        "Observations:",
        "Comment",
        "Notes",
    ]
    for term in disallowed:
        assert is_disallowed_parameter_name(term) is True, f"Expected '{term}' to be disallowed"

    # Verify legitimate clinical tests are NOT disallowed
    allowed = [
        "Hemoglobin",
        "Hemoglobin (Hb)",
        "White Blood Cell Count",
        "Platelet Count",
        "Fasting Blood Glucose",
        "HbA1c",
        "Total Cholesterol",
        "HDL Cholesterol",
        "LDL Cholesterol",
        "Triglycerides",
        "Serum Creatinine",
        "Creatinine",
        "Blood Urea Nitrogen",
        "eGFR",
        "Serum Potassium",
        "Total Bilirubin",
        "ALT",
        "AST",
        "TSH",
    ]
    for term in allowed:
        assert is_disallowed_parameter_name(term) is False, f"Expected '{term}' to be allowed"


def test_reference_range_with_commas_and_unicode_units():
    """Verify parse_reference_range cleanly handles thousands commas and unicode symbols."""
    # WBC range: 4,000 - 11,000 cells/µL
    low, high = parse_reference_range("4,000 - 11,000 cells/µL")
    assert (low, high) == (4000.0, 11000.0)

    # Platelets: 150,000 - 450,000 /uL
    low, high = parse_reference_range("150,000 - 450,000 /uL")
    assert (low, high) == (150000.0, 450000.0)

    # Glucose: 70 - 99 mg/dL
    low, high = parse_reference_range("70 - 99 mg/dL")
    assert (low, high) == (70.0, 99.0)

    # Less than with unit: < 200 mg/dL
    low, high = parse_reference_range("< 200 mg/dL")
    assert (low, high) == (None, 200.0)

    # Greater than with unit: > 60 mL/min
    low, high = parse_reference_range("> 60 mL/min")
    assert (low, high) == (60.0, None)


def test_valid_clinical_conflicts_preserved():
    """Verify that legitimate clinical conflicts (e.g. allergies, medications) still function correctly."""
    # Allergy conflict: no known allergies in intake vs documented allergy
    allergy_conflicts = detect_allergy_conflict("No known allergies", "Lisinopril, Penicillin")
    assert len(allergy_conflicts) == 1
    assert allergy_conflicts[0]["conflict_type"] == "ALLERGY"
    assert allergy_conflicts[0]["severity"] == "HIGH"

    # Medication discrepancy: discontinued medication
    med_conflicts = detect_medication_conflict("Amlodipine 10mg", "Amlodipine 10mg, Glipizide 5mg")
    assert len(med_conflicts) == 1
    assert med_conflicts[0]["conflict_type"] == "MEDICATION"
    assert "glipizide 5mg" in med_conflicts[0]["description"]


@pytest.mark.asyncio
async def test_duplicate_conflict_persistence_prevention(db_session):
    """Verify that re-processing reports or running conflict detection does not duplicate conflicts."""
    from app.models.patient import Patient, Sex
    from app.models.report import Report, ProcessingStatus
    from app.services.report_service import process_report
    from sqlalchemy import select
    from app.models.analysis import Conflict

    from app.models.user import User
    from app.core.auth import hash_password

    # Create test user
    user = User(email="conflict_test@medlens.dev", password_hash=hash_password("pw123"), is_active=True)
    db_session.add(user)
    await db_session.flush()

    # Create test patient
    patient = Patient(owner_user_id=user.id, identifier="PT-TEST-001", name="Conflict Test Patient", age=45, sex=Sex.MALE)
    db_session.add(patient)
    await db_session.flush()

    # Report text containing duplicate parameter: e.g. two separate glucose entries
    report_text = """
    Fasting Blood Glucose: 142 mg/dL
    Reference Range: 70 - 99 mg/dL

    Fasting Blood Glucose: 148 mg/dL
    Reference Range: 70 - 99 mg/dL
    """

    report = Report(
        patient_id=patient.id,
        raw_text=report_text,
        content_hash="test-hash-dup-prevention-1",
        processing_status=ProcessingStatus.UPLOADED,
    )
    db_session.add(report)
    await db_session.flush()

    # Process first time
    await process_report(report, db_session)

    confs_first = (await db_session.execute(select(Conflict).where(Conflict.patient_id == patient.id))).scalars().all()
    assert len(confs_first) == 1, f"Expected 1 duplicate parameter conflict, got {len(confs_first)}"

    # Process second time (reprocessing)
    await process_report(report, db_session)

    confs_second = (await db_session.execute(select(Conflict).where(Conflict.patient_id == patient.id))).scalars().all()
    # Must STILL be exactly 1 conflict record, NOT 2
    assert len(confs_second) == 1, f"Expected exactly 1 conflict after reprocessing, got {len(confs_second)}"


def test_undesirable_and_differential_percentage_counts():
    """Verify corrupted cutoff tiers are rejected and differential percentage counts are evaluated accurately."""
    from app.analysis.reference_engine import parse_numeric_value, parse_reference_range, calculate_reference_status
    from app.normalization.normalizer import is_disallowed_parameter_name

    # 1. Reject cutoff tiers and risk headers extracted by OCR/PDF space artifacts
    assert is_disallowed_parameter_name("Undesir Able") is True
    assert is_disallowed_parameter_name("Moder Ate Risk") is True
    assert is_disallowed_parameter_name("Borderline : 200 - 239") is True
    assert is_disallowed_parameter_name("Near Optimal") is True
    assert is_disallowed_parameter_name("Average Risk: 4.5-7.1") is True

    # Legitimate tests must never be rejected
    assert is_disallowed_parameter_name("Neutrophils") is False
    assert is_disallowed_parameter_name("Lymphocytes") is False
    assert is_disallowed_parameter_name("Monocytes") is False
    assert is_disallowed_parameter_name("Eosinophils") is False
    assert is_disallowed_parameter_name("Basophils") is False

    # 2. Differential Leukocyte Counts (DLC) measured in % with compound ranges
    neutro_low, neutro_high = parse_reference_range("2.0-7.5 X 10³/uL (40 - 80%)", unit="%", observed_value="61.1 %")
    assert (neutro_low, neutro_high) == (40.0, 80.0)
    assert calculate_reference_status(61.1, neutro_low, neutro_high) == "WITHIN"

    lympho_low, lympho_high = parse_reference_range("1.0-4.0 X 10³/uL (20 - 40%)", unit="%", observed_value="29.6 %")
    assert (lympho_low, lympho_high) == (20.0, 40.0)
    assert calculate_reference_status(29.6, lympho_low, lympho_high) == "WITHIN"

    mono_low, mono_high = parse_reference_range("0.2-1.0 X 10³/uL (2 - 10%)", unit="%", observed_value="5.3 %")
    assert (mono_low, mono_high) == (2.0, 10.0)
    assert calculate_reference_status(5.3, mono_low, mono_high) == "WITHIN"

    eosino_low, eosino_high = parse_reference_range("0.02-0.5 X 10³/uL (1-6%)", unit="%", observed_value="3.1 %")
    assert (eosino_low, eosino_high) == (1.0, 6.0)
    assert calculate_reference_status(3.1, eosino_low, eosino_high) == "WITHIN"

    baso_low, baso_high = parse_reference_range("0.02 - 0.1 X 10³/uL (1-2%) | Borderline: 200 - 239", unit="%", observed_value="0.9 %")
    assert (baso_low, baso_high) == (1.0, 2.0)
    assert calculate_reference_status(0.9, baso_low, baso_high) == "LOW"

    # 3. Numeric values with operators
    assert parse_numeric_value("> 240 mg/dL") == 240.0
    assert parse_numeric_value("<40 mg/dL") == 40.0
    assert parse_numeric_value("7.2 -11.0") == 7.2


def test_dad_report_clinical_summary_extraction():
    """Verify that clinical summary reports (e.g. dad_report.pdf) extract pure biomarkers without intake leakage."""
    import os
    from app.extraction.ai_provider import _fallback_rule_extraction
    from app.extraction.document_processor import clean_text, extract_text
    from app.normalization.normalizer import is_disallowed_parameter_name
    from app.analysis.reference_engine import calculate_reference_status, parse_reference_range

    dad_pdf_path = r"C:\Users\rishi\Downloads\dad_report.pdf"
    if not os.path.exists(dad_pdf_path):
        return

    with open(dad_pdf_path, "rb") as f:
        text = extract_text("dad_report.pdf", f.read())
    cleaned = clean_text(text)
    res = _fallback_rule_extraction(cleaned)

    # Must extract the 52 lab results cleanly
    assert len(res.parameters) == 52, f"Expected 52 parameters, got {len(res.parameters)}"

    names = [p.original_name for p in res.parameters]

    # Must NOT contain intake, metadata, medications, symptoms
    for bad in ("ashokgatla57@gmail.com", "Amlodipine", "fatigue.", "Clinical Biochemistry", "Pending"):
        assert bad not in names, f"Corrupted parameter '{bad}' was extracted!"

    for p in res.parameters:
        assert not is_disallowed_parameter_name(p.original_name)
        assert not is_disallowed_parameter_name(p.canonical_name if hasattr(p, "canonical_name") else p.original_name)

    # Verify Hemoglobin has reference range and is WITHIN
    hb = next((p for p in res.parameters if "hemoglobin" in p.original_name.lower()), None)
    assert hb is not None
    assert hb.observed_value == "13.2"
    assert hb.reference_range == "13.0 - 17.0"
    low, high = parse_reference_range(hb.reference_range)
    assert calculate_reference_status(13.2, low, high) == "WITHIN"

    # Verify Fasting Glucose has reference range and is HIGH
    glu = next((p for p in res.parameters if "glucose" in p.original_name.lower()), None)
    assert glu is not None
    assert glu.observed_value == "128.0"
    assert glu.reference_range == "70.0 - 99.0"
    low_g, high_g = parse_reference_range(glu.reference_range)
    assert calculate_reference_status(128.0, low_g, high_g) == "HIGH"


