import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def test_client():
    from backend.main import app
    client = TestClient(app)
    yield client

def test_login(test_client):
    response = test_client.post("/auth/login", json={"email": "johndoe@example.com", "password": "password"})
    assert response.status_code == 200
    assert 'token' in response.json()

def test_invalid_login(test_client):
    response = test_client.post("/auth/login", json={"email": "invaliduser@example.com", "password": "wrongpassword"})
    assert response.status_code == 401

def test_missing_fields_login(test_client):
    response = test_client.post("/auth/login", json={})
    assert response.status_code == 422