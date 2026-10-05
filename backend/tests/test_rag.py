import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_auth_token(email: str = "rag_user@example.com") -> tuple[str, str]:
    res = client.post("/api/v1/auth/register", json={
        "name": "RAG Tester",
        "email": email,
        "password": "Password123!",
    })
    data = res.json()
    return data["access_token"], data["user"]["id"]


def test_rag_query_with_matching_document():
    token, user_id = get_auth_token("rag_match@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload document
    doc_content = (
        "Project Titan was initiated in March 2023 with an initial budget of 15 million dollars.\n\n"
        "The primary objective is to migrate all on-premise document storage to a high-availability cloud architecture.\n\n"
        "The lead architect responsible for the migration is Dr. Sarah Jenkins."
    )
    files = {"file": ("titan_charter.txt", io.BytesIO(doc_content.encode("utf-8")), "text/plain")}
    res_up = client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert res_up.status_code == 201
    doc_id = res_up.json()["id"]

    # Process document
    res_proc = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert res_proc.status_code == 200

    # Execute RAG Query
    res_rag = client.post("/api/v1/rag/query", headers=headers, json={
        "question": "Who is the lead architect for Project Titan?",
        "threshold": -1.0,
    })
    assert res_rag.status_code == 200
    data = res_rag.json()

    assert data["question"] == "Who is the lead architect for Project Titan?"
    assert len(data["answer"]) > 0
    assert data["chunks_retrieved"] >= 1
    assert len(data["sources"]) >= 1

    # Verify source citations structure
    source = data["sources"][0]
    assert source["document_id"] == doc_id
    assert source["document_name"] == "titan_charter.txt"
    assert "snippet" in source
    assert isinstance(source["score"], float)


def test_rag_query_when_no_context_found():
    token, user_id = get_auth_token("rag_empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # User with no documents asks a question
    res_rag = client.post("/api/v1/rag/query", headers=headers, json={
        "question": "What is the secret launch date of Project Alpha?",
    })
    assert res_rag.status_code == 200
    data = res_rag.json()

    assert "could not find enough information" in data["answer"].lower()
    assert data["chunks_retrieved"] == 0
    assert len(data["sources"]) == 0


def test_rag_user_isolation():
    token_a, user_id_a = get_auth_token("rag_owner_a@example.com")
    token_b, user_id_b = get_auth_token("rag_intruder_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads sensitive document
    secret_text = "The internal encryption key for database backups is XK9-772-OMEGA."
    files = {"file": ("keys.txt", io.BytesIO(secret_text.encode("utf-8")), "text/plain")}
    res_up = client.post("/api/v1/documents/upload", headers=headers_a, files=files)
    doc_id = res_up.json()["id"]
    client.post(f"/api/v1/documents/{doc_id}/process", headers=headers_a)

    # User B queries about User A's secret key
    res_rag_b = client.post("/api/v1/rag/query", headers=headers_b, json={
        "question": "What is the encryption key for database backups?",
        "threshold": -1.0,
    })
    assert res_rag_b.status_code == 200
    data_b = res_rag_b.json()

    # User B MUST NOT get User A's data or sources
    assert "could not find enough information" in data_b["answer"].lower()
    assert data_b["chunks_retrieved"] == 0
    assert len(data_b["sources"]) == 0
    assert "XK9-772-OMEGA" not in data_b["answer"]
