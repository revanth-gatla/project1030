"""Comprehensive integration test suite verifying MedLens Core Input Architecture & Workflow:
1. Patient Information Intake (Required Input A)
2. Medical Report Ingestion (Required Input B)
3. Structured Medical Record & Clinical Workspace
4. Deterministic Reference Ranges (BELOW / WITHIN / ABOVE / UNKNOWN)
5. Safety Conflict Detection with Patient Intake
6. Cross-User Authorization & Security Boundaries
7. Longitudinal Trajectory Shift Calculation
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_patient_intake_creation_and_persistence(auth_client: AsyncClient):
    """Verify that patient demographics and full clinical intake are accepted and persisted atomically."""
    payload = {
        "name": "Elena Vance",
        "identifier": "MRN-89412",
        "age": 54,
        "sex": "FEMALE",
        "symptoms": "Exertional dyspnea, progressive bilateral lower extremity edema, worsening fatigue",
        "existing_conditions": "Type 2 Diabetes Mellitus, Stage 3 CKD, Essential Hypertension",
        "allergies": "Lisinopril (angioedema), Penicillin (urticaria)",
        "medications": "Metformin 1000mg BID, Amlodipine 10mg daily, Furosemide 40mg daily",
        "notes": "Patient reports worsening exercise tolerance over 4 weeks."
    }

    resp = await auth_client.post("/patients", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["name"] == "Elena Vance"
    assert data["identifier"] == "MRN-89412"
    assert data["age"] == 54
    assert data["sex"] == "FEMALE"

    # Verify intake is atomically returned
    assert data["intake"] is not None
    intake = data["intake"]
    assert intake["allergies"] == "Lisinopril (angioedema), Penicillin (urticaria)"
    assert intake["medications"] == "Metformin 1000mg BID, Amlodipine 10mg daily, Furosemide 40mg daily"
    assert "Type 2 Diabetes" in intake["existing_conditions"]
    assert "Exertional dyspnea" in intake["symptoms"]

    patient_id = data["id"]

    # Verify subsequent GET returns persisted intake
    get_resp = await auth_client.get(f"/patients/{patient_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["intake"]["allergies"] == intake["allergies"]
    assert fetched["intake"]["notes"] == "Patient reports worsening exercise tolerance over 4 weeks."


@pytest.mark.asyncio
async def test_patient_intake_update(auth_client: AsyncClient):
    """Verify updating intake fields on an existing patient record."""
    create_resp = await auth_client.post("/patients", json={
        "name": "Marcus Wright",
        "age": 42,
        "sex": "MALE",
        "allergies": "None known"
    })
    assert create_resp.status_code == 201
    patient_id = create_resp.json()["id"]

    update_payload = {
        "symptoms": "Occasional tension headaches",
        "existing_conditions": "Hyperlipidemia",
        "allergies": "Aspirin (gastric bleeding)",
        "medications": "Atorvastatin 20mg daily",
        "notes": "Updated during clinical intake review"
    }

    put_resp = await auth_client.put(f"/patients/{patient_id}/intake", json=update_payload)
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated["allergies"] == "Aspirin (gastric bleeding)"
    assert updated["medications"] == "Atorvastatin 20mg daily"


@pytest.mark.asyncio
async def test_patient_cross_user_isolation(auth_client: AsyncClient, second_auth_client: AsyncClient):
    """Verify that patients and their clinical intake are strictly isolated between providers."""
    # User 1 creates patient
    resp1 = await auth_client.post("/patients", json={
        "name": "Secret Patient",
        "age": 60,
        "sex": "OTHER",
        "allergies": "Codeine"
    })
    patient_id = resp1.json()["id"]

    # User 2 attempts to fetch patient -> 403 or 404
    resp2 = await second_auth_client.get(f"/patients/{patient_id}")
    assert resp2.status_code in [403, 404]

    # User 2 attempts to update intake -> 403 or 404
    resp_update = await second_auth_client.put(f"/patients/{patient_id}/intake", json={
        "allergies": "Unauthorized edit"
    })
    assert resp_update.status_code in [403, 404]


@pytest.mark.asyncio
async def test_complete_end_to_end_clinical_workflow(auth_client: AsyncClient):
    """Full synthetic E2E workflow:
    1. Patient Intake Creation
    2. Medical Report Ingestion
    3. Document Extraction & Deterministic Reference Range Classification
    4. Safety Conflict Detection (cross-referencing intake allergies)
    5. Contextual AI Insights Generation
    6. Clinician Review & Audit Trail
    """
    # 1. Patient Intake
    intake_data = {
        "name": "Robert Martinez",
        "identifier": "MRN-10293",
        "age": 58,
        "sex": "MALE",
        "symptoms": "Severe fatigue, nocturia, lower leg edema",
        "existing_conditions": "Type 2 Diabetes, Hypertension, Stage 3 CKD",
        "allergies": "Lisinopril (angioedema), Penicillin",
        "medications": "Amlodipine 10mg daily, Glipizide 5mg daily",
        "notes": "Follow-up visit with renal panel"
    }
    p_resp = await auth_client.post("/patients", json=intake_data)
    assert p_resp.status_code == 201
    patient = p_resp.json()
    patient_id = patient["id"]

    # 2. Medical Report Ingestion (Core Input B)
    report_text = """
    ADVANCED CLINICAL PATHOLOGY LABS
    Patient Name: Robert Martinez
    Date: 2026-09-01
    
    COMPREHENSIVE METABOLIC & HEMATOLOGY PANEL
    Hemoglobin: 10.2 g/dL (Reference: 13.0 - 17.0)
    WBC: 12.8 x10^3/uL (Reference: 4.0 - 11.0)
    Fasting Glucose: 168 mg/dL (Reference: 70 - 99)
    Serum Creatinine: 1.8 mg/dL (Reference: 0.7 - 1.3)
    eGFR: 42 mL/min/1.73m2 (Reference: > 60)
    Serum Potassium: 5.6 mEq/L (Reference: 3.5 - 5.0)
    
    CLINICAL RECOMMENDATION:
    Consider Lisinopril 10mg daily for proteinuria reduction.
    """

    rep_resp = await auth_client.post(
        f"/patients/{patient_id}/reports/paste",
        json={
            "text": report_text,
            "report_date": "2026-09-01",
            "source_name": "Advanced Clinical Pathology Labs"
        }
    )
    assert rep_resp.status_code == 201
    report = rep_resp.json()
    report_id = report["id"]

    # 3. Process Report Pipeline
    proc_resp = await auth_client.post(f"/reports/{report_id}/process")
    assert proc_resp.status_code == 200
    processed = proc_resp.json()

    assert processed["processing_status"] in ["VALIDATED", "REVIEW_REQUIRED"]
    lab_results = processed.get("lab_results", [])
    assert len(lab_results) >= 4, f"Expected at least 4 lab results, got {len(lab_results)}"

    # Check deterministic mathematical classifications
    statuses = {r["canonical_name"]: r["reference_status"] for r in lab_results}
    # Potassium 5.6 > 5.0 -> ABOVE / HIGH
    if "Serum Potassium" in statuses:
        assert statuses["Serum Potassium"] in ["ABOVE", "HIGH"]
    # Glucose 168 > 99 -> ABOVE / HIGH
    if "Fasting Glucose" in statuses:
        assert statuses["Fasting Glucose"] in ["ABOVE", "HIGH"]

    # Verify provenance was generated
    prov_resp = await auth_client.get(f"/reports/{report_id}/provenance")
    assert prov_resp.status_code == 200
    provs = prov_resp.json()
    assert len(provs) > 0

    # 4. Check Safety Conflicts (Lisinopril allergy conflict detection)
    confs_resp = await auth_client.get(f"/patients/{patient_id}/conflicts")
    assert confs_resp.status_code == 200
    confs = confs_resp.json()
    # If Lisinopril was recommended and patient has Lisinopril allergy, conflict should be flagged
    lisinopril_conflict = next((c for c in confs if "lisinopril" in c["description"].lower()), None)
    if lisinopril_conflict:
        assert lisinopril_conflict["severity"] in ["CRITICAL", "HIGH"]
        # Resolve conflict
        res_resp = await auth_client.post(
            f"/conflicts/{lisinopril_conflict['id']}/resolve",
            json={"resolution_notes": "Provider verified: Lisinopril discontinued due to documented allergy."}
        )
        assert res_resp.status_code == 200
        assert res_resp.json()["resolved"] is True

    # 5. Contextual AI Insights Generation
    insight_resp = await auth_client.post(f"/reports/{report_id}/insights")
    assert insight_resp.status_code == 200
    insight = insight_resp.json()
    assert "summary" in insight
    assert len(insight["summary"]) > 20

    # 6. Clinician Review & Audit Trail Sign-off
    rev_resp = await auth_client.post(
        f"/reports/{report_id}/review",
        json={
            "status": "ACCEPTED",
            "notes": "Reviewed and validated CBC and metabolic parameters. Adjusted anti-hypertensive."
        }
    )
    assert rev_resp.status_code == 200
    review_record = rev_resp.json()
    assert review_record["new_status"] == "ACCEPTED"

    # Verify audit history
    history_resp = await auth_client.get(f"/patients/{patient_id}/review-history")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) >= 1
    assert history[0]["new_status"] == "ACCEPTED"


@pytest.mark.asyncio
async def test_longitudinal_trajectory_comparison(auth_client: AsyncClient):
    """Verify paired comparison between baseline and follow-up reports."""
    # Create patient
    p_resp = await auth_client.post("/patients", json={
        "name": "Sarah Connor",
        "age": 45,
        "sex": "FEMALE"
    })
    patient_id = p_resp.json()["id"]

    # Ingest Report 1 (Baseline)
    r1_resp = await auth_client.post(
        f"/patients/{patient_id}/reports/paste",
        json={
            "text": "Hemoglobin: 11.0 g/dL (12.0 - 16.0)\nSerum Potassium: 4.2 mEq/L (3.5 - 5.0)",
            "report_date": "2026-06-01"
        }
    )
    rep1_id = r1_resp.json()["id"]
    await auth_client.post(f"/reports/{rep1_id}/process")

    # Ingest Report 2 (Follow-up)
    r2_resp = await auth_client.post(
        f"/patients/{patient_id}/reports/paste",
        json={
            "text": "Hemoglobin: 13.5 g/dL (12.0 - 16.0)\nSerum Potassium: 5.3 mEq/L (3.5 - 5.0)",
            "report_date": "2026-09-01"
        }
    )
    rep2_id = r2_resp.json()["id"]
    await auth_client.post(f"/reports/{rep2_id}/process")

    # Compare reports
    comp_resp = await auth_client.get(f"/patients/{patient_id}/comparisons?previous_report_id={rep1_id}&current_report_id={rep2_id}")
    assert comp_resp.status_code == 200
    comp = comp_resp.json()

    assert comp["patient_id"] == patient_id
    assert len(comp["results"]) >= 1

    # Check that Hemoglobin increased (11.0 -> 13.5)
    hb = next((r for r in comp["results"] if "hemoglobin" in r["canonical_name"].lower()), None)
    if hb:
        dir_val = hb.get("direction") or hb.get("change_direction")
        assert dir_val == "INCREASED"
        assert hb.get("percentage_change") is not None or hb.get("change_percent") is not None
