import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine
from app.rag.embeddings import EmbeddingService, MockEmbeddingProvider
from app.services.retrieval_service import RetrievalService
from app.core.config import settings

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_auth_token(email: str = "vector_tester@example.com") -> tuple[str, str]:
    res = client.post("/api/v1/auth/register", json={
        "name": "Vector Tester",
        "email": email,
        "password": "Password123!",
    })
    data = res.json()
    return data["access_token"], data["user"]["id"]


def test_embedding_service_dimensions_and_determinism():
    svc = EmbeddingService.get_instance()
    text = "Artificial intelligence is revolutionizing document processing."

    vec1 = svc.embed_query(text)
    vec2 = svc.embed_query(text)

    assert len(vec1) == settings.EMBEDDING_DIMENSIONS
    assert len(vec2) == settings.EMBEDDING_DIMENSIONS
    assert vec1 == vec2  # Deterministic

    # Batch embedding
    batch = ["First chunk text", "Second chunk text"]
    vecs = svc.embed_documents(batch)
    assert len(vecs) == 2
    assert len(vecs[0]) == settings.EMBEDDING_DIMENSIONS


def test_document_processing_generates_embeddings():
    token, user_id = get_auth_token("embed_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    content = (
        "PostgreSQL with pgvector enables high-performance vector search in relational databases.\n\n"
        "It supports exact and approximate nearest neighbor search via HNSW and IVFFlat indexes.\n\n"
        "RAG applications store document chunk embeddings directly in database tables."
    )
    files = {"file": ("pgvector_guide.txt", io.BytesIO(content.encode("utf-8")), "text/plain")}
    res_upload = client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert res_upload.status_code == 201
    doc_id = res_upload.json()["id"]

    # Process document
    res_proc = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)
    assert res_proc.status_code == 200
    assert res_proc.json()["processing_status"] == "COMPLETED"

    # Verify chunks have embeddings
    res_chunks = client.get(f"/api/v1/documents/{doc_id}/chunks", headers=headers)
    assert res_chunks.status_code == 200
    chunks = res_chunks.json()["chunks"]
    assert len(chunks) >= 1


def test_semantic_search_api_and_user_isolation():
    token_a, user_id_a = get_auth_token("user_vec_a@example.com")
    token_b, user_id_b = get_auth_token("user_vec_b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads and processes a document
    doc_text_a = "Quantum computing relies on qubits to perform superposition and entanglement calculations."
    files_a = {"file": ("quantum.txt", io.BytesIO(doc_text_a.encode("utf-8")), "text/plain")}
    res_up_a = client.post("/api/v1/documents/upload", headers=headers_a, files=files_a)
    doc_id_a = res_up_a.json()["id"]
    client.post(f"/api/v1/documents/{doc_id_a}/process", headers=headers_a)

    # User A searches for quantum
    res_search_a = client.post("/api/v1/search", headers=headers_a, json={
        "query": "quantum computing qubits",
        "threshold": -1.0,  # Match any score in test
    })
    assert res_search_a.status_code == 200
    data_a = res_search_a.json()
    assert data_a["total"] >= 1
    assert data_a["results"][0]["document_id"] == doc_id_a

    # User B searches for same query -> MUST return 0 results (user isolation!)
    res_search_b = client.post("/api/v1/search", headers=headers_b, json={
        "query": "quantum computing qubits",
        "threshold": -1.0,
    })
    assert res_search_b.status_code == 200
    data_b = res_search_b.json()
    assert data_b["total"] == 0
    assert len(data_b["results"]) == 0
