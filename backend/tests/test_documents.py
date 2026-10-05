import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine
from app.utils.file_utils import get_storage_path

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_auth_token(email: str, name: str = "Test User") -> str:
    res = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": "Password123!",
    })
    return res.json()["access_token"]


def test_upload_valid_txt_document():
    token = get_auth_token("user_upload@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    file_content = b"This is a test document content for RAGForge indexing."
    files = {"file": ("sample_notes.txt", io.BytesIO(file_content), "text/plain")}

    response = client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "sample_notes.txt"
    assert data["file_type"] == "txt"
    assert data["file_size"] == len(file_content)
    assert data["processing_status"] == "UPLOADED"

    # Verify physical file existence
    stored_path = get_storage_path(data["stored_filename"])
    assert stored_path.exists()
    assert stored_path.read_bytes() == file_content


def test_reject_unsupported_file_extension():
    token = get_auth_token("user_reject@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("malicious.exe", io.BytesIO(b"MZ..."), "application/octet-stream")}
    response = client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_list_and_user_isolation():
    token_a = get_auth_token("user_a@example.com")
    token_b = get_auth_token("user_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads a doc
    files = {"file": ("user_a_private.txt", io.BytesIO(b"Confidential user A data"), "text/plain")}
    res_upload = client.post("/api/v1/documents/upload", headers=headers_a, files=files)
    doc_id_a = res_upload.json()["id"]

    # User A lists -> should see 1 doc
    list_a = client.get("/api/v1/documents", headers=headers_a)
    assert list_a.status_code == 200
    assert list_a.json()["total"] >= 1

    # User B lists -> should NOT see User A's doc
    list_b = client.get("/api/v1/documents", headers=headers_b)
    assert list_b.status_code == 200
    user_b_doc_ids = [d["id"] for d in list_b.json()["items"]]
    assert doc_id_a not in user_b_doc_ids

    # User B cannot access doc A
    get_unauthorized = client.get(f"/api/v1/documents/{doc_id_a}", headers=headers_b)
    assert get_unauthorized.status_code == 404

    # User B cannot delete doc A
    del_unauthorized = client.delete(f"/api/v1/documents/{doc_id_a}", headers=headers_b)
    assert del_unauthorized.status_code == 404


def test_delete_document_and_file():
    token = get_auth_token("user_del@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("to_delete.txt", io.BytesIO(b"Temporary file content"), "text/plain")}
    res = client.post("/api/v1/documents/upload", headers=headers, files=files)
    doc = res.json()
    doc_id = doc["id"]
    stored_path = get_storage_path(doc["stored_filename"])
    assert stored_path.exists()

    # Delete doc
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 204

    # Confirm physical file deleted
    assert not stored_path.exists()

    # Confirm record gone
    get_res = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 404
