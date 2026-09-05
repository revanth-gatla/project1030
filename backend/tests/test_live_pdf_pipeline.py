import os
import sqlite3
import pytest
import requests
from app.core.auth import create_access_token

@pytest.mark.skipif(
    os.getenv("RUN_LIVE_TESTS") != "1",
    reason="Requires live running backend server at http://127.0.0.1:8001",
)
def test_pipeline():
    token = create_access_token(10)
    headers = {"Authorization": f"Bearer {token}"}

    # Verify patient 7
    r_pt = requests.get("http://127.0.0.1:8001/patients/7", headers=headers)
    assert r_pt.status_code == 200, r_pt.text
    pt_data = r_pt.json()
    print(f"Verified Patient: {pt_data['name']} ({pt_data['identifier']})")

    # Clean up incomplete reports for patient 7
    conn = sqlite3.connect("medlens.db")
    c = conn.cursor()
    c.execute("DELETE FROM reports WHERE patient_id=7 AND (processing_status='UPLOADED' OR processing_status='FAILED')")
    conn.commit()
    conn.close()

    # Upload PDF
    pdf_path = r"C:\Users\rishi\Downloads\MedLens_Previous_Medical_Report_Arjun_PT-10001.pdf"
    assert os.path.exists(pdf_path), f"File not found: {pdf_path}"

    with open(pdf_path, "rb") as f:
        files = {"file": ("MedLens_Previous_Medical_Report_Arjun_PT-10001.pdf", f, "application/pdf")}
        r_up = requests.post("http://127.0.0.1:8001/patients/7/reports", headers=headers, files=files)

    assert r_up.status_code == 201, r_up.text
    up_data = r_up.json()
    report_id = up_data["id"]
    print(f"Uploaded Report ID: {report_id}, initial date: {up_data.get('report_date')}")

    # Process report
    r_proc = requests.post(f"http://127.0.0.1:8001/reports/{report_id}/process", headers=headers)
    assert r_proc.status_code == 200, r_proc.text
    proc_data = r_proc.json()

    print(f"Processed Report Status: {proc_data['processing_status']}")
    print(f"Processed Report Date: {proc_data['report_date']}")
    assert proc_data["report_date"] is not None
    assert "2026-06-05" in proc_data["report_date"], f"Expected 2026-06-05, got {proc_data['report_date']}"

    labs = proc_data.get("lab_results", [])
    print(f"Extracted Lab Parameters Count: {len(labs)}")
    assert len(labs) == 13, f"Expected 13 lab parameters, got {len(labs)}"

    for lr in labs:
        print(f"  {lr['original_name']} -> canonical: '{lr['canonical_name']}': {lr['observed_value']} {lr['unit']} (Ref: {lr['reference_range_text']})")
        assert "reference range" not in lr["canonical_name"].lower()
        assert "reference range" not in lr["original_name"].lower()

    # Test longitudinal comparison against September 5 report (report_id=18)
    r_comp = requests.post(
        "http://127.0.0.1:8001/patients/7/comparisons",
        headers=headers,
        json={"previous_report_id": report_id, "current_report_id": 18}
    )
    assert r_comp.status_code == 201, r_comp.text
    comp_data = r_comp.json()
    results = comp_data.get("results", [])
    print(f"\nLongitudinal Comparison Results Count: {len(results)}")
    assert len(results) == 13, f"Expected 13 paired results, got {len(results)}"

    for cr in results:
        print(f"  {cr['canonical_name']}: Baseline(June)={cr['previous_value']} -> Current(Sept)={cr['current_value']} [{cr['current_unit']}] | Direction={cr['direction']} Delta={cr['absolute_change']} Change={cr['percentage_change']}%")
        assert cr["previous_value"] is not None, f"Baseline value missing for {cr['canonical_name']}"
        assert cr["current_value"] is not None, f"Current value missing for {cr['canonical_name']}"

    print("\nALL END-TO-END PIPELINE CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_pipeline()
