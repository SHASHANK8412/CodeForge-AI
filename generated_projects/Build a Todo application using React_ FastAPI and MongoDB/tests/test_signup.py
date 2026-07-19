import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def test_client():
    from backend.main import app
    client = TestClient(app)
    yield client

def test_signup(test_client):
    response = test_client.post("/auth/signup", json={"email": "janedoe@example.com", "password": "password123"})
    assert response.status_code == 200

def test_duplicate_email_signup(test_client):
    response = test_client.post("/auth/signup", json={"email": "johndoe@example.com", "password": "password123"})
    assert response.status_code == 409