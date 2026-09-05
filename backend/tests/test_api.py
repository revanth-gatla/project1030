"""API tests — auth, patients, authorization."""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuth:
    async def test_register(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={
            "email": "new@medlens.dev",
            "password": "securepass123",
        })
        assert resp.status_code == 201
        assert "access_token" in resp.json()

    async def test_register_duplicate(self, client: AsyncClient):
        await client.post("/auth/register", json={"email": "dup@medlens.dev", "password": "securepass123"})
        resp = await client.post("/auth/register", json={"email": "dup@medlens.dev", "password": "securepass123"})
        assert resp.status_code == 409
        assert resp.json()["error"]["message"] == "An account with this email already exists. Please sign in."

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post("/auth/register", json={"email": "short@medlens.dev", "password": "123"})
        assert resp.status_code == 422

    async def test_login(self, client: AsyncClient):
        await client.post("/auth/register", json={"email": "login@medlens.dev", "password": "securepass123"})
        resp = await client.post("/auth/login", json={"email": "login@medlens.dev", "password": "securepass123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/auth/register", json={"email": "wrong@medlens.dev", "password": "securepass123"})
        resp = await client.post("/auth/login", json={"email": "wrong@medlens.dev", "password": "wrongpassword"})
        assert resp.status_code == 401
        assert resp.json()["error"]["message"] == "Incorrect password. Please try again."

    async def test_login_unregistered_email(self, client: AsyncClient):
        resp = await client.post("/auth/login", json={"email": "nonexistent@medlens.dev", "password": "securepass123"})
        assert resp.status_code == 401
        assert resp.json()["error"]["message"] == "No account found with this email. Please register first."

    async def test_login_invalid_email_format(self, client: AsyncClient):
        resp = await client.post("/auth/login", json={"email": "invalid-email-format", "password": "securepass123"})
        assert resp.status_code == 422
        assert resp.json()["error"]["message"] == "Please enter a valid email address."

    async def test_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_me_authenticated(self, auth_client: AsyncClient):
        resp = await auth_client.get("/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@medlens.dev"


@pytest.mark.asyncio
class TestPatients:
    async def test_create_patient(self, auth_client: AsyncClient):
        resp = await auth_client.post("/patients", json={
            "name": "Test Patient",
            "age": 42,
            "sex": "MALE",
        })
        assert resp.status_code == 201
        assert resp.json()["name"] == "Test Patient"

    async def test_list_patients(self, auth_client: AsyncClient):
        await auth_client.post("/patients", json={"name": "P1"})
        resp = await auth_client.get("/patients")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_patient(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/patients", json={"name": "Get Test"})
        pid = create_resp.json()["id"]
        resp = await auth_client.get(f"/patients/{pid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Test"

    async def test_update_patient(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/patients", json={"name": "Before"})
        pid = create_resp.json()["id"]
        resp = await auth_client.patch(f"/patients/{pid}", json={"name": "After"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "After"

    async def test_delete_patient(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/patients", json={"name": "Delete Me"})
        pid = create_resp.json()["id"]
        resp = await auth_client.delete(f"/patients/{pid}")
        assert resp.status_code == 204

    async def test_patient_not_found(self, auth_client: AsyncClient):
        resp = await auth_client.get("/patients/99999")
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestAuthorization:
    async def test_cross_user_patient_access(self, client: AsyncClient):
        """User A must NOT access User B's patient."""
        # Create User A
        resp_a = await client.post("/auth/register", json={"email": "usera@medlens.dev", "password": "password123"})
        token_a = resp_a.json()["access_token"]

        # Create User B
        resp_b = await client.post("/auth/register", json={"email": "userb@medlens.dev", "password": "password123"})
        token_b = resp_b.json()["access_token"]

        # User A creates patient
        create_resp = await client.post(
            "/patients",
            json={"name": "A's Patient"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        patient_id = create_resp.json()["id"]

        # User B tries to access User A's patient
        resp = await client.get(
            f"/patients/{patient_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 403

    async def test_unauthenticated_patient_access(self, client: AsyncClient):
        resp = await client.get("/patients")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestIntake:
    async def test_save_intake(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/patients", json={"name": "Intake Test"})
        pid = create_resp.json()["id"]
        resp = await auth_client.post(f"/patients/{pid}/intake", json={
            "symptoms": "Fatigue, weakness",
            "existing_conditions": "Type 2 Diabetes",
            "allergies": "No known allergies",
            "medications": "Metformin 500mg",
            "notes": "Regular checkup",
        })
        assert resp.status_code == 200
        assert resp.json()["symptoms"] == "Fatigue, weakness"

    async def test_get_intake(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/patients", json={"name": "Intake Get"})
        pid = create_resp.json()["id"]
        await auth_client.post(f"/patients/{pid}/intake", json={"symptoms": "Headache"})
        resp = await auth_client.get(f"/patients/{pid}/intake")
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestHealth:
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
class TestReportPaste:
    async def test_paste_report(self, auth_client: AsyncClient):
        create_resp = await auth_client.post("/patients", json={"name": "Report Test"})
        pid = create_resp.json()["id"]
        resp = await auth_client.post(f"/patients/{pid}/reports/paste", json={
            "text": "Hemoglobin 10.2 g/dL Reference: 13-17 g/dL\nWBC 7400 /cumm 4000-11000",
            "report_date": "2026-08-28",
            "source_name": "Test Lab",
        })
        assert resp.status_code == 201
        assert resp.json()["processing_status"] == "UPLOADED"


@pytest.mark.asyncio
class TestDashboard:
    async def test_dashboard_stats(self, auth_client: AsyncClient):
        resp = await auth_client.get("/dashboard/stats")
        assert resp.status_code == 200
        assert "total_patients" in resp.json()
