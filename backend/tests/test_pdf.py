"""Tests for PDF report generation endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPdfReport:
    async def test_pdf_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/patients/1/report/pdf")
        assert resp.status_code == 401

    async def test_pdf_generation_success(self, auth_client: AsyncClient):
        # 1. Create a patient
        create_resp = await auth_client.post("/patients", json={
            "name": "Jane Medical",
            "age": 45,
            "sex": "FEMALE",
            "identifier": "MRN-12345",
            "symptoms": "Occasional dizziness and shortness of breath",
            "existing_conditions": "Hypertension",
            "allergies": "Penicillin",
            "medications": "Lisinopril 10mg daily",
            "notes": "Follow-up in 3 months",
        })
        assert create_resp.status_code == 201
        patient_id = create_resp.json()["id"]

        # 2. Ingest a report
        report_resp = await auth_client.post(f"/patients/{patient_id}/reports/paste", json={
            "text": "Hemoglobin: 13.5 g/dL (Reference: 12.0 - 16.0)\nPotassium: 4.2 mEq/L (Reference: 3.5 - 5.0)",
            "report_date": "2026-03-01",
            "source_name": "Hospital Central Lab",
        })
        assert report_resp.status_code == 201

        # 3. Download PDF report
        pdf_resp = await auth_client.get(f"/patients/{patient_id}/report/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert "attachment;" in pdf_resp.headers["content-disposition"]
        # PDF bytes start with magic bytes %PDF-
        assert pdf_resp.content.startswith(b"%PDF-")
        assert len(pdf_resp.content) > 500

    async def test_pdf_nonexistent_patient(self, auth_client: AsyncClient):
        resp = await auth_client.get("/patients/999999/report/pdf")
        assert resp.status_code == 404
