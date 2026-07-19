import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def test_client():
    from backend.main import app
    client = TestClient(app)
    yield client

def test_read_tasks(test_client):
    token = 'your-generated-token'
    headers = {'Authorization': f'Bearer {token}'}
    response = test_client.get("/tasks", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_create_task(test_client):
    token = 'your-generated-token'
    headers = {'Authorization': f'Bearer {token}'}
    response = test_client.post("/tasks", json={"title": "Test Task", "category": "personal"}, headers=headers)
    assert response.status_code == 201

def test_update_task(test_client):
    token = 'your-generated-token'
    headers = {'Authorization': f'Bearer {token}'}
    task_id = 1
    response = test_client.put(f"/tasks/{task_id}", json={"title": "Updated Test Task"}, headers=headers)
    assert response.status_code == 200

def test_delete_task(test_client):
    token = 'your-generated-token'
    headers = {'Authorization': f'Bearer {token}'}
    task_id = 1
    response = test_client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200