"""
AIForge Security & Dependency Intelligence Engine Automated Test Suite
========================================================================
Automated unit, integration, REST API, and auto-remediation tests for:
- SecretScanner & value masking
- DependencyScanner & unpinned version detection
- SASTScanner (SQLi, Command Injection, shell=True, eval)
- ConfigScanner (CORS wildcards, debug mode)
- APISecurityScanner (Route security matrix)
- DockerGitScanner (Dockerfile non-root user, .gitignore audit)
- SBOMGenerator (SPDX sbom.json generation)
- SecurityManager (Weighted security score & SECURITY_GATE evaluation)
- SecurityRepairAgent (Auto-fixing hardcoded secrets, CORS, .gitignore)
- REST API Security Endpoints
- Intentionally Vulnerable Security Repair Demo
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.security.security_scanners import (
    SecretScanner, DependencyScanner, SASTScanner,
    ConfigScanner, APISecurityScanner, DockerGitScanner
)
from backend.security.sbom_generator import SBOMGenerator
from backend.security.security_manager import SecurityManager
from backend.agents.security_repair_agent import SecurityRepairAgent

client = TestClient(app)


class TestSecretScanner:
    """Verifies pattern matching and secret value masking."""

    def test_secret_pattern_detection_and_masking(self):
        scanner = SecretScanner()
        manifest = {
            "backend/config.py": 'API_KEY = "mock_sk_live_1234567890abcdef1234567890"\nJWT_SECRET = "super_secret_jwt_key"\n'
        }
        findings = scanner.scan(manifest)
        assert len(findings) >= 1
        secret_finding = findings[0]
        assert secret_finding.category == "hardcoded_secret"
        assert secret_finding.severity == "CRITICAL"
        assert secret_finding.masked_value is not None
        assert "1234567890" not in secret_finding.masked_value


class TestDependencyScanner:
    """Verifies package manifest auditing and unpinned dependency detection."""

    def test_unpinned_dependencies_detected(self):
        scanner = DependencyScanner()
        manifest = {
            "package.json": '{"dependencies": {"react": "*", "express": "latest"}}',
            "requirements.txt": "fastapi\nuvicorn\n"
        }
        findings = scanner.scan(manifest)
        assert len(findings) >= 2
        assert any(f.file == "package.json" for f in findings)
        assert any(f.file == "requirements.txt" for f in findings)


class TestSASTScanner:
    """Verifies deterministic SAST vulnerability detection."""

    def test_sql_and_command_injection_detection(self):
        scanner = SASTScanner()
        manifest = {
            "backend/db.py": 'cursor.execute(f"SELECT * FROM users WHERE username = \'{user_input}\'")\n',
            "backend/cmd.py": 'subprocess.run(f"rm -rf {path}", shell=True)\n'
        }
        findings = scanner.scan(manifest)
        assert len(findings) >= 2
        categories = [f.category for f in findings]
        assert "sast_vulnerability" in categories


class TestConfigScanner:
    """Verifies CORS wildcards and debug mode detection."""

    def test_cors_and_debug_mode_detection(self):
        scanner = ConfigScanner()
        manifest = {
            "backend/main.py": "app.add_middleware(CORSMiddleware, allow_origins=['*'])\napp.run(debug=True)\n"
        }
        findings = scanner.scan(manifest)
        assert len(findings) >= 2
        descriptions = [f.description for f in findings]
        assert any("CORS" in d for d in descriptions)
        assert any("debug" in d for d in descriptions)


class TestAPISecurityScanner:
    """Verifies API route security matrix generation."""

    def test_api_security_matrix_generation(self):
        scanner = APISecurityScanner()
        manifest = {
            "backend/main.py": '@app.get("/users")\ndef get_users(): pass\n@app.post("/login")\ndef login(data: BaseModel): pass\n'
        }
        matrix = scanner.scan(manifest)
        assert len(matrix) >= 2
        endpoints = [m["endpoint"] for m in matrix]
        assert "GET /users" in endpoints


class TestSBOMGenerator:
    """Verifies SPDX sbom.json generation."""

    def test_sbom_generation(self):
        generator = SBOMGenerator()
        manifest = {
            "package.json": '{"dependencies": {"react": "^18.2.0"}}',
            "requirements.txt": "fastapi==0.109.0\n"
        }
        sbom = generator.generate_sbom("Test Project", manifest)
        assert sbom.spdx_version == "SPDX-2.3"
        assert len(sbom.components) == 2
        ecosystems = [c.ecosystem for c in sbom.components]
        assert "npm" in ecosystems
        assert "pip" in ecosystems


class TestSecurityManagerAndGate:
    """Verifies weighted Security Score calculation and SECURITY_GATE evaluation."""

    def test_security_gate_evaluation(self):
        mgr = SecurityManager()
        clean_manifest = {
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            "package.json": '{"dependencies": {"react": "18.2.0"}}',
            ".gitignore": ".env\n"
        }
        report = mgr.audit_project("Clean App", clean_manifest)
        assert report.security_score >= 90.0
        assert report.gate_status == "PASSED"

    def test_failed_security_gate_on_critical_finding(self):
        mgr = SecurityManager()
        vuln_manifest = {
            "backend/config.py": 'API_KEY = "mock_sk_live_1234567890abcdef1234567890"\n'
        }
        report = mgr.audit_project("Vuln App", vuln_manifest)
        assert report.security_score < 85.0
        assert report.gate_status == "FAILED"


class TestSecurityRepairAgent:
    """Verifies automatic remediation of hardcoded secrets, CORS, and .gitignore."""

    def test_auto_remediation_of_secrets_and_cors(self):
        repair_agent = SecurityRepairAgent()
        mgr = SecurityManager()

        vuln_manifest = {
            "backend/main.py": 'API_KEY = "mock_sk_live_1234567890abcdef1234567890"\napp.add_middleware(CORSMiddleware, allow_origins=["*"])\n'
        }

        audit_1 = mgr.audit_project("Demo", vuln_manifest)
        fix_res = repair_agent.fix_security_issues(audit_1.findings, vuln_manifest)

        audit_2 = mgr.audit_project("Demo", vuln_manifest)

        assert fix_res.status == "repaired"
        assert ".env.example" in vuln_manifest
        assert ".gitignore" in vuln_manifest
        assert audit_2.security_score > audit_1.security_score


class TestSecurityAPIRoutes:
    """Verifies REST API endpoints for security audit, auto-fix, and SBOM."""

    def test_get_security_endpoint(self):
        res = client.get("/api/projects/sec_demo_1/security")
        assert res.status_code == 200
        data = res.json()
        assert "security_score" in data

    def test_post_security_fix_endpoint(self):
        res = client.post(
            "/api/projects/sec_demo_1/security/fix",
            json={"files": {"backend/main.py": 'API_KEY = "mock_sk_live_1234567890abcdef1234567890"\n'}}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert ".env.example" in data["modified_files"]

    def test_get_sbom_endpoint(self):
        res = client.get("/api/projects/sec_demo_1/sbom")
        assert res.status_code == 200
        data = res.json()
        assert "spdx_version" in data
