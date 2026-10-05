import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_database():
    # Fresh schema for test run
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_user_registration_success():
    payload = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["name"] == "Jane Developer"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_user_registration_duplicate_email():
    payload = {
        "name": "Duplicate User",
        "email": "jane@example.com",
        "password": "AnotherPassword456!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_user_login_success():
    payload = {
        "email": "jane@example.com",
        "password": "SecurePassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane@example.com"


def test_user_login_invalid_password():
    payload = {
        "email": "jane@example.com",
        "password": "WrongPassword!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_user_login_nonexistent_email():
    payload = {
        "email": "nobody@example.com",
        "password": "SomePassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_get_current_user_authenticated():
    # Login to obtain token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "jane@example.com",
        "password": "SecurePassword123!",
    })
    token = login_res.json()["access_token"]

    # Request /me with token
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_data = res.json()
    assert user_data["email"] == "jane@example.com"
    assert user_data["name"] == "Jane Developer"


def test_get_current_user_unauthorized():
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

    res_invalid = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert res_invalid.status_code == 401
