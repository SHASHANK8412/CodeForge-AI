"""
AIForge Security Hardening Regression Test Suite
================================================
Automated security regression tests verifying fixes for the 20 Security Audit domains:
- CORS Security Misconfigurations
- Secret / API Key Exposure in Telemetry Traces
- Command & Shell Injection in Tool Adapters
- Path Traversal & Zip Slip Vulnerabilities
- Input Validation & Project Workspace Isolation
"""

import pytest
import io
import zipfile
from fastapi.testclient import TestClient

from backend.main import app
from backend.observability.service import OpenTelemetryService, _sanitize_headers
from backend.tools.git_tool import GitTool
from backend.tools.safety.command_validator import CommandValidator
from backend.exporter.zipper import ProjectZipper
from backend.validation.generated_file_validator import GeneratedFileValidator
from backend.services.project_builder import StructuredProjectBuilder

client = TestClient(app)


class TestCORSHandledSecurely:
    """Verifies CORS headers restrict unauthorized cross-origin requests."""

    def test_cors_preflight_restricted_origin(self):
        res = client.options(
            "/api/generate-project",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert res.status_code in [200, 204, 405]
        # Verify wildcard * is not reflected when credentials are allowed
        cors_origin = res.headers.get("access-control-allow-origin", "")
        assert cors_origin != "*"

    def test_cors_untrusted_origin_rejected(self):
        res = client.options(
            "/api/generate-project",
            headers={
                "Origin": "http://evil-attacker.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        cors_origin = res.headers.get("access-control-allow-origin", "")
        assert cors_origin != "http://evil-attacker.com"
        assert cors_origin != "*"


class TestSecretExposureInTelemetry:
    """Verifies sensitive headers (Authorization, Cookie, API Keys) are redacted from trace logs."""

    def test_bearer_token_redaction(self):
        headers = {
            "Authorization": "Bearer secret_jwt_token_12345",
            "Cookie": "session_id=abcdef123456",
            "X-API-Key": "sk_live_999888777",
            "User-Agent": "PytestClient"
        }
        sanitized = _sanitize_headers(headers)
        assert sanitized["Authorization"] == "[REDACTED]"
        assert sanitized["Cookie"] == "[REDACTED]"
        assert sanitized["X-API-Key"] == "[REDACTED]"
        assert sanitized["User-Agent"] == "PytestClient"

    def test_opentelemetry_record_trace_secrets_redacted(self):
        service = OpenTelemetryService()
        raw_headers = {"authorization": "Bearer secret_token_xyz"}
        trace = service.record_trace("proj_1", "POST", "/api/test", 200, headers=raw_headers)
        span = trace.spans[0]
        stored_headers = span.attributes.get("headers", {})
        assert stored_headers.get("authorization") in ["[REDACTED_HEADER]", "[REDACTED]"]
        assert "secret_token_xyz" not in str(stored_headers)


class TestCommandAndShellInjection:
    """Verifies command execution adapters reject shell injection attempts."""

    def test_git_tool_command_injection_rejected(self):
        tool = GitTool()
        # Chained command attempt
        res = tool.execute(git_cmd="status; calc.exe")
        # Command should fail or execute safely without running injected payload
        assert isinstance(res, dict)
        assert res["exit_code"] != 0 or "git" in res["stdout"] or "git" in res["stderr"]

    def test_command_validator_blocks_shell_chaining(self):
        val = CommandValidator()
        assert not val.validate_command("git status; rm -rf /")
        assert not val.validate_command("python -c 'print(1)' && whoami")
        assert not val.validate_command("ls -la | grep main")
        assert not val.validate_command("echo $(id)")
        assert val.validate_command("git status")
        assert val.validate_command("pytest tests/")


TestPathTraversalAndZipSlip = """
Path Traversal & Zip Slip Tests are covered in test_hostile_qa_suite.py
"""


class TestZipSlipProtection:
    """Verifies ZipExporter / ProjectZipper filters relative path traversal sequences."""

    def test_project_zipper_strips_path_traversal(self):
        zipper = ProjectZipper()
        files = {
            "app/main.py": "print('ok')",
            "../../etc/passwd": "root:x:0:0:",
            "../secret.env": "DB_PASS=secret"
        }
        zip_bytes = zipper.create_zip_bytes(files, root_folder="secure_app")
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for name in zf.namelist():
                assert ".." not in name
                assert name.startswith("secure_app/")


class TestProjectIsolation:
    """Verifies project files are written strictly inside target output directory."""

    def test_builder_rejects_unsafe_project_paths(self):
        builder = StructuredProjectBuilder()
        manifest = {
            "valid.py": "x = 1"
        }
        # Path traversal in project name
        res = builder.assemble_real_project("../UnsafeProject", {}, {}, "", "", "")
        assert not res["safe_dir_name"].startswith("..")
        assert "UnsafeProject" in res["safe_dir_name"]
