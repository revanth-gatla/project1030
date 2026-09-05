"""Live verification of the 9 required auth test cases against http://127.0.0.1:8001."""

import json
import urllib.error
import urllib.request
import uuid

BASE_URL = "http://127.0.0.1:8001"


def req(method: str, path: str, data: dict = None, token: str = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as resp:
            status = resp.status
            content = json.loads(resp.read().decode("utf-8"))
            return status, content
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            content = json.loads(e.read().decode("utf-8"))
        except Exception:
            content = {"raw": str(e)}
        return status, content


def run_tests():
    print("=== Running 9 Required Live Verification Cases ===")

    test_id = str(uuid.uuid4())[:8]
    test_email = f"clinician_{test_id}@hospital.org"
    test_password = "SecurePassword123!"
    unregistered_email = f"unregistered_{test_id}@hospital.org"

    # Case 1: Unregistered email
    status, body = req("POST", "/auth/login", {"email": unregistered_email, "password": test_password})
    assert status == 401, f"Expected 401, got {status}: {body}"
    msg = body.get("error", {}).get("message")
    assert msg == "No account found with this email. Please register first.", f"Unexpected msg: {msg}"
    print("[PASS] Case 1: Unregistered email correctly returns 401 and 'No account found with this email. Please register first.'")

    # Case 5: New user registration (do this before Case 2 so user exists)
    status, body = req("POST", "/auth/register", {"email": test_email, "password": test_password})
    assert status == 201, f"Expected 201, got {status}: {body}"
    token_1 = body.get("access_token")
    assert token_1, "Expected access_token in registration response"
    print("[PASS] Case 5: New user registration succeeds with 201 and returns access_token.")

    # Case 2: Registered email + wrong password
    status, body = req("POST", "/auth/login", {"email": test_email, "password": "WrongPassword999!"})
    assert status == 401, f"Expected 401, got {status}: {body}"
    msg = body.get("error", {}).get("message")
    assert msg == "Incorrect password. Please try again.", f"Unexpected msg: {msg}"
    print("[PASS] Case 2: Registered email + wrong password returns 401 and 'Incorrect password. Please try again.'")

    # Case 3: Registered email + correct password
    status, body = req("POST", "/auth/login", {"email": test_email, "password": test_password})
    assert status == 200, f"Expected 200, got {status}: {body}"
    token_2 = body.get("access_token")
    assert token_2, "Expected access_token in login response"
    print("[PASS] Case 3: Registered email + correct password returns 200 and logs in successfully.")

    # Case 4: Invalid email format
    status, body = req("POST", "/auth/login", {"email": "not-a-valid-email", "password": test_password})
    assert status == 422, f"Expected 422, got {status}: {body}"
    msg = body.get("error", {}).get("message")
    assert msg == "Please enter a valid email address.", f"Unexpected msg: {msg}"
    print("[PASS] Case 4: Invalid email format returns 422 and 'Please enter a valid email address.'")

    # Case 6: Duplicate registration
    status, body = req("POST", "/auth/register", {"email": test_email, "password": test_password})
    assert status == 409, f"Expected 409, got {status}: {body}"
    msg = body.get("error", {}).get("message")
    assert msg == "An account with this email already exists. Please sign in.", f"Unexpected msg: {msg}"
    print("[PASS] Case 6: Duplicate registration returns 409 and 'An account with this email already exists. Please sign in.'")

    # Case 7: Logout and login again
    status, body = req("POST", "/auth/logout", None, token_2)
    assert status == 200, f"Expected 200, got {status}: {body}"
    # Re-login with registered credentials
    status, body = req("POST", "/auth/login", {"email": test_email, "password": test_password})
    assert status == 200, f"Expected 200, got {status}: {body}"
    new_token = body.get("access_token")
    assert new_token, "Expected valid token after re-login"
    print("[PASS] Case 7: Logout and re-login succeeds with valid session.")

    # Case 8: Protected routes remain protected
    status, body = req("GET", "/auth/me")
    assert status == 401, f"Expected 401 for unauthenticated /auth/me, got {status}: {body}"
    status, body = req("GET", "/patients")
    assert status == 401, f"Expected 401 for unauthenticated /patients, got {status}: {body}"
    # Authenticated access
    status, body = req("GET", "/auth/me", None, new_token)
    assert status == 200, f"Expected 200, got {status}: {body}"
    assert body.get("email") == test_email
    print("[PASS] Case 8: Protected routes reject unauthenticated requests with 401 and allow authenticated access.")

    # Case 9: No cross-user access
    # Register User B
    email_b = f"user_b_{test_id}@hospital.org"
    status, body = req("POST", "/auth/register", {"email": email_b, "password": test_password})
    token_b = body["access_token"]
    # User A creates a patient
    status, patient_a = req("POST", "/patients", {"name": "Patient Owned by A"}, token=new_token)
    assert status == 201, f"Expected 201, got {status}: {patient_a}"
    patient_a_id = patient_a["id"]
    # User B tries to read User A's patient
    status, body = req("GET", f"/patients/{patient_a_id}", None, token=token_b)
    assert status in (403, 404), f"Expected 403 or 404 for cross-user access, got {status}: {body}"
    print(f"[PASS] Case 9: User B cannot access User A's patient data (status code {status}).")

    print("\nALL 9 LIVE VERIFICATION CASES PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
