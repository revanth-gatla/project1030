import pytest
from httpx import AsyncClient
from app.extraction.ai_provider import get_ai_provider
from app.normalization.normalizer import is_disallowed_parameter_name, normalize_parameter_name
from app.analysis.reference_engine import calculate_reference_status, parse_reference_range, parse_numeric_value

ARJUN_PREVIOUS_REPORT_TEXT = """
MEDICAL LABORATORY REPORT
Previous report · Synthetic demonstration data · Not for clinical use
Patient Name: Arjun
Patient ID: PT-10001
Age: 42
Sex: Male
Report Date: 05 June 2026
Report Type: Routine Laboratory Panel

COMPLETE BLOOD COUNT
Test / Parameter Observed Value Unit Reference Range
Hemoglobin (Hb) 13.2 g/dL 13.0 - 17.0
White Blood Cell Count (WBC) 8,200 cells/uL 4,000 - 11,000
Platelet Count 238,000 cells/uL 150,000 - 450,000

BIOCHEMISTRY
Test / Parameter Observed Value Unit Reference Range
Fasting Blood Glucose 128 mg/dL 70 - 99
HbA1c 6.8 % 4.0 - 5.6
Total Cholesterol 205 mg/dL 125 - 200
HDL Cholesterol 46 mg/dL 40 - 60
LDL Cholesterol 134 mg/dL 0 - 100
Triglycerides 149 mg/dL 50 - 150
Creatinine 1.0 mg/dL 0.7 - 1.3
BUN 17 mg/dL 7 - 20
ALT 30 U/L 7 - 56
AST 28 U/L 10 - 40

OBSERVATIONS
Fasting glucose and HbA1c are above the provided reference ranges. Total cholesterol and LDL cholesterol
are above the provided reference ranges. Triglycerides are within the provided range but near its upper
limit. Other reported parameters are within their provided reference ranges.
"""

EXPECTED_BENCHMARK = {
    "Hemoglobin": {"val": 13.2, "unit": "g/dL", "ref": "13.0 - 17.0", "status": "WITHIN"},
    "White Blood Cell Count": {"val": 8200, "unit": "cells/uL", "ref": "4,000 - 11,000", "status": "WITHIN"},
    "Platelet Count": {"val": 238000, "unit": "cells/uL", "ref": "150,000 - 450,000", "status": "WITHIN"},
    "Fasting Blood Sugar": {"val": 128, "unit": "mg/dL", "ref": "70 - 99", "status": "HIGH"},
    "Glycated Hemoglobin (HbA1c)": {"val": 6.8, "unit": "%", "ref": "4.0 - 5.6", "status": "HIGH"},
    "Total Cholesterol": {"val": 205, "unit": "mg/dL", "ref": "125 - 200", "status": "HIGH"},
    "HDL Cholesterol": {"val": 46, "unit": "mg/dL", "ref": "40 - 60", "status": "WITHIN"},
    "LDL Cholesterol": {"val": 134, "unit": "mg/dL", "ref": "0 - 100", "status": "HIGH"},
    "Triglycerides": {"val": 149, "unit": "mg/dL", "ref": "50 - 150", "status": "WITHIN"},
    "Creatinine": {"val": 1.0, "unit": "mg/dL", "ref": "0.7 - 1.3", "status": "WITHIN"},
    "Blood Urea Nitrogen": {"val": 17, "unit": "mg/dL", "ref": "7 - 20", "status": "WITHIN"},
    "Alanine Aminotransferase (ALT)": {"val": 30, "unit": "U/L", "ref": "7 - 56", "status": "WITHIN"},
    "Aspartate Aminotransferase (AST)": {"val": 28, "unit": "U/L", "ref": "10 - 40", "status": "WITHIN"},
}

@pytest.mark.asyncio
async def test_arjun_extraction_and_classification():
    provider = get_ai_provider()
    extraction = await provider.extract_report(ARJUN_PREVIOUS_REPORT_TEXT)

    # 1. Verify extraction extracted 13 parameters
    params = extraction.parameters
    assert len(params) == 13, f"Expected 13 parameters, got {len(params)}"

    # 2. Confirm there is NO parameter named "Reference Range"
    for p in params:
        assert not is_disallowed_parameter_name(p.original_name), f"Disallowed parameter extracted: {p.original_name}"
        assert "reference" not in p.original_name.lower()
        # 5. Confirm confidence is NOT hardcoded to 0.95
        assert p.confidence != 0.95, f"Confidence hardcoded to 0.95 on {p.original_name}"

    # 3. Test normalization and deterministic classification for all 13 items
    for p in params:
        canonical = normalize_parameter_name(p.original_name)
        assert canonical in EXPECTED_BENCHMARK, f"Unexpected canonical name {canonical}"

        bench = EXPECTED_BENCHMARK[canonical]
        val_num = parse_numeric_value(p.observed_value)
        low, high = parse_reference_range(p.reference_range)
        status = calculate_reference_status(val_num, low, high)

        assert status == bench["status"], f"Status mismatch for {canonical}: expected {bench['status']}, got {status}"
        assert p.reference_range is not None
        assert len(p.reference_range) > 0


@pytest.mark.asyncio
async def test_arjun_full_pipeline_api(auth_client: AsyncClient):
    # Create synthetic patient Arjun
    p_resp = await auth_client.post(
        "/patients",
        json={
            "name": "Arjun Mehta",
            "identifier": "PT-VERIFY-01",
            "age": 42,
            "sex": "MALE",
        },
    )
    assert p_resp.status_code == 201
    patient_id = p_resp.json()["id"]

    # Ingest Report
    r_resp = await auth_client.post(
        f"/patients/{patient_id}/reports/paste",
        json={
            "text": ARJUN_PREVIOUS_REPORT_TEXT,
            "report_date": "2026-06-05",
            "source_name": "Routine Laboratory Panel",
        },
    )
    assert r_resp.status_code == 201
    report_id = r_resp.json()["id"]

    # Process Report
    proc_resp = await auth_client.post(f"/reports/{report_id}/process")
    assert proc_resp.status_code == 200
    report_data = proc_resp.json()

    lab_results = report_data.get("lab_results", [])
    assert len(lab_results) == 13

    # Confirm no "Reference Range" parameter
    param_names = [r["original_name"].lower() for r in lab_results]
    for name in param_names:
        assert "reference" not in name

    # Confirm confidence is not hardcoded 95%
    for r in lab_results:
        assert r["confidence"] != 0.95

    # Confirm deterministic statuses
    status_map = {r["canonical_name"]: r["reference_status"] for r in lab_results}
    for canon, bench in EXPECTED_BENCHMARK.items():
        assert canon in status_map, f"Missing {canon} in results"
        assert status_map[canon] == bench["status"], f"Status mismatch for {canon}: {status_map[canon]} != {bench['status']}"

    # Confirm provenance exists
    prov_resp = await auth_client.get(f"/reports/{report_id}/provenance")
    assert prov_resp.status_code == 200
    provs = prov_resp.json()
    assert len(provs) == 13

    # Confirm no duplicate parameter conflicts
    conf_resp = await auth_client.get(f"/patients/{patient_id}/conflicts")
    assert conf_resp.status_code == 200
    conflicts = conf_resp.json()
    dupe_confs = [c for c in conflicts if c["conflict_type"] == "DUPLICATE_PARAMETER"]
    assert len(dupe_confs) == 0
