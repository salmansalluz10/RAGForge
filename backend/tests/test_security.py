import io
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine
from app.core.config import settings
from app.utils.file_utils import sanitize_filename, get_storage_path

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_auth_token(email: str = "security_tester@example.com") -> tuple[str, str]:
    res = client.post("/api/v1/auth/register", json={
        "name": "Sec Tester",
        "email": email,
        "password": "Password123!",
    })
    data = res.json()
    return data["access_token"], data["user"]["id"]


def test_security_headers_present():
    """Verify security headers (X-Content-Type-Options, X-Frame-Options) on API responses."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_sql_injection_resilience():
    """Verify parameterized queries prevent SQL injection."""
    token, _ = get_auth_token("sqli_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Malicious SQL payloads in search, title, and query
    payloads = [
        "' OR 1=1 --",
        "'; DROP TABLE users; --",
        "' UNION SELECT id, password_hash, email FROM users --",
    ]

    for p in payloads:
        # Search query
        res_search = client.post("/api/v1/search", headers=headers, json={"query": p})
        assert res_search.status_code == 200

        # Document list search
        res_docs = client.get(f"/api/v1/documents?search={p}", headers=headers)
        assert res_docs.status_code == 200

        # Collection creation
        res_col = client.post("/api/v1/collections", headers=headers, json={"name": p})
        assert res_col.status_code == 201


def test_path_traversal_sanitization():
    """Verify path traversal characters in uploaded filenames are safely stripped."""
    dangerous_names = [
        "../../../../etc/passwd.txt",
        "..\\..\\Windows\\System32\\cmd.exe.txt",
        "nested/sub/path/notes.txt",
    ]

    for raw_name in dangerous_names:
        clean = sanitize_filename(raw_name)
        assert "/" not in clean
        assert "\\" not in clean
        assert ".." not in clean


def test_invalid_and_expired_jwt():
    """Verify invalid, expired, and tampered JWT tokens are strictly rejected."""
    # 1. Tampered signature
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NSJ9.invalid_signature_xxx"
    res1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res1.status_code == 401

    # 2. Expired token
    expired_payload = {
        "sub": "user_id_123",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    res2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res2.status_code == 401

    # 3. Missing bearer prefix
    res3 = client.get("/api/v1/auth/me", headers={"Authorization": "Basic 12345"})
    assert res3.status_code == 401


def test_all_protected_endpoints_require_authentication():
    """Ensure all protected endpoints return 401 when accessed without authorization."""
    protected_endpoints = [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/documents"),
        ("POST", "/api/v1/documents/upload"),
        ("GET", "/api/v1/collections"),
        ("POST", "/api/v1/collections"),
        ("GET", "/api/v1/conversations"),
        ("POST", "/api/v1/conversations"),
        ("POST", "/api/v1/search"),
        ("POST", "/api/v1/rag/query"),
        ("GET", "/api/v1/dashboard/stats"),
    ]

    for method, path in protected_endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path)
        assert res.status_code in [401, 403], f"Endpoint {method} {path} should be protected"


def test_strict_cross_user_isolation():
    """Confirm user cannot read, update, or delete any resource of another user."""
    token_victim, victim_id = get_auth_token("victim@example.com")
    token_attacker, attacker_id = get_auth_token("attacker@example.com")

    h_victim = {"Authorization": f"Bearer {token_victim}"}
    h_attacker = {"Authorization": f"Bearer {token_attacker}"}

    # Victim creates resources
    files = {"file": ("private_notes.txt", io.BytesIO(b"Victim private data"), "text/plain")}
    res_doc = client.post("/api/v1/documents/upload", headers=h_victim, files=files)
    doc_id = res_doc.json()["id"]

    res_col = client.post("/api/v1/collections", headers=h_victim, json={"name": "Victim Col"})
    col_id = res_col.json()["id"]

    res_conv = client.post("/api/v1/conversations", headers=h_victim, json={"title": "Victim Chat"})
    conv_id = res_conv.json()["id"]

    # Attacker attempts to read victim's resources -> 404
    assert client.get(f"/api/v1/documents/{doc_id}", headers=h_attacker).status_code == 404
    assert client.get(f"/api/v1/collections/{col_id}", headers=h_attacker).status_code == 404
    assert client.get(f"/api/v1/conversations/{conv_id}", headers=h_attacker).status_code == 404

    # Attacker attempts to modify victim's resources -> 404
    assert client.put(f"/api/v1/collections/{col_id}", headers=h_attacker, json={"name": "Hacked"}).status_code == 404
    assert client.put(f"/api/v1/conversations/{conv_id}", headers=h_attacker, json={"title": "Hacked"}).status_code == 404
    assert client.post(f"/api/v1/conversations/{conv_id}/messages", headers=h_attacker, json={"content": "Hacked"}).status_code == 404

    # Attacker attempts to delete victim's resources -> 404
    assert client.delete(f"/api/v1/documents/{doc_id}", headers=h_attacker).status_code == 404
    assert client.delete(f"/api/v1/collections/{col_id}", headers=h_attacker).status_code == 404
    assert client.delete(f"/api/v1/conversations/{conv_id}", headers=h_attacker).status_code == 404


def test_safe_error_responses_no_stack_traces():
    """Verify error responses never return raw internal stack traces."""
    # Invalid document ID
    res = client.get("/api/v1/documents/nonexistent-id", headers={"Authorization": "Bearer bad-token"})
    assert res.status_code == 401
    data = res.json()
    assert "detail" in data
    assert "Traceback" not in str(data)
    assert "sqlalchemy" not in str(data).lower()
