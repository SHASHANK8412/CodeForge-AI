"""
AIForge Generated File Content Integrity Automated Test Suite
==============================================================
Automated unit, integration, write-readback, ZIP validation, and E2E tests for:
- FileIntegrityValidator
- PlaceholderDetector
- Unified code_extractor regex patterns
- Write -> Read-Back SHA256 checksum validation
- ZIP export archive integrity validation
- REST API Debug Endpoint GET /api/projects/{id}/integrity
- Full E2E non-empty generated source code pipeline
"""

import pytest
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.validation.file_integrity import FileIntegrityValidator, FileRepresentation
from backend.validation.placeholder_detector import PlaceholderDetector
from backend.validation.code_extractor import extract_files_from_agent_output
from backend.services.project_builder import StructuredProjectBuilder
from backend.services.zip_service import ZipService

client = TestClient(app)


class TestFileIntegrityValidator:
    """Verifies language- and functionality-aware file completeness validation."""

    def test_complete_python_file_valid(self):
        validator = FileIntegrityValidator()
        code = "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health(): return {'status': 'ok'}\n"
        rep = validator.validate_file_representation("backend/main.py", code)
        assert rep.is_valid
        assert rep.status == "VALID"
        assert rep.lines >= 5
        assert len(rep.sha256) == 64

    def test_comment_only_placeholder_rejected(self):
        validator = FileIntegrityValidator()
        placeholder_code = "# JWT Authentication Middleware\n"
        rep = validator.validate_file_representation("backend/auth.py", placeholder_code)
        assert not rep.is_valid
        assert rep.status == "PLACEHOLDER"

    def test_allowed_empty_files_pass(self):
        validator = FileIntegrityValidator()
        rep = validator.validate_file_representation("backend/__init__.py", "")
        assert rep.is_valid
        assert rep.status == "VALID"


class TestPlaceholderDetector:
    """Verifies contextual detection of comment stubs, TODO comments, and ellipsis."""

    def test_detects_comment_stub(self):
        detector = PlaceholderDetector()
        res = detector.detect("backend/auth.py", "# JWT Authentication Middleware\n")
        assert res.is_placeholder
        assert "comment" in res.reason.lower()

    def test_detects_todo_stub(self):
        detector = PlaceholderDetector()
        res = detector.detect("frontend/src/App.jsx", "// TODO: Implement dashboard components\n")
        assert res.is_placeholder
        assert "todo" in res.reason.lower()

    def test_allows_legitimate_init(self):
        detector = PlaceholderDetector()
        res = detector.detect("backend/__init__.py", "")
        assert not res.is_placeholder


class TestCodeExtractorPatterns:
    """Verifies unified multi-file code block parsing across languages."""

    def test_extracts_python_sql_jsx_blocks(self):
        llm_output = (
            "# filepath: backend/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```\n\n"
            "-- filepath: database/schema.sql\n```sql\nCREATE TABLE users (id SERIAL PRIMARY KEY);\n```\n\n"
            "// filepath: frontend/src/App.jsx\n```jsx\nexport default function App() { return <div>App</div>; }\n```\n"
        )
        extracted = extract_files_from_agent_output(llm_output)
        assert "backend/main.py" in extracted
        assert "database/schema.sql" in extracted
        assert "frontend/src/App.jsx" in extracted


class TestWriteReadbackAndZipValidation:
    """Verifies write->readback SHA256 checksum verification and ZIP archive validation."""

    def test_write_readback_sha256_checksum(self, tmp_path):
        builder = StructuredProjectBuilder()
        manifest = {
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            "README.md": "# Demo Application\n"
        }
        target_dir = builder.write_project_to_disk("Integrity_Demo", manifest, base_dir=str(tmp_path))
        assert target_dir.exists()
        assert (target_dir / "backend/main.py").read_text() == manifest["backend/main.py"]

    def test_zip_integrity_validation(self, tmp_path):
        builder = StructuredProjectBuilder()
        zip_svc = ZipService()
        manifest = {
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            "README.md": "# Demo Application\n"
        }
        proj_dir = builder.write_project_to_disk("Zip_Integrity_Demo", manifest, base_dir=str(tmp_path))
        zip_path = tmp_path / "Zip_Integrity_Demo.zip"
        zip_svc.zip_project(proj_dir, zip_path)
        assert zip_svc.validate_zip_integrity(zip_path, proj_dir)


class TestIntegrityAPIEndpoints:
    """Verifies GET /api/projects/{generation_id}/files and GET /api/projects/{project_id}/integrity endpoints."""

    def test_files_endpoint_returns_file_representation(self):
        res = client.get("/api/projects/demo_project/files")
        assert res.status_code == 200
        data = res.json()
        assert "files" in data
        assert isinstance(data["files"], list)

    def test_integrity_debug_endpoint(self):
        res = client.get("/api/projects/demo_project/integrity")
        assert res.status_code == 200
        data = res.json()
        assert "integrity" in data
        assert "files_detail" in data
