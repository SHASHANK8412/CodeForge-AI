import io
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.services.project_assembler import ProjectAssembler
from backend.services.project_validator import ProjectValidator
from backend.services.project_tester import ProjectTester
from backend.services.project_exporter import ProjectExporter
from backend.main import app

client = TestClient(app)


def test_assembler_merging_and_safety():
    assembler = ProjectAssembler()

    agent_outputs = {
        "frontend": {
            "frontend/src/App.jsx": "export default function App() {}",
            "frontend/package.json": '{"name": "test-app"}'
        },
        "backend": {
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            # Unsafe traversal path should be blocked
            "../../etc/passwd": "malicious",
            "backend/requirements.txt": "fastapi>=0.100.0\n"
        },
        "database": {
            "database/schema.sql": "CREATE TABLE users (id SERIAL PRIMARY KEY);"
        }
    }

    assembled = assembler.assemble_project(agent_outputs, project_name="UnitTest_Proj")
    files = assembled["files"]
    manifest = assembled["manifest"]

    assert "frontend/src/App.jsx" in files
    assert "backend/main.py" in files
    assert "../../etc/passwd" not in files
    assert "etc/passwd" not in files
    
    assert manifest["total_files"] == 5
    assert len(manifest["conflicts"]) == 0
    assert len(manifest["duplicates"]) == 0


def test_assembler_conflicts_and_duplicates():
    assembler = ProjectAssembler()

    agent_outputs = {
        "frontend": {
            "shared/utils.js": "export const data = 1;"
        },
        "backend": {
            # Same path, DIFFERENT content -> Conflict
            "shared/utils.js": "export const data = 2;"
        }
    }

    assembled = assembler.assemble_project(agent_outputs, project_name="Conflict_Proj")
    files = assembled["files"]
    manifest = assembled["manifest"]

    assert "shared/utils.js" in files
    assert len(manifest["conflicts"]) == 1
    assert manifest["files"][0]["status"] == "conflict_resolved"


def test_validator_integrity_and_secrets():
    validator = ProjectValidator()

    files = {
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "backend/requirements.txt": "fastapi>=0.100.0\n",
        "frontend/package.json": '{"name": "test-app", "dependencies": {}}',
        "frontend/src/App.jsx": "export default function App() { return <div>App</div>; }",
        "database/schema.sql": "CREATE TABLE posts (id INT);",
        "README.md": "# Project Title",
        # Accidental secret
        "backend/config.py": "OPENAI_API_KEY = 'sk-proj-1234567890abcdef1234567890abcdef'\n"
    }

    manifest = {
        "project_name": "Validator_Proj",
        "files": [{"path": p, "agent": "backend", "size": len(c)} for p, c in files.items()]
    }

    summary = validator.validate_project(files, manifest)
    assert summary["score"] < 100.0  # Points deducted for secret
    assert summary["details"]["secrets_detected_count"] == 1
    # Check that the secret was detected
    assert any("secret detected" in err.lower() for err in summary["errors"])


def test_validator_empty_files_deduction():
    validator = ProjectValidator()

    files = {
        "backend/main.py": "",  # Empty critical file -> FAIL
        "backend/requirements.txt": "fastapi",
        "frontend/package.json": '{"name": "app"}',
        "frontend/src/App.jsx": "export default function App() {}",
        "README.md": ""  # Empty non-critical file -> warning
    }

    manifest = {
        "project_name": "Empty_Proj",
        "files": [{"path": p, "agent": "backend", "size": len(c)} for p, c in files.items()]
    }

    summary = validator.validate_project(files, manifest)
    assert summary["status"] == "FAIL"
    assert any("is empty" in err for err in summary["errors"])
    assert len(summary["warnings"]) >= 1


def test_exporter_zipping():
    exporter = ProjectExporter()

    files = {
        "backend/main.py": "print('hello')",
        "backend/__pycache__/main.cpython.pyc": "binary",
        "node_modules/react/index.js": "react source",
        "README.md": "# Readme"
    }

    zip_path = exporter.export_project("Zip_Proj", files)
    assert Path(zip_path).exists()
    assert zip_path.name.endswith(".zip")

    # Read zip and verify exclusions
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "Zip_Proj/backend/main.py" in namelist
        assert "Zip_Proj/README.md" in namelist
        # Excluded paths should not be in zip
        assert not any("__pycache__" in name for name in namelist)
        assert not any("node_modules" in name for name in namelist)

    # Clean up test zip
    zip_path.unlink()


def test_api_routes():
    # 1. Test POST /api/project/validate
    payload = {
        "project_id": "test_gen_api",
        "files": {
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "frontend/package.json": '{"name": "app"}',
            "README.md": "# Title"
        }
    }
    res = client.post("/api/project/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "score" in data
    assert "status" in data

    # 2. Test GET /api/project/{project_id}/status
    res = client.get("/api/project/test_gen_api/status")
    assert res.status_code == 200
    assert "status" in res.json()

    # 3. Test GET /api/project/{project_id}/files
    res = client.get("/api/project/test_gen_api/files")
    assert res.status_code == 200
    assert "files" in res.json()
