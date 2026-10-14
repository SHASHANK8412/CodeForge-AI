"""
AIForge AI Code Workspace Test Suite
====================================
Validates all IDE workspace REST endpoints, file operations, security sandboxing,
AI Code Actions, Diff Generation, Problems panel, Changes tracking, and Test execution.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.quality.version_manager import global_version_manager
from backend.memory.codebase_indexer import global_codebase_indexer


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_workspace_project():
    project_id = "test_workspace_proj"
    files = {
        "backend/main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/api/health')\ndef health():\n    return {'status': 'healthy'}\n",
        "backend/routes/auth.py": "from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.post('/login')\ndef login():\n    return {'token': 'jwt_secret_token'}\n",
        "frontend/src/App.jsx": "import React from 'react';\n\nexport default function App() {\n    return <div>Hello AIForge</div>;\n}\n",
        "database/schema.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50));\n",
        "tests/test_auth.py": "def test_auth_dummy():\n    assert True\n"
    }
    # Create base version snapshot
    global_version_manager.create_snapshot(
        project_id=project_id,
        files_map=files,
        repair_reason="Initial workspace test snapshot"
    )
    # Index files
    global_codebase_indexer.index_project_files(project_id, files)
    return project_id, files


# ---------------------------------------------------------------------------
# 1. File Listing & Tree API Tests
# ---------------------------------------------------------------------------

def test_workspace_files_listing(client, sample_workspace_project):
    project_id, files = sample_workspace_project
    resp = client.get(f"/api/project/{project_id}/files")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == project_id
    assert len(data["files"]) >= len(files)
    
    paths = [f["path"] for f in data["files"]]
    assert "backend/main.py" in paths
    assert "frontend/src/App.jsx" in paths
    assert "database/schema.sql" in paths


def test_workspace_get_single_file(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    resp = client.get(f"/api/project/{project_id}/file?path=backend/main.py")
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == "backend/main.py"
    assert "from fastapi import FastAPI" in data["content"]
    assert data["language"] == "python"
    assert "hash" in data


# ---------------------------------------------------------------------------
# 2. Security Sandbox & Path Traversal Protection
# ---------------------------------------------------------------------------

def test_workspace_security_rejects_directory_traversal(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    
    # Path traversal with ../
    resp = client.get(f"/api/project/{project_id}/file?path=../../etc/passwd")
    assert resp.status_code in (400, 404)

    # Absolute path access
    resp2 = client.get(f"/api/project/{project_id}/file?path=/etc/shadow")
    assert resp2.status_code in (400, 404)

    # Secret files (.env)
    resp3 = client.get(f"/api/project/{project_id}/file?path=.env")
    assert resp3.status_code in (400, 404)


# ---------------------------------------------------------------------------
# 3. File Saving, Incremental Indexing & Version Snapshots
# ---------------------------------------------------------------------------

def test_workspace_save_file_updates_index_and_snapshot(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    new_content = "from fastapi import FastAPI\n\napp = FastAPI(title='Updated API')\n\n@app.get('/api/health')\ndef health():\n    return {'status': 'ok'}\n"
    
    save_resp = client.put(f"/api/project/{project_id}/file", json={
        "path": "backend/main.py",
        "content": new_content
    })
    assert save_resp.status_code == 200
    save_data = save_resp.json()
    assert save_data["status"] == "SUCCESS"
    assert save_data["path"] == "backend/main.py"
    assert "file_hash" in save_data

    # Verify retrieval returns updated content
    get_resp = client.get(f"/api/project/{project_id}/file?path=backend/main.py")
    assert get_resp.status_code == 200
    assert "Updated API" in get_resp.json()["content"]

    # Verify history snapshot incremented
    history = global_version_manager.get_history(project_id)
    assert len(history) >= 2
    assert "backend/main.py" in history[-1].changed_files


# ---------------------------------------------------------------------------
# 4. AI Code Actions & Explain / Refactor / Tests
# ---------------------------------------------------------------------------

def test_workspace_ai_code_actions(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    
    # 1. Explain action
    resp_explain = client.post(f"/api/project/{project_id}/ai-action", json={
        "path": "backend/main.py",
        "selected_code": "def health():\n    return {'status': 'healthy'}",
        "action": "explain"
    })
    assert resp_explain.status_code == 200
    data_explain = resp_explain.json()
    assert data_explain["status"] == "SUCCESS"
    assert "result" in data_explain
    assert len(data_explain["result"]) > 0

    # 2. Generate tests action
    resp_tests = client.post(f"/api/project/{project_id}/ai-action", json={
        "path": "backend/routes/auth.py",
        "selected_code": "def login():\n    return {'token': 'jwt_secret_token'}",
        "action": "tests"
    })
    assert resp_tests.status_code == 200
    data_tests = resp_tests.json()
    assert data_tests["status"] == "SUCCESS"
    assert "test" in data_tests["result"].lower() or "def test" in data_tests["result"]

    # 3. Refactor action
    resp_refactor = client.post(f"/api/project/{project_id}/ai-action", json={
        "path": "backend/routes/auth.py",
        "selected_code": "def login():\n    return {'token': 'jwt_secret_token'}",
        "action": "refactor"
    })
    assert resp_refactor.status_code == 200
    assert resp_refactor.json()["status"] == "SUCCESS"


# ---------------------------------------------------------------------------
# 5. Unified Diff Generation API
# ---------------------------------------------------------------------------

def test_workspace_diff_generation(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    orig = "def fetch_data():\n    return 42\n"
    mod = "async def fetch_data():\n    return 42\n"

    resp = client.post(f"/api/project/{project_id}/diff", json={
        "path": "services/api.py",
        "original_content": orig,
        "modified_content": mod
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert "diff" in data
    assert "-def fetch_data" in data["diff"]
    assert "+async def fetch_data" in data["diff"]
    assert data["lines_added"] >= 1
    assert data["lines_removed"] >= 1


# ---------------------------------------------------------------------------
# 6. Test Runner, Problems, Changes & Timeline APIs
# ---------------------------------------------------------------------------

def test_workspace_test_runner_endpoint(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    resp = client.post(f"/api/project/{project_id}/test")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("PASS", "FAIL")
    assert data["total"] > 0
    assert "passed" in data
    assert "output" in data


def test_workspace_problems_endpoint(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    resp = client.get(f"/api/project/{project_id}/problems")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_problems" in data
    assert isinstance(data["problems"], list)


def test_workspace_changes_endpoint(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    # After saving a file earlier, changes should record the modified file
    resp = client.get(f"/api/project/{project_id}/changes")
    assert resp.status_code == 200
    data = resp.json()
    assert "changes" in data
    assert isinstance(data["changes"], list)


def test_workspace_timeline_endpoint(client, sample_workspace_project):
    project_id, _ = sample_workspace_project
    resp = client.get(f"/api/project/{project_id}/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert len(data["events"]) > 0
