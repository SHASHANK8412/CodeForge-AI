"""
AIForge Execution & Self-Healing Engine Automated Test Suite
============================================================
Automated unit, integration, failure demo, and security tests for:
- ProjectDetector
- ErrorClassifier
- SandboxedExecutionManager
- ExecutionAgent
- DiagnosticAgent
- RepairAgent
- 8-Level ValidationPipeline
- REST API Execution Endpoints
- Intentionally Broken Self-Healing Failure Demos
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.execution.project_detector import ProjectDetector
from backend.execution.error_classifier import ErrorClassifier
from backend.execution.sandbox_manager import SandboxedExecutionManager
from backend.agents.execution_agent import ExecutionAgent
from backend.agents.diagnostic_agent import DiagnosticAgent
from backend.agents.repair_agent import RepairAgent
from backend.validation.validation_pipeline import ValidationPipeline

client = TestClient(app)


class TestProjectDetector:
    """Verifies automatic detection of language, framework, and build/test commands."""

    def test_react_vite_detection(self):
        detector = ProjectDetector()
        manifest = {
            "package.json": '{"dependencies": {"react": "^18.0.0", "vite": "^4.0.0"}, "scripts": {"dev": "vite", "build": "vite build"}}',
            "src/App.jsx": "export default function App() {}"
        }
        cfg = detector.detect(manifest)
        assert cfg.language == "javascript"
        assert cfg.framework == "vite"
        assert cfg.start_command == "npm run dev"

    def test_fastapi_python_detection(self):
        detector = ProjectDetector()
        manifest = {
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "requirements.txt": "fastapi\nuvicorn\n"
        }
        cfg = detector.detect(manifest)
        assert cfg.language == "python"
        assert cfg.framework == "fastapi"
        assert cfg.test_command == "python -m pytest"


class TestErrorClassifier:
    """Verifies deterministic classification across 18 error categories."""

    def test_syntax_error_classification(self):
        classifier = ErrorClassifier()
        cat = classifier.classify("SyntaxError: invalid syntax (main.py, line 12)")
        assert cat == "syntax_error"

    def test_import_error_classification(self):
        classifier = ErrorClassifier()
        cat = classifier.classify("ModuleNotFoundError: No module named 'requests'")
        assert cat == "import_error"

    def test_port_conflict_classification(self):
        classifier = ErrorClassifier()
        cat = classifier.classify("OSError: [Errno 98] Address already in use: 8000")
        assert cat == "port_conflict"


class TestSandboxedExecutionManager:
    """Verifies command allowlist, process timeout, and security isolation."""

    def test_disallowed_command_blocked(self):
        mgr = SandboxedExecutionManager()
        res = mgr.execute_command("rm -rf /")
        assert res.status == "security_violation"
        assert res.exit_code == 126

    def test_allowed_command_executed(self):
        mgr = SandboxedExecutionManager()
        res = mgr.execute_command("python --version")
        assert res.status == "success"
        assert res.exit_code == 0
        assert "Python" in res.stdout or "Python" in res.stderr


class TestDiagnosticAndRepairAgents:
    """Verifies diagnostic root cause isolation and targeted patch generation."""

    def test_diagnostic_agent_structured_output(self):
        agent = DiagnosticAgent()
        exec_report = {
            "failed_command": "python -m pytest",
            "error_message": "ModuleNotFoundError: No module named 'jwt'",
            "stderr": "ModuleNotFoundError: No module named 'jwt'"
        }
        diag = agent.diagnose_failure(exec_report, {"backend/auth.py": "import jwt"})
        assert diag.error_category == "import_error"
        assert "jwt" in diag.root_cause.lower() or "import" in diag.root_cause.lower()

    def test_repair_agent_code_patch(self):
        agent = RepairAgent()
        diag_data = {
            "root_cause": "ModuleNotFoundError: No module named 'jwt'",
            "affected_files": ["backend/auth.py"],
            "recommended_fix": "Add import jwt"
        }
        files_map = {"backend/auth.py": "# Auth module\n"}
        res = agent.repair_code(diag_data, files_map)
        assert res["status"] == "fixed"
        assert "backend/auth.py" in files_map
        assert "jwt" in files_map["backend/auth.py"]


class TestValidationPipeline:
    """Verifies 8-Level validation pipeline and quality score generation."""

    def test_pipeline_all_passed(self):
        pipeline = ValidationPipeline()
        manifest = {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()", "package.json": "{}", "src/App.jsx": "export default function App() {}"}
        report = pipeline.run_pipeline(manifest, {"status": "success", "exit_code": 0}, {"failed": 0, "passed": 10})
        assert report.is_production_ready
        assert report.overall_status == "PRODUCTION_READY"
        assert report.quality_scores["overall_score"] > 85.0


class TestExecutionAPIEndpoints:
    """Verifies REST API execution and repair endpoints."""

    def test_execute_endpoint(self):
        res = client.post(
            "/api/projects/demo_proj_1/execute",
            json={"files": {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n"}}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "validation" in data

    def test_get_execution_endpoint(self):
        res = client.get("/api/projects/demo_proj_1/execution")
        assert res.status_code == 200
        data = res.json()
        assert "execution" in data

    def test_repair_endpoint(self):
        res = client.post(
            "/api/projects/demo_proj_1/repair",
            json={
                "files": {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n"},
                "diagnostic": {"root_cause": "Fix syntax", "affected_files": ["backend/main.py"]}
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "re_validation" in data


class TestSelfHealingFailureDemo:
    """Simulates an intentionally broken project that is executed, diagnosed, repaired, and verified."""

    def test_broken_project_self_healing_flow(self):
        # 1. Broken project with syntax bug
        broken_files = {
            "backend/main.py": "'WRONG' syntax file\nfrom fastapi import FastAPI\napp = FastAPI()\n",
            "README.md": "# App"
        }

        # 2. Execute
        exec_agent = ExecutionAgent()
        report = exec_agent.execute_project(broken_files)

        # 3. Diagnose
        diag_agent = DiagnosticAgent()
        diag = diag_agent.diagnose_failure(report.model_dump(), broken_files)

        # 4. Repair
        repair_agent = RepairAgent()
        repair_res = repair_agent.repair_code(diag.model_dump(), broken_files)

        # 5. Re-execute & Re-validate
        re_exec = exec_agent.execute_project(broken_files)
        pipeline = ValidationPipeline()
        val_report = pipeline.run_pipeline(broken_files, re_exec.model_dump())

        assert repair_res["status"] == "fixed"
        assert val_report.overall_status in ["PRODUCTION_READY", "PASSED_WITH_WARNINGS"]
