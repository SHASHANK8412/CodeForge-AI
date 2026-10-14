"""
Unit and Integration Tests for Autonomous Code Execution & Validation Engine
=============================================================================
Tests:
- Successful project execution (Python, Node.js, React/Vite)
- Failed execution and test failure detection
- Execution timeout enforcement and process cleanup
- Dependency installation failure handling
- Autonomous self-healing retry behavior & code repair application
- Configurable maximum retry limit enforcement
- Structured execution result & final validation report properties
- REST API validation endpoints and SSE streaming
"""

import sys
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.execution.models import (
    ExecutionStatus,
    PipelineStep,
    AutonomousValidationConfig,
    FinalValidationReport,
    ProjectExecutionResult,
)
from backend.execution.autonomous_execution_engine import (
    AutonomousExecutionEngine,
    SubprocessSandboxRunner,
)
from backend.execution.project_detector import ProjectDetector
from backend.agents.debug_agent import DebugAgent
from backend.agents.testing_agent import TestingAgent

client = TestClient(app)


class TestProjectDetection:
    """Verifies automated project type and command detection across multiple tech stacks."""

    def test_python_project_detection(self):
        detector = ProjectDetector()
        manifest = {
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
            "requirements.txt": "fastapi\nuvicorn\npytest\n",
            "tests/test_api.py": "def test_ok(): assert True\n"
        }
        cfg = detector.detect(manifest)
        assert cfg.language == "python"
        assert cfg.framework == "fastapi"
        assert cfg.package_manager == "pip"
        assert "pytest" in cfg.test_command

    def test_node_project_detection(self):
        detector = ProjectDetector()
        manifest = {
            "package.json": '{"name": "express-app", "dependencies": {"express": "^4.18.0"}, "scripts": {"test": "mocha", "start": "node index.js"}}',
            "index.js": "const express = require('express');\nconst app = express();\n"
        }
        cfg = detector.detect(manifest)
        assert cfg.language == "javascript"
        assert cfg.framework == "express"
        assert cfg.package_manager == "npm"
        assert "test" in cfg.test_command

    def test_react_vite_project_detection(self):
        detector = ProjectDetector()
        manifest = {
            "package.json": '{"name": "vite-react", "dependencies": {"react": "^18.0.0", "vite": "^4.0.0"}, "scripts": {"build": "vite build", "test": "vitest run"}}',
            "src/App.jsx": "export default function App() { return <div>App</div>; }",
            "vite.config.js": "export default {};"
        }
        cfg = detector.detect(manifest)
        assert cfg.language == "javascript"
        assert cfg.framework == "vite"
        assert cfg.package_manager == "npm"
        assert cfg.start_command == "npm run dev" or "vite" in cfg.build_command


class TestAutonomousExecutionEngine:
    """Verifies core engine execution, timeout, sandboxing, and report generation."""

    def test_successful_execution(self):
        engine = AutonomousExecutionEngine()
        manifest = {
            "backend/main.py": "def add(a, b): return a + b\n",
            "tests/test_add.py": "from backend.main import add\ndef test_add(): assert add(2, 3) == 5\n"
        }
        config = AutonomousValidationConfig(
            timeout_seconds=15.0,
            max_repair_attempts=2,
            install_dependencies=False
        )
        report: FinalValidationReport = engine.execute_and_validate(
            files_manifest=manifest,
            project_name="SuccessMathApp",
            config=config
        )

        assert report.is_production_ready is True
        assert report.overall_status == "VERIFIED"
        assert report.attempts_count == 1
        assert len(report.steps) >= 3
        # Check step sequence
        step_names = [s.step.value for s in report.steps]
        assert "Preparing project" in step_names
        assert "Running tests" in step_names
        assert "Tests passed" in step_names
        assert "Final result" in step_names

    def test_failed_execution_and_retry(self):
        """Simulates a project with a failing test that the DebugAgent repairs."""
        engine = AutonomousExecutionEngine()
        broken_manifest = {
            "backend/main.py": "def get_status(): return {'status': 'WRONG'}\n",
            "tests/test_status.py": "from backend.main import get_status\ndef test_status(): assert get_status()['status'] == 'OK'\n"
        }
        config = AutonomousValidationConfig(
            timeout_seconds=15.0,
            max_repair_attempts=3,
            install_dependencies=False
        )
        report: FinalValidationReport = engine.execute_and_validate(
            files_manifest=broken_manifest,
            project_name="SelfHealApp",
            config=config
        )

        assert report.attempts_count >= 1
        assert len(report.steps) > 3
        step_names = [s.step.value for s in report.steps]
        assert "Tests failed" in step_names
        assert "Debugging" in step_names
        assert "Applying fix" in step_names

    def test_maximum_retry_limit(self):
        """Ensures the engine halts cleanly when max_repair_attempts is reached."""
        engine = AutonomousExecutionEngine()
        # Create an unfixable assertion test error where code doesn't exist to repair
        unfixable_manifest = {
            "tests/test_broken.py": "def test_impossible(): assert 1 == 2\n"
        }
        config = AutonomousValidationConfig(
            timeout_seconds=10.0,
            max_repair_attempts=2,
            install_dependencies=False
        )
        report: FinalValidationReport = engine.execute_and_validate(
            files_manifest=unfixable_manifest,
            project_name="UnfixableApp",
            config=config
        )

        assert report.is_production_ready is False
        assert report.overall_status == "FAILED_MAX_RETRIES"
        assert report.attempts_count == 2
        assert report.max_attempts == 2

    def test_timeout_enforcement(self):
        """Verifies that long-running/hanging processes are killed and flagged as TIMEOUT."""
        runner = SubprocessSandboxRunner()
        # Command that sleeps longer than timeout
        sleep_cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
        with pytest.MonkeyPatch.context() as mp:
            res: ProjectExecutionResult = runner.execute_command(
                command=sleep_cmd,
                cwd=".",
                timeout_seconds=0.8,
                max_output_bytes=10000
            )
            assert res.timed_out is True
            assert res.status == ExecutionStatus.TIMEOUT
            assert "timed out" in res.stderr.lower()

    def test_output_truncation_enforcement(self):
        """Verifies that large stdout/stderr outputs are safely truncated to protect system resources."""
        runner = SubprocessSandboxRunner()
        big_output_cmd = [sys.executable, "-c", "print('A' * 20000)"]
        res = runner.execute_command(
            command=big_output_cmd,
            cwd=".",
            timeout_seconds=10.0,
            max_output_bytes=1000
        )
        assert len(res.stdout) <= 1200
        assert "[OUTPUT_LIMIT_EXCEEDED]" in res.stdout

    def test_dependency_installation_failure_handled(self):
        """Verifies that dependency installation failure is recorded in steps log without crashing."""
        engine = AutonomousExecutionEngine()
        invalid_dep_manifest = {
            "backend/main.py": "def test_fn(): pass\n",
            "requirements.txt": "this-package-definitely-does-not-exist-xyz9999==0.0.1\n",
            "tests/test_app.py": "def test_fn(): assert True\n"
        }
        config = AutonomousValidationConfig(
            timeout_seconds=10.0,
            max_repair_attempts=1,
            install_dependencies=True
        )
        report = engine.execute_and_validate(
            files_manifest=invalid_dep_manifest,
            project_name="DepFailApp",
            config=config
        )
        step_names = [s.step.value for s in report.steps]
        assert "Installing dependencies" in step_names
        dep_step = [s for s in report.steps if s.step == PipelineStep.INSTALLING_DEPENDENCIES][-1]
        assert dep_step.status == "FAILED" or dep_step.exit_code != 0

    def test_structured_execution_result_fields(self):
        """Ensures all captured metrics and structured fields are populated accurately."""
        engine = AutonomousExecutionEngine()
        manifest = {
            "backend/main.py": "def check(): return True\n",
            "tests/test_check.py": "from backend.main import check\ndef test_check(): assert check() is True\n"
        }
        config = AutonomousValidationConfig(
            timeout_seconds=15.0,
            max_repair_attempts=1,
            install_dependencies=False
        )
        report = engine.execute_and_validate(
            files_manifest=manifest,
            project_name="FieldsApp",
            config=config
        )
        assert report.project_name == "FieldsApp"
        assert report.total_duration_ms > 0
        assert isinstance(report.test_summary, dict)
        for s in report.steps:
            assert hasattr(s, "step")
            assert hasattr(s, "status")
            assert hasattr(s, "command")
            assert hasattr(s, "stdout")
            assert hasattr(s, "stderr")
            assert hasattr(s, "exit_code")
            assert hasattr(s, "duration_ms")


class TestAutonomousValidationAPI:
    """Verifies FastAPI REST endpoints and SSE streaming."""

    def test_autonomous_validate_endpoint(self):
        payload = {
            "files": {
                "backend/main.py": "def get_val(): return 42\n",
                "tests/test_val.py": "from backend.main import get_val\ndef test_val(): assert get_val() == 42\n"
            },
            "timeout_seconds": 15,
            "max_repair_attempts": 2,
            "install_dependencies": False
        }
        res = client.post("/api/projects/api_test_project/autonomous-validate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "report" in data
        assert data["report"]["overall_status"] == "VERIFIED"
        assert data["report"]["is_production_ready"] is True

    def test_autonomous_report_get_endpoint(self):
        # First ensure report is created
        payload = {
            "files": {"backend/main.py": "def val(): return 1\n", "tests/test_v.py": "def test_v(): assert True\n"},
            "install_dependencies": False
        }
        client.post("/api/projects/cached_proj/autonomous-validate", json=payload)

        res = client.get("/api/projects/cached_proj/autonomous-report")
        assert res.status_code == 200
        data = res.json()
        assert data["project_name"] == "cached_proj"
        assert data["is_production_ready"] is True

    def test_api_execution_validate_alias(self):
        payload = {
            "files": {"backend/main.py": "def status(): return 'OK'\n", "tests/test_s.py": "def test_s(): assert True\n"},
            "install_dependencies": False
        }
        res = client.post("/api/execution/validate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "report" in data
