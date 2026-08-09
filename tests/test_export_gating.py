"""
Unit, Security, and Real Integration Tests for AIForge Centralized Export Gate (Phase 11)
"""

import io
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.execution.models import ExportValidationResult, ExportResult
from backend.exporter.gate import ExportGate, global_export_gate
from backend.exporter.zipper import global_project_zipper

client = TestClient(app)


@pytest.fixture
def valid_project_dir(tmp_path):
    proj_dir = tmp_path / "generated_projects" / "GoodTodoApp"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "backend").mkdir(parents=True, exist_ok=True)
    (proj_dir / "backend" / "main.py").write_text("def app(): pass", encoding="utf-8")
    return proj_dir


@pytest.fixture
def valid_state(valid_project_dir):
    return {
        "project_name": "GoodTodoApp",
        "project_path": str(valid_project_dir),
        "files": {
            "backend/main.py": "def app(): pass",
            "frontend/App.jsx": "export default function App() {}"
        },
        "status": "PASS",
        "execution_results": {"exit_code": 0, "status": "PASS"},
        "test_results": {"success": True, "failed": 0, "passed": 5}
    }


def test_export_gate_allows_verified_project(valid_state):
    gate = ExportGate()
    gate.mark_verified(valid_state)
    res = gate.validate_state(valid_state)
    assert res.allowed is True
    assert "passed cleanly" in res.reason
    assert res.checks["execution_passed"] is True
    assert res.checks["testing_passed"] is True
    assert res.checks["status_is_pass"] is True


def test_export_gate_denies_failed_project(valid_state):
    gate = ExportGate()
    valid_state["execution_results"]["status"] = "FAIL"
    valid_state["execution_results"]["exit_code"] = 1
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "Execution evidence missing or failed" in res.reason


def test_export_gate_denies_missing_execution_result(valid_state):
    gate = ExportGate()
    valid_state["execution_results"] = {}
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "Execution evidence missing or failed" in res.reason


def test_export_gate_denies_failed_tests(valid_state):
    gate = ExportGate()
    valid_state["test_results"] = {"success": False, "failed": 2, "passed": 3}
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "Testing evidence missing or failed" in res.reason


def test_export_gate_denies_failed_max_iterations(valid_state):
    gate = ExportGate()
    valid_state["status"] = "FAILED_MAX_ITERATIONS"
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "unresolved failure status" in res.reason


def test_export_gate_denies_unsupported(valid_state):
    gate = ExportGate()
    valid_state["status"] = "UNSUPPORTED"
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "unresolved failure status" in res.reason


def test_export_gate_denies_security_error(valid_state):
    gate = ExportGate()
    valid_state["status"] = "SECURITY_ERROR"
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "unresolved failure status" in res.reason


def test_export_gate_denies_missing_project_directory(valid_state, tmp_path):
    gate = ExportGate()
    valid_state["project_path"] = str(tmp_path / "non_existent_dir_9999")
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "Invalid or missing project directory path" in res.reason


def test_export_gate_denies_empty_project(valid_state):
    gate = ExportGate()
    valid_state["files"] = {}
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "Project has no files" in res.reason


def test_export_gate_rejects_traversal_paths(valid_state):
    gate = ExportGate()
    valid_state["files"]["../../outside.txt"] = "malicious payload"
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "invalid path traversal" in res.reason


def test_export_gate_rejects_absolute_paths(valid_state):
    gate = ExportGate()
    valid_state["files"]["/etc/passwd"] = "root:x:0:0"
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "invalid path traversal" in res.reason


def test_zip_contains_expected_verified_files(valid_state):
    gate = ExportGate()
    gate.mark_verified(valid_state)
    res = gate.validate_state(valid_state)
    assert res.allowed is True

    zip_bytes = global_project_zipper.create_zip_bytes(valid_state["files"], root_folder="GoodTodoApp")
    assert len(zip_bytes) > 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        namelist = zf.namelist()
        assert "GoodTodoApp/backend/main.py" in namelist
        assert "GoodTodoApp/frontend/App.jsx" in namelist


def test_zip_export_cannot_bypass_gate(valid_state):
    valid_state["status"] = "FAILED_MAX_ITERATIONS"
    resp = client.post("/api/export/zip", json={
        "project_id": "GoodTodoApp",
        "files": valid_state["files"],
        "state": valid_state
    })
    assert resp.status_code == 403
    assert "Export Denied" in resp.json()["detail"]


def test_github_export_cannot_bypass_gate(valid_state):
    valid_state["execution_results"]["status"] = "FAIL"
    resp = client.post("/api/export/github", json={
        "project_id": "GoodTodoApp",
        "files": valid_state["files"],
        "state": valid_state
    })
    assert resp.status_code == 403
    assert "Export Denied" in resp.json()["detail"]


def test_stale_verification_is_rejected(valid_state):
    gate = ExportGate()
    gate.mark_verified(valid_state)
    
    # Verify initial state passes
    assert gate.validate_state(valid_state).allowed is True

    # Modify file after verification
    valid_state["files"]["backend/main.py"] = "def app(): print('unverified change')"
    
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "modified after verification passed" in res.reason


def test_modified_after_verification_project_is_rejected(valid_state):
    gate = ExportGate()
    gate.mark_verified(valid_state)
    
    # Add a new unverified file
    valid_state["files"]["backend/unverified_route.py"] = "def backdoor(): pass"
    
    res = gate.validate_state(valid_state)
    assert res.allowed is False
    assert "modified after verification passed" in res.reason


def test_good_todo_app_complete_export_succeeds(valid_state):
    gate = ExportGate()
    gate.mark_verified(valid_state)
    
    val = gate.validate_state(valid_state)
    assert val.allowed is True

    resp = client.post("/api/export/zip", json={
        "project_id": "GoodTodoApp",
        "files": valid_state["files"],
        "state": valid_state
    })
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"


def test_bad_todo_app_export_is_denied(valid_state):
    valid_state["project_name"] = "BadTodoApp"
    valid_state["execution_results"] = {"exit_code": 1, "status": "FAIL"}
    valid_state["test_results"] = {"success": False, "failed": 3}
    valid_state["status"] = "FAILED"

    resp = client.post("/api/export/zip", json={
        "project_id": "BadTodoApp",
        "files": valid_state["files"],
        "state": valid_state
    })
    assert resp.status_code == 403
    assert "Export Denied" in resp.json()["detail"]
