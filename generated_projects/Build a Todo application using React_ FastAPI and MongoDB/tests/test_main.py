import pytest
from main import app, create_access_token

def test_login():
    response = app.post("/token", data={"username": "johndoe", "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None

def test_register():
    response = app.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "newpass"}
    )
    assert response.status_code == 200

def test_dashboard():
    token = create_access_token(data={"sub": "johndoe"})
    headers = {"Authorization": f"Bearer {token}"}
    response = app.get("/api/tasks/list", headers=headers)
    assert response.status_code == 200