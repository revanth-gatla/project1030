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
