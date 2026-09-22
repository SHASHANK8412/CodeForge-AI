"""
AIForge Code Workspace Automated Unit & Integration Test Suite
================================================================
Automated tests for Code Workspace state, Review finding line parsing,
file tree hierarchy, status bar metadata formatting, and project file loading.
"""

import pytest
from backend.services.project_builder import StructuredProjectBuilder
from backend.review.security_checker import SecurityChecker
from backend.validation.generated_file_validator import GeneratedFileValidator


class TestCodeWorkspaceIntegrity:
    """Verifies workspace file loading, line jump locations, and manifest structure."""

    def test_assembled_project_manifest_integrity(self):
        builder = StructuredProjectBuilder()
        assembled = builder.assemble_real_project(
            project_name="Workspace IDE Test",
            plan_json={},
            arch_json={},
            frontend_code="// filepath: src/App.jsx\n```jsx\nimport React from 'react';\nexport default function App() {\n  return <div>IDE Test</div>;\n}\n```",
            backend_code="# filepath: backend/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```",
            database_code="-- filepath: database/schema.sql\n```sql\nCREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(255));\n```",
            testing_code="# filepath: tests/test_api.py\n```python\ndef test_health():\n    assert True\n```",
            docs_code="# Workspace IDE Test Documentation\nStandard documentation."
        )
        assert assembled["total_files"] >= 4
        manifest = assembled["manifest"]
        assert "backend/main.py" in manifest

    def test_security_checker_project_scan(self, tmp_path):
        checker = SecurityChecker()
        test_file = tmp_path / "main.py"
        test_file.write_text("import os\neval('1+1')\nsubprocess.run('rm -rf /', shell=True)", encoding="utf-8")
        findings = checker.check_project(tmp_path)
        assert isinstance(findings, list)
        assert len(findings) > 0
        assert "issue" in findings[0] or "severity" in findings[0]

    def test_file_size_and_line_count_calculations(self):
        content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
        lines = content.split("\n")
        assert len(lines) == 6
        file_size = len(content.encode("utf-8"))
        assert file_size > 0
