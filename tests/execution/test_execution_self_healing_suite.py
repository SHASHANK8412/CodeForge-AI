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
- Retired REST execution endpoints answer 410 and execute nothing
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

# The diagnostic agent asks the local model for a JSON diagnosis. These tests used to call the real model
# (about 40 s each, and the result depended on its answer); a double gives a fixed, deliberately imperfect
# answer - a non-standard category and paths that do not exist - which the agent must not trust.
SLOPPY_DIAGNOSIS = (
    '```json\n{"root_cause": "No module named jwt", "error_category": "ModuleNotFoundError", '
    '"affected_files": ["auth.py", "../../etc/passwd"], "severity": "HIGH", "confidence": 0.7}\n```'
)


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
        assert cat == "SYNTAX_ERROR"

    def test_import_error_classification(self):
        classifier = ErrorClassifier()
        cat = classifier.classify("ModuleNotFoundError: No module named 'requests'")
        assert cat == "IMPORT_ERROR"

    def test_port_conflict_classification(self):
        classifier = ErrorClassifier()
        cat = classifier.classify("OSError: [Errno 98] Address already in use: 8000")
        assert cat == "PORT_CONFLICT"


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
        agent.generate = lambda prompt: SLOPPY_DIAGNOSIS
        exec_report = {
            "failed_command": "python -m pytest",
            "error_message": "ModuleNotFoundError: No module named 'jwt'",
            "stderr": "ModuleNotFoundError: No module named 'jwt'"
        }
        diag = agent.diagnose_failure(exec_report, {"backend/auth.py": "import jwt"})
        assert diag.error_category == "IMPORT_ERROR"
        assert "jwt" in diag.root_cause.lower() or "import" in diag.root_cause.lower()
        assert diag.affected_files == ["backend/auth.py"]          # invented and traversal paths are dropped

    def test_diagnostic_agent_falls_back_when_the_model_answer_is_unusable(self):
        agent = DiagnosticAgent()
        agent.generate = lambda prompt: "I think the import is broken."
        diag = agent.diagnose_failure({"failed_command": "python -m pytest", "stderr": "ModuleNotFoundError: No module named 'jwt'"},
                                      {"backend/auth.py": "import jwt"})
        assert diag.error_category == "IMPORT_ERROR" and diag.affected_files == ["backend/auth.py"]

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


RETIRED_ENDPOINTS = [
    ("post", "/api/projects/demo_proj_1/execute"),
    ("get", "/api/projects/demo_proj_1/execution"),
    ("post", "/api/projects/demo_proj_1/repair"),
    ("get", "/api/projects/demo_proj_1/validation"),
]
REPLACEMENT = "/api/projects/demo_proj_1/verifications"


class TestRetiredExecutionAPIEndpoints:
    """The request-body execute/repair endpoints and their execution/validation reads are retired in favour
    of the Execution Guardian (/api/projects/{id}/verifications). They must answer 410, name the replacement,
    and run nothing."""

    @pytest.mark.parametrize("method,url", RETIRED_ENDPOINTS)
    def test_retired_endpoint_returns_410_naming_replacement(self, method, url):
        res = getattr(client, method)(url, **({"json": {}} if method == "post" else {}))
        assert res.status_code == 410
        data = res.json()
        assert data["replacement"] == REPLACEMENT
        assert REPLACEMENT in data["detail"]

    @pytest.mark.parametrize("url", [u for m, u in RETIRED_ENDPOINTS if m == "post"])
    def test_retired_endpoint_executes_nothing_from_request(self, url, tmp_path, monkeypatch):
        calls = []
        monkeypatch.setattr(ExecutionAgent, "execute_project", lambda self, *a, **k: calls.append("execute"))
        monkeypatch.setattr(RepairAgent, "repair_code", lambda self, *a, **k: calls.append("repair"))
        monkeypatch.setattr(ValidationPipeline, "run_pipeline", lambda self, *a, **k: calls.append("validate"))
        sentinel = tmp_path / "executed.txt"
        payload = {
            "files": {
                "backend/main.py": f"open({str(sentinel)!r}, 'w').write('ran')\n",
                "tests/test_x.py": "import backend.main\ndef test_x(): assert True\n",
            },
            "diagnostic": {"root_cause": "Fix syntax", "affected_files": ["backend/main.py"]},
            "timeout": 3600,
        }
        res = client.post(url, json=payload)
        assert res.status_code == 410
        assert calls == []
        assert not sentinel.exists()

    @pytest.mark.parametrize("url", [u for m, u in RETIRED_ENDPOINTS if m == "get"])
    def test_retired_read_endpoint_serves_no_report(self, url):
        client.post("/api/projects/demo_proj_1/execute", json={
            "files": {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n"},
        })
        res = client.get(url)
        assert res.status_code == 410
        assert set(res.json()) == {"detail", "replacement"}


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
        diag_agent.generate = lambda prompt: '{"root_cause": "syntax", "affected_files": ["main.py"]}'
        diag = diag_agent.diagnose_failure(report.model_dump(), broken_files)
        assert diag.affected_files and all(f in broken_files for f in diag.affected_files)

        # 4. Repair
        repair_agent = RepairAgent()
        repair_res = repair_agent.repair_code(diag.model_dump(), broken_files)

        # 5. Re-execute & Re-validate
        re_exec = exec_agent.execute_project(broken_files)
        pipeline = ValidationPipeline()
        val_report = pipeline.run_pipeline(broken_files, re_exec.model_dump())

        assert repair_res["status"] == "fixed"
        assert val_report.overall_status in ["PRODUCTION_READY", "PASSED_WITH_WARNINGS"]
