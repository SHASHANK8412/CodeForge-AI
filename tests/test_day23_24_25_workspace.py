import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.generators.project_generator import GENERATED_PROJECTS_DIR
from backend.quality.version_manager import global_version_manager

client = TestClient(app)

@pytest.fixture
def setup_dummy_project():
    """Creates a temporary generated project structure for testing workspace APIs."""
    project_id = "test_workspace_gen_proj"
    proj_dir = GENERATED_PROJECTS_DIR / project_id
    proj_dir.mkdir(parents=True, exist_ok=True)
    
    # Write some mock code files
    (proj_dir / "backend").mkdir(exist_ok=True)
    (proj_dir / "backend/main.py").write_text("print('original python code')", encoding="utf-8")
    (proj_dir / "README.md").write_text("# Mock README", encoding="utf-8")
    
    # Initialize snapshot
    global_version_manager._history[project_id] = []
    
    yield project_id
    
    # Cleanup
    if proj_dir.exists():
        import shutil
        shutil.rmtree(proj_dir)
    if project_id in global_version_manager._history:
        del global_version_manager._history[project_id]


def test_file_save_endpoint_security(setup_dummy_project):
    project_id = setup_dummy_project
    
    # 1. Valid save
    payload = {
        "path": "backend/main.py",
        "content": "print('updated python code')"
    }
    response = client.put(f"/api/project/{project_id}/file", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "VALIDATION REQUIRED"
    
    # Verify file content written to disk
    file_path = GENERATED_PROJECTS_DIR / project_id / "backend/main.py"
    assert file_path.read_text(encoding="utf-8") == "print('updated python code')"
    
    # Verify snapshot created with change source USER
    history = global_version_manager.get_version_history(project_id)
    assert len(history) == 1
    assert history[0].change_source == "USER"
    assert history[0].repair_reason == "User edited backend/main.py"

    # 2. Path traversal block (relative path climbing)
    payload_bad = {
        "path": "../../etc/passwd",
        "content": "malicious content"
    }
    response_bad = client.put(f"/api/project/{project_id}/file", json=payload_bad)
    assert response_bad.status_code == 400
    assert "traversal" in response_bad.json()["detail"].lower()


def test_syntax_validation_on_save(setup_dummy_project):
    project_id = setup_dummy_project
    
    # Save code with syntax errors
    payload = {
        "path": "backend/main.py",
        "content": "def broken_syntax(:" # Missing argument list closing
    }
    response = client.put(f"/api/project/{project_id}/file", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["validation_errors"]) > 0
    assert "syntax error" in data["validation_errors"][0].lower()


def test_project_structured_review(setup_dummy_project):
    project_id = setup_dummy_project
    
    # Trigger review
    response = client.post(f"/api/project/{project_id}/review")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "score" in data
    assert "issues" in data
    
    # If LLM fell back, issues list might have at least one record
    for issue in data["issues"]:
        assert "severity" in issue
        assert "file" in issue
        assert "category" in issue


def test_fix_proposal_and_apply(setup_dummy_project):
    project_id = setup_dummy_project
    
    # Propose fix
    payload = {
        "file": "backend/main.py",
        "line": 1,
        "category": "CODE_QUALITY",
        "title": "Clean print statement",
        "description": "Code is unorganized",
        "suggested_fix": "Use logging library instead of print"
    }
    response = client.post(f"/api/project/{project_id}/propose-fix", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "diff" in data
    assert "before" in data
    assert "after" in data
    
    # Apply proposed content
    apply_payload = {
        "file": "backend/main.py",
        "content": "import logging\nlogging.info('updated to log')"
    }
    apply_res = client.post(f"/api/project/{project_id}/apply-fix", json=apply_payload)
    assert apply_res.status_code == 200
    assert apply_res.json()["success"] is True
    
    # Verify snapshot with source AI_FIX
    history = global_version_manager.get_version_history(project_id)
    # 2 snapshots: 1 from previous setup if created, otherwise 1
    assert len(history) >= 1
    assert history[-1].change_source == "AI_FIX"


def test_rollback_snapshots(setup_dummy_project):
    project_id = setup_dummy_project
    
    # Create two snapshots
    client.put(f"/api/project/{project_id}/file", json={"path": "backend/main.py", "content": "version 1 content"})
    client.put(f"/api/project/{project_id}/file", json={"path": "backend/main.py", "content": "version 2 content"})
    
    history = global_version_manager.get_version_history(project_id)
    assert len(history) == 2
    v1_id = history[0].version_id
    
    # Rollback to v1
    rollback_res = client.post(f"/api/project/{project_id}/rollback", json={"version_id": v1_id})
    assert rollback_res.status_code == 200
    assert rollback_res.json()["success"] is True
    
    # Verify disk content is restored to version 1
    file_path = GENERATED_PROJECTS_DIR / project_id / "backend/main.py"
    assert file_path.read_text(encoding="utf-8") == "version 1 content"
