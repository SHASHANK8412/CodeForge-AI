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

def test_signup(test_client):
    response = test_client.post("/auth/signup", json={"email": "janedoe@example.com", "password": "password123"})
    assert response.status_code == 200

def test_todo_list(test_client):
    # Assuming a user is logged in and has tasks
    token = 'your-generated-token'
    headers = {'Authorization': f'Bearer {token}'}
    response = test_client.get("/todo", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_todo_create(test_client):
    # Assuming a user is logged in and has tasks
    token = 'your-generated-token'
    headers = {'Authorization': f'Bearer {token}'}
    response = test_client.post("/todo", json={"title": "Test Task", "category": "personal"}, headers=headers)
    assert response.status_code == 201

def test_todo_update(test_client):
    # Assuming a user is logged in and has tasks
    token = 'your-generated-token'
    headers = {'Authorization': f'Bearer {token}'}
    task_id = 1
    response = test_client.put(f"/todo/{task_id}", json={"title": "Updated Test Task"}, headers=headers)
    assert response.status_code == 200

def test_todo_delete(test_client):
    # Assuming a user is logged in and has tasks
    token = 'your-generated-token'
    headers = {'Authorization': f'Bearer {token}'}
    task_id = 1
    response = test_client.delete(f"/todo/{task_id}", headers=headers)
    assert response.status_code == 200