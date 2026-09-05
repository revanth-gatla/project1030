"""Tests for reference range engine, normalization, and conflict detection."""

import pytest
from app.analysis.reference_engine import (
    parse_reference_range, calculate_reference_status,
    parse_numeric_value, calculate_change_direction,
)
from app.normalization.normalizer import normalize_parameter_name
from app.analysis.conflict_detector import (
    detect_allergy_conflict, detect_medication_conflict,
    detect_demographic_conflict, detect_duplicate_parameters,
)


# ── Reference Range Parsing ─────────────────────────────────

class TestParseReferenceRange:
    def test_standard_range(self):
        assert parse_reference_range("13-17") == (13.0, 17.0)

    def test_range_with_spaces(self):
        assert parse_reference_range("13 - 17") == (13.0, 17.0)

    def test_range_with_dash(self):
        assert parse_reference_range("13–17") == (13.0, 17.0)

    def test_range_with_unit_suffix(self):
        low, high = parse_reference_range("13-17 g/dL")
        assert low == 13.0
        assert high == 17.0

    def test_less_than(self):
        assert parse_reference_range("< 200") == (None, 200.0)

    def test_greater_than(self):
        assert parse_reference_range("> 40") == (40.0, None)

    def test_up_to(self):
        assert parse_reference_range("Up to 5.7") == (None, 5.7)

    def test_decimal_range(self):
        assert parse_reference_range("0.7 - 1.3") == (0.7, 1.3)

    def test_none(self):
        assert parse_reference_range(None) == (None, None)

    def test_empty(self):
        assert parse_reference_range("") == (None, None)


# ── Reference Status Calculation ────────────────────────────

class TestCalculateReferenceStatus:
    def test_below(self):
        assert calculate_reference_status(10.2, 13.0, 17.0) == "BELOW"

    def test_within(self):
        assert calculate_reference_status(15.0, 13.0, 17.0) == "WITHIN"

    def test_above(self):
        assert calculate_reference_status(18.0, 13.0, 17.0) == "ABOVE"

    def test_at_lower_bound(self):
        assert calculate_reference_status(13.0, 13.0, 17.0) == "WITHIN"

    def test_at_upper_bound(self):
        assert calculate_reference_status(17.0, 13.0, 17.0) == "WITHIN"

    def test_missing_range(self):
        assert calculate_reference_status(10.0, None, None) == "UNKNOWN"

    def test_missing_value(self):
        assert calculate_reference_status(None, 13.0, 17.0) == "UNKNOWN"

    def test_less_than_only(self):
        assert calculate_reference_status(250.0, None, 200.0) == "ABOVE"

    def test_less_than_within(self):
        assert calculate_reference_status(150.0, None, 200.0) == "WITHIN"

    def test_greater_than_only(self):
        assert calculate_reference_status(30.0, 40.0, None) == "BELOW"

    def test_greater_than_within(self):
        assert calculate_reference_status(50.0, 40.0, None) == "WITHIN"


# ── Numeric Parsing ─────────────────────────────────────────

class TestParseNumericValue:
    def test_simple(self):
        assert parse_numeric_value("10.2") == 10.2

    def test_integer(self):
        assert parse_numeric_value("142") == 142.0

    def test_comma(self):
        assert parse_numeric_value("7,400") == 7400.0

    def test_with_operator(self):
        assert parse_numeric_value("> 1000") == 1000.0

    def test_invalid(self):
        assert parse_numeric_value("positive") is None

    def test_empty(self):
        assert parse_numeric_value("") is None


# ── Change Direction ────────────────────────────────────────

class TestCalculateChangeDirection:
    def test_increased(self):
        d, a, p = calculate_change_direction(10.0, 12.0, "g/dL", "g/dL")
        assert d == "INCREASED"
        assert a == 2.0
        assert p == 20.0

    def test_decreased(self):
        d, a, p = calculate_change_direction(12.0, 10.0, "g/dL", "g/dL")
        assert d == "DECREASED"
        assert a == -2.0

    def test_stable(self):
        d, a, p = calculate_change_direction(10.0, 10.0, "g/dL", "g/dL")
        assert d == "STABLE"

    def test_new(self):
        d, a, p = calculate_change_direction(None, 10.0, None, "g/dL")
        assert d == "NEW"

    def test_missing(self):
        d, a, p = calculate_change_direction(10.0, None, "g/dL", None)
        assert d == "MISSING"

    def test_unit_mismatch(self):
        d, a, p = calculate_change_direction(10.0, 100.0, "g/dL", "mg/L")
        assert d == "NOT_COMPARABLE"


# ── Normalization ───────────────────────────────────────────

class TestNormalization:
    def test_hb(self):
        assert normalize_parameter_name("Hb") == "Hemoglobin"

    def test_hgb(self):
        assert normalize_parameter_name("HGB") == "Hemoglobin"

    def test_hemoglobin(self):
        assert normalize_parameter_name("Hemoglobin") == "Hemoglobin"

    def test_haemoglobin(self):
        assert normalize_parameter_name("Haemoglobin") == "Hemoglobin"

    def test_wbc(self):
        assert normalize_parameter_name("WBC") == "White Blood Cell Count"

    def test_sgot(self):
        assert normalize_parameter_name("SGOT") == "Aspartate Aminotransferase (AST)"

    def test_sgpt(self):
        assert normalize_parameter_name("SGPT") == "Alanine Aminotransferase (ALT)"

    def test_tsh(self):
        assert normalize_parameter_name("TSH") == "Thyroid Stimulating Hormone"

    def test_unknown_preserves_original(self):
        result = normalize_parameter_name("Some Custom Test")
        assert result == "Some Custom Test"

    def test_case_insensitive(self):
        assert normalize_parameter_name("hb") == normalize_parameter_name("HB")


# ── Conflict Detection ─────────────────────────────────────

class TestConflictDetection:
    def test_allergy_conflict(self):
        conflicts = detect_allergy_conflict("No known allergies", "Penicillin allergy")
        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "ALLERGY"
        assert conflicts[0]["severity"] == "HIGH"

    def test_no_allergy_conflict(self):
        conflicts = detect_allergy_conflict("Penicillin", "Penicillin")
        assert len(conflicts) == 0

    def test_medication_conflict(self):
        conflicts = detect_medication_conflict("Metformin", "Metformin, Aspirin")
        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "MEDICATION"

    def test_no_medication_conflict(self):
        conflicts = detect_medication_conflict("Metformin", "Metformin")
        assert len(conflicts) == 0

    def test_demographic_age_conflict(self):
        conflicts = detect_demographic_conflict(42, 30, None, None)
        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "DEMOGRAPHIC"

    def test_no_demographic_conflict(self):
        conflicts = detect_demographic_conflict(42, 41, None, None)
        assert len(conflicts) == 0

    def test_sex_conflict(self):
        conflicts = detect_demographic_conflict(None, None, "MALE", "FEMALE")
        assert len(conflicts) == 1

    def test_duplicate_parameters(self):
        lab_results = [
            {"canonical_name": "Hemoglobin", "original_name": "Hb", "observed_value": "10.2"},
            {"canonical_name": "Hemoglobin", "original_name": "HGB", "observed_value": "10.5"},
        ]
        conflicts = detect_duplicate_parameters(lab_results)
        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "DUPLICATE_PARAMETER"
