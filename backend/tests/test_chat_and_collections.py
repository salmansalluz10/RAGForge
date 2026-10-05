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


def get_auth_token(email: str = "chat_user@example.com") -> tuple[str, str]:
    res = client.post("/api/v1/auth/register", json={
        "name": "Chat Tester",
        "email": email,
        "password": "Password123!",
    })
    data = res.json()
    return data["access_token"], data["user"]["id"]


def test_collection_lifecycle_and_document_linking():
    token, user_id = get_auth_token("col_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create collection
    res_col = client.post("/api/v1/collections", headers=headers, json={
        "name": "Financial Reports",
        "description": "Annual 10-K and quarterly earnings filings",
    })
    assert res_col.status_code == 201
    col_id = res_col.json()["id"]
    assert res_col.json()["name"] == "Financial Reports"

    # 2. Upload document
    files = {"file": ("report_q1.txt", io.BytesIO(b"Revenue was $10M."), "text/plain")}
    res_doc = client.post("/api/v1/documents/upload", headers=headers, files=files)
    doc_id = res_doc.json()["id"]

    # 3. Add document to collection
    res_link = client.post(f"/api/v1/collections/{col_id}/documents", headers=headers, json={
        "document_id": doc_id,
    })
    assert res_link.status_code == 200
    assert res_link.json()["collection_id"] == col_id

    # 4. List collections -> count should be 1
    res_list = client.get("/api/v1/collections", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 1
    assert res_list.json()["items"][0]["document_count"] == 1

    # 5. Remove document from collection
    res_unlink = client.delete(f"/api/v1/collections/{col_id}/documents/{doc_id}", headers=headers)
    assert res_unlink.status_code == 200
    assert res_unlink.json()["collection_id"] is None

    # 6. Delete collection
    res_del = client.delete(f"/api/v1/collections/{col_id}", headers=headers)
    assert res_del.status_code == 204


def test_chat_conversations_and_rag_messages():
    token, user_id = get_auth_token("chat_rag_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload & process document
    doc_text = "Acme Corp was founded in 2015 by Alice and Bob in Seattle."
    files = {"file": ("acme_history.txt", io.BytesIO(doc_text.encode("utf-8")), "text/plain")}
    res_up = client.post("/api/v1/documents/upload", headers=headers, files=files)
    doc_id = res_up.json()["id"]
    client.post(f"/api/v1/documents/{doc_id}/process", headers=headers)

    # 1. Create conversation
    res_conv = client.post("/api/v1/conversations", headers=headers, json={
        "title": "New Conversation",
    })
    assert res_conv.status_code == 201
    conv_id = res_conv.json()["id"]

    # 2. Send message
    res_msg = client.post(f"/api/v1/conversations/{conv_id}/messages", headers=headers, json={
        "content": "Where was Acme Corp founded?",
    })
    assert res_msg.status_code == 201
    msg_data = res_msg.json()
    assert msg_data["role"] == "assistant"
    assert len(msg_data["content"]) > 0

    # 3. Get conversation details (should contain 2 messages: user & assistant)
    res_detail = client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["role"] == "user"
    assert detail["messages"][1]["role"] == "assistant"

    # 4. Rename conversation
    res_rename = client.put(f"/api/v1/conversations/{conv_id}", headers=headers, json={
        "title": "Acme Founding History",
    })
    assert res_rename.status_code == 200
    assert res_rename.json()["title"] == "Acme Founding History"

    # 5. Delete conversation
    res_del = client.delete(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert res_del.status_code == 204


def test_dashboard_stats():
    token, user_id = get_auth_token("dashboard_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload a doc and create a collection
    files = {"file": ("dashboard_doc.txt", io.BytesIO(b"Sample data"), "text/plain")}
    client.post("/api/v1/documents/upload", headers=headers, files=files)
    client.post("/api/v1/collections", headers=headers, json={"name": "Dash Collection"})
    client.post("/api/v1/conversations", headers=headers, json={"title": "Dash Conversation"})

    res_stats = client.get("/api/v1/dashboard/stats", headers=headers)
    assert res_stats.status_code == 200
    data = res_stats.json()
    assert data["total_documents"] >= 1
    assert data["total_collections"] >= 1
    assert data["total_conversations"] >= 1
    assert "status_counts" in data
    assert len(data["recent_documents"]) >= 1
    assert len(data["recent_conversations"]) >= 1


def test_user_isolation_chat_and_collections():
    token_a, id_a = get_auth_token("owner_isolation@example.com")
    token_b, id_b = get_auth_token("intruder_isolation@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates collection and conversation
    res_col_a = client.post("/api/v1/collections", headers=headers_a, json={"name": "Confidential Col A"})
    col_id_a = res_col_a.json()["id"]

    res_conv_a = client.post("/api/v1/conversations", headers=headers_a, json={"title": "Secret Conv A"})
    conv_id_a = res_conv_a.json()["id"]

    # User B cannot access User A's collection
    res_col_b = client.get(f"/api/v1/collections/{col_id_a}", headers=headers_b)
    assert res_col_b.status_code == 404

    res_col_del_b = client.delete(f"/api/v1/collections/{col_id_a}", headers=headers_b)
    assert res_col_del_b.status_code == 404

    # User B cannot access or message User A's conversation
    res_conv_b = client.get(f"/api/v1/conversations/{conv_id_a}", headers=headers_b)
    assert res_conv_b.status_code == 404

    res_msg_b = client.post(f"/api/v1/conversations/{conv_id_a}/messages", headers=headers_b, json={"content": "Spy message"})
    assert res_msg_b.status_code == 404
