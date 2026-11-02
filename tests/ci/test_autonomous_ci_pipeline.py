"""
Unit and Integration Tests for AIForge Autonomous CI/CD Pipeline
================================================================
Covers:
1. Successful pipeline execution (Python)
2. Successful pipeline execution (Node.js/React)
3. Dependency installation failure
4. Build failure handling
5. Test stage failure handling
6. Lint stage failure handling
7. Security stage failure handling (secrets detection)
8. Execution timeout handling
9. Retry mechanism invocation
10. Maximum retry limit enforcement (MAX_CI_REPAIR_ATTEMPTS)
11. Docker execution & graceful failure/fallback handling
12. Successful automated self-repair loop (closed-loop healing)
13. Failed automated repair when retries exhausted
14. Dynamic GitHub Actions workflow generation
15. Project-type detection integration
16. CI Pipeline history persistence and retrieval
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from backend.ci.models import (
    CIStageType,
    CIStageStatus,
    CIOverallStatus,
    CIStageResult,
    CIConfig,
    CIPipelineResult,
)
from backend.ci.pipeline import CIPipelineEngine
from backend.ci.history_store import CIHistoryStore
from backend.ci.github_actions_generator import GitHubActionsWorkflowGenerator
from backend.execution.project_detector import ProjectDetector, DetectedProjectConfig
from backend.execution.models import ProjectExecutionResult, ExecutionStatus, DebugResult
from backend.execution.execution_backend import ExecutionBackend, LocalExecutionBackend, DockerExecutionBackend
from backend.execution.execution_service import ExecutionService


class TestAutonomousCIPipeline:
    """Complete test suite for the Autonomous CI/CD Pipeline."""

    @pytest.fixture
    def mock_execution_service(self):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)
        mock_backend.execute_command.return_value = ProjectExecutionResult(
            status=ExecutionStatus.PASS,
            stdout="Execution successful\nRan 5 tests in 0.05s\nOK",
            stderr="",
            exit_code=0,
            execution_time=0.12,
            timed_out=False
        )
        service.get_backend.return_value = mock_backend
        return service

    @pytest.fixture
    def clean_history_store(self, tmp_path):
        return CIHistoryStore(storage_path=tmp_path / "ci_history.json")

    # -------------------------------------------------------------------------
    # 1. Successful Pipeline Execution (Python)
    # -------------------------------------------------------------------------
    def test_successful_python_pipeline(self, mock_execution_service, clean_history_store):
        engine = CIPipelineEngine(
            execution_service=mock_execution_service,
            history_store=clean_history_store
        )
        files = {
            "requirements.txt": "fastapi>=0.100.0\npytest>=7.0.0\n",
            "main.py": "def hello():\n    return 'world'\n",
            "tests/test_main.py": "from main import hello\ndef test_hello():\n    assert hello() == 'world'\n"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_python_proj",
            config=CIConfig(max_repair_attempts=2, docker_enabled=False)
        )

        assert result.status == CIOverallStatus.PASSED.value
        assert result.repair_attempts == 0
        assert result.dependencies["status"] == CIStageStatus.PASSED.value
        assert result.build["status"] == CIStageStatus.PASSED.value
        assert result.tests["status"] == CIStageStatus.PASSED.value
        assert result.lint["status"] in [CIStageStatus.PASSED.value, CIStageStatus.WARNING.value]
        assert result.security["status"] == CIStageStatus.PASSED.value
        assert result.workflow_yaml != ""
        assert "actions/setup-python" in result.workflow_yaml

    # -------------------------------------------------------------------------
    # 2. Successful Pipeline Execution (Node.js/React)
    # -------------------------------------------------------------------------
    def test_successful_node_pipeline(self, mock_execution_service, clean_history_store):
        engine = CIPipelineEngine(
            execution_service=mock_execution_service,
            history_store=clean_history_store
        )
        files = {
            "package.json": '{"name": "demo-react", "scripts": {"build": "vite build", "test": "vitest run"}}',
            "src/App.jsx": "export default function App() { return <div>Hello Vite</div>; }",
            "vite.config.js": "export default { plugins: [] };"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_node_proj",
            config=CIConfig(max_repair_attempts=1, docker_enabled=False)
        )

        assert result.status == CIOverallStatus.PASSED.value
        assert result.repair_attempts == 0
        assert "actions/setup-node" in result.workflow_yaml
        assert "npm run build" in result.workflow_yaml

    # -------------------------------------------------------------------------
    # 3. Dependency Installation Failure
    # -------------------------------------------------------------------------
    def test_dependency_installation_failure(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)
        # Simulate dependency stage failure
        mock_backend.execute_command.return_value = ProjectExecutionResult(
            status=ExecutionStatus.FAIL,
            stdout="",
            stderr="ERROR: Could not find a version that satisfies the requirement non_existent_pkg==99.99",
            exit_code=1,
            execution_time=0.45
        )
        service.get_backend.return_value = mock_backend

        engine = CIPipelineEngine(
            execution_service=service,
            history_store=clean_history_store
        )
        files = {
            "requirements.txt": "non_existent_pkg==99.99\n",
            "main.py": "print('ok')\n"
        }

        # Prevent debug agent from looping by setting max_repair_attempts=0
        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_dep_fail",
            config=CIConfig(max_repair_attempts=0)
        )

        assert result.status == CIOverallStatus.FAILED.value
        assert result.dependencies["status"] == CIStageStatus.FAILED.value
        assert "non_existent_pkg" in result.dependencies["stderr"]

    # -------------------------------------------------------------------------
    # 4. Build Failure Handling
    # -------------------------------------------------------------------------
    def test_build_failure(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)

        def mock_exec(*args, **kwargs):
            cmd = kwargs.get("command") or (args[0] if args else [])
            cmd_str = " ".join(cmd)
            if "py_compile" in cmd_str or "build" in cmd_str:
                return ProjectExecutionResult(
                    status=ExecutionStatus.FAIL,
                    stdout="",
                    stderr="SyntaxError: invalid syntax in main.py line 4",
                    exit_code=1,
                    execution_time=0.2
                )
            return ProjectExecutionResult(
                status=ExecutionStatus.PASS,
                stdout="OK",
                stderr="",
                exit_code=0,
                execution_time=0.1
            )

        mock_backend.execute_command.side_effect = mock_exec
        service.get_backend.return_value = mock_backend

        engine = CIPipelineEngine(
            execution_service=service,
            history_store=clean_history_store
        )
        files = {
            "main.py": "def invalid_func(\n    return 42\n"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_build_fail",
            config=CIConfig(max_repair_attempts=0)
        )

        assert result.status == CIOverallStatus.FAILED.value
        assert result.build["status"] == CIStageStatus.FAILED.value

    # -------------------------------------------------------------------------
    # 5. Test Stage Failure Handling
    # -------------------------------------------------------------------------
    def test_test_stage_failure(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)

        def mock_exec(*args, **kwargs):
            cmd = kwargs.get("command") or (args[0] if args else [])
            cmd_str = " ".join(cmd)
            if "pytest" in cmd_str or "test" in cmd_str:
                return ProjectExecutionResult(
                    status=ExecutionStatus.FAIL,
                    stdout="FAILED tests/test_calc.py::test_add - AssertionError: 4 != 5",
                    stderr="",
                    exit_code=1,
                    execution_time=0.3
                )
            return ProjectExecutionResult(
                status=ExecutionStatus.PASS,
                stdout="Installed",
                stderr="",
                exit_code=0,
                execution_time=0.1
            )

        mock_backend.execute_command.side_effect = mock_exec
        service.get_backend.return_value = mock_backend

        engine = CIPipelineEngine(
            execution_service=service,
            history_store=clean_history_store
        )
        files = {
            "main.py": "def add(a, b): return a + b\n",
            "tests/test_calc.py": "from main import add\ndef test_add(): assert add(2, 2) == 5\n"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_unit_fail",
            config=CIConfig(max_repair_attempts=0)
        )

        assert result.status == CIOverallStatus.FAILED.value
        assert result.tests["status"] == CIStageStatus.FAILED.value
        assert "AssertionError" in result.tests["stdout"]

    # -------------------------------------------------------------------------
    # 6. Lint Stage Failure Handling
    # -------------------------------------------------------------------------
    def test_lint_stage_failure(self, mock_execution_service, clean_history_store):
        engine = CIPipelineEngine(
            execution_service=mock_execution_service,
            history_store=clean_history_store
        )
        # Introduce a broken python file with syntax error that causes lint compilation check to fail
        files = {
            "main.py": "def broken_syntax(x\n    return x + 1\n",
            "utils.py": "print('valid')\n"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_lint_fail",
            config=CIConfig(max_repair_attempts=0)
        )

        assert result.status == CIOverallStatus.FAILED.value
        assert result.lint["status"] == CIStageStatus.FAILED.value
        assert result.lint["exit_code"] != 0

    # -------------------------------------------------------------------------
    # 7. Security Stage Failure Handling
    # -------------------------------------------------------------------------
    def test_security_stage_failure(self, mock_execution_service, clean_history_store):
        engine = CIPipelineEngine(
            execution_service=mock_execution_service,
            history_store=clean_history_store
        )
        # Introduce leaked credentials
        files = {
            "config.py": 'AWS_SECRET_KEY = "AKIA1234567890123456"\nAPI_KEY = "api_key = \\"abcdefghijklmnopqrstuvwxyz1234\\""\n',
            "main.py": "print('running')\n"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_sec_fail",
            config=CIConfig(max_repair_attempts=0)
        )

        assert result.status == CIOverallStatus.FAILED.value
        assert result.security["status"] == CIStageStatus.FAILED.value
        assert "Hardcoded secret" in result.security["stdout"] or "AWS_ACCESS_KEY" in result.security["stderr"]

    # -------------------------------------------------------------------------
    # 8. Execution Timeout Handling
    # -------------------------------------------------------------------------
    def test_execution_timeout(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)
        mock_backend.execute_command.return_value = ProjectExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            stdout="Process timed out after 5.0 seconds",
            stderr="TimeoutExpired",
            exit_code=124,
            execution_time=5.0,
            timed_out=True
        )
        service.get_backend.return_value = mock_backend

        engine = CIPipelineEngine(
            execution_service=service,
            history_store=clean_history_store
        )
        files = {
            "main.py": "import time\ntime.sleep(60)\n"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_timeout",
            config=CIConfig(timeout_seconds=5.0, max_repair_attempts=0)
        )

        assert result.status == CIOverallStatus.TIMEOUT.value

    # -------------------------------------------------------------------------
    # 9. Retry Mechanism Invocation
    # -------------------------------------------------------------------------
    def test_retry_mechanism_invokes_debug_agent(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)

        # Stage returns failure
        mock_backend.execute_command.return_value = ProjectExecutionResult(
            status=ExecutionStatus.FAIL,
            stdout="",
            stderr="ImportError: No module named 'utils'",
            exit_code=1,
            execution_time=0.1
        )
        service.get_backend.return_value = mock_backend

        mock_debug_agent = MagicMock()
        mock_debug_agent.diagnose_and_repair.return_value = DebugResult(
            diagnosis="Missing utils module",
            root_cause="File utils.py is absent",
            error_type="ImportError",
            suggested_fix="Create utils.py",
            changes={"utils.py": "def helper(): return 1"},
            confidence=0.95
        )

        engine = CIPipelineEngine(
            execution_service=service,
            debug_agent=mock_debug_agent,
            history_store=clean_history_store
        )
        files = {
            "main.py": "import utils\nprint(utils.helper())\n"
        }

        # Set max attempts to 1
        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_retry_trigger",
            config=CIConfig(max_repair_attempts=1)
        )

        # Verify debug agent was called with diagnostics
        assert mock_debug_agent.diagnose_and_repair.called
        call_arg = mock_debug_agent.diagnose_and_repair.call_args[0][0]
        assert "execution_results" in call_arg
        assert call_arg["execution_results"]["failed_stage"] in ["build", "tests", "dependencies"]

    # -------------------------------------------------------------------------
    # 10. Maximum Retry Limit Enforcement
    # -------------------------------------------------------------------------
    def test_maximum_retry_limit_enforced(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)
        mock_backend.execute_command.return_value = ProjectExecutionResult(
            status=ExecutionStatus.FAIL,
            stdout="",
            stderr="Persistent unrecoverable error",
            exit_code=1,
            execution_time=0.1
        )
        service.get_backend.return_value = mock_backend

        mock_debug_agent = MagicMock()
        mock_debug_agent.diagnose_and_repair.return_value = DebugResult(
            diagnosis="Persistent bug",
            root_cause="Cannot fix",
            error_type="RuntimeError",
            suggested_fix="Try again",
            changes={"main.py": "# attempted fix\n"},
            confidence=0.5
        )

        engine = CIPipelineEngine(
            execution_service=service,
            debug_agent=mock_debug_agent,
            history_store=clean_history_store
        )
        files = {"main.py": "print(1/0)\n"}

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_max_retry",
            config=CIConfig(max_repair_attempts=3)
        )

        assert result.status == CIOverallStatus.FAILED.value
        assert result.repair_attempts == 3
        assert mock_debug_agent.diagnose_and_repair.call_count == 3

    # -------------------------------------------------------------------------
    # 11. Docker Execution and Fallback Handling
    # -------------------------------------------------------------------------
    def test_docker_execution_and_fallback(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_docker_backend = MagicMock(spec=DockerExecutionBackend)
        mock_docker_backend.execute_command.return_value = ProjectExecutionResult(
            status=ExecutionStatus.PASS,
            stdout="Executed inside isolated Docker container",
            stderr="",
            exit_code=0,
            execution_time=0.88
        )
        service.get_backend.return_value = mock_docker_backend

        engine = CIPipelineEngine(
            execution_service=service,
            history_store=clean_history_store
        )
        files = {
            "requirements.txt": "fastapi>=0.100.0\n",
            "main.py": "print('running inside docker')\n"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_docker_run",
            config=CIConfig(docker_enabled=True, execution_backend="docker", max_repair_attempts=0)
        )

        assert result.status == CIOverallStatus.PASSED.value
        assert result.backend_used == "docker"
        service.get_backend.assert_called_with(backend_name="docker")

    # -------------------------------------------------------------------------
    # 12. Successful Automated Self-Repair Loop
    # -------------------------------------------------------------------------
    def test_successful_automated_self_repair(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)

        has_failed = [False]

        def dynamic_exec(*args, **kwargs):
            cmd = kwargs.get("command") or (args[0] if args else [])
            cmd_str = " ".join(cmd)
            # Fail on first test execution, pass after repair
            if "pytest" in cmd_str:
                if not has_failed[0]:
                    has_failed[0] = True
                    return ProjectExecutionResult(
                        status=ExecutionStatus.FAIL,
                        stdout="FAILED test_calc.py - AssertionError: 2 != 3",
                        stderr="",
                        exit_code=1,
                        execution_time=0.15
                    )
            return ProjectExecutionResult(
                status=ExecutionStatus.PASS,
                stdout="3 passed in 0.05s",
                stderr="",
                exit_code=0,
                execution_time=0.1
            )

        mock_backend.execute_command.side_effect = dynamic_exec
        service.get_backend.return_value = mock_backend

        mock_debug_agent = MagicMock()
        mock_debug_agent.diagnose_and_repair.return_value = DebugResult(
            diagnosis="Calculator formula off-by-one",
            root_cause="Return value was incorrect",
            error_type="AssertionError",
            suggested_fix="Fix return expression to a + b",
            changes={"main.py": "def calc(a, b): return a + b\n"},
            confidence=0.98
        )

        engine = CIPipelineEngine(
            execution_service=service,
            debug_agent=mock_debug_agent,
            history_store=clean_history_store
        )
        files = {
            "main.py": "def calc(a, b): return a + b + 1\n",
            "tests/test_calc.py": "from main import calc\ndef test_calc(): assert calc(1, 1) == 2\n"
        }

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_self_heal",
            config=CIConfig(max_repair_attempts=2)
        )

        assert result.status == CIOverallStatus.PASSED.value
        assert result.repair_attempts == 1
        assert len(result.applied_repairs) == 1
        assert "main.py" in result.files_modified
        assert result.applied_repairs[0]["diagnosis"] == "Calculator formula off-by-one"

    # -------------------------------------------------------------------------
    # 13. Failed Automated Repair Loop
    # -------------------------------------------------------------------------
    def test_failed_automated_repair_exhausted(self, clean_history_store):
        service = MagicMock(spec=ExecutionService)
        mock_backend = MagicMock(spec=ExecutionBackend)
        mock_backend.execute_command.return_value = ProjectExecutionResult(
            status=ExecutionStatus.FAIL,
            stdout="",
            stderr="Unsolvable deadlock",
            exit_code=1,
            execution_time=0.1
        )
        service.get_backend.return_value = mock_backend

        mock_debug_agent = MagicMock()
        mock_debug_agent.diagnose_and_repair.return_value = DebugResult(
            diagnosis="Deadlock remains",
            root_cause="Unknown",
            error_type="FatalError",
            suggested_fix="Patch code",
            changes={"main.py": "# modified but still broken\n"},
            confidence=0.3
        )

        engine = CIPipelineEngine(
            execution_service=service,
            debug_agent=mock_debug_agent,
            history_store=clean_history_store
        )
        files = {"main.py": "print('broken')\n"}

        result = engine.execute_pipeline(
            files_manifest=files,
            project_id="test_fail_repair",
            config=CIConfig(max_repair_attempts=2)
        )

        assert result.status == CIOverallStatus.FAILED.value
        assert result.repair_attempts == 2

    # -------------------------------------------------------------------------
    # 14. GitHub Actions Workflow Generation
    # -------------------------------------------------------------------------
    def test_github_actions_generation_python_and_node(self):
        generator = GitHubActionsWorkflowGenerator()

        # Python with requirements.txt
        python_files = {
            "requirements.txt": "fastapi\nuvicorn\npytest\n",
            "main.py": "print('hello')"
        }
        py_yaml = generator.generate_workflow(python_files, project_name="python-api")
        assert "name: AIForge CI - python-api" in py_yaml
        assert "actions/setup-python" in py_yaml
        assert "pip install" in py_yaml
        assert "pytest" in py_yaml
        assert "ruff" in py_yaml or "flake8" in py_yaml
        assert "bandit" in py_yaml

        # Node / React with package.json
        node_files = {
            "package.json": '{"name": "vite-dashboard", "scripts": {"build": "vite build", "test": "vitest", "lint": "eslint ."}}',
            "vite.config.js": "export default {}"
        }
        node_yaml = generator.generate_workflow(node_files, project_name="vite-dashboard")
        assert "name: AIForge CI - vite-dashboard" in node_yaml
        assert "actions/setup-node" in node_yaml
        assert "npm ci" in node_yaml or "npm install" in node_yaml
        assert "npm run build" in node_yaml
        assert "npm test" in node_yaml
        assert "npm run lint" in node_yaml

    # -------------------------------------------------------------------------
    # 15. Project-Type Detection Integration
    # -------------------------------------------------------------------------
    def test_project_type_detection_integration(self):
        detector = ProjectDetector()

        # Python FastAPI
        py_res = detector.detect({"requirements.txt": "fastapi\n", "main.py": "app = FastAPI()"})
        assert py_res.language == "python"

        # Python pyproject.toml
        pyproj_res = detector.detect({"pyproject.toml": "[tool.poetry]\nname='demo'"})
        assert pyproj_res.language == "python"

        # Node.js
        node_res = detector.detect({"package.json": '{"dependencies": {"express": "^4.18.0"}}'})
        assert node_res.language == "javascript" or node_res.language == "node"

        # React / Vite
        vite_res = detector.detect({"package.json": '{"dependencies": {"react": "^18.0.0"}}', "vite.config.js": ""})
        assert "react" in str(vite_res.framework).lower() or "vite" in str(vite_res.framework).lower()

    # -------------------------------------------------------------------------
    # 16. CI Pipeline History Persistence and Retrieval
    # -------------------------------------------------------------------------
    def test_ci_history_store(self, tmp_path):
        store = CIHistoryStore(storage_path=tmp_path / "runs.json")

        sample_res = CIPipelineResult(
            run_id="run_101",
            project_id="proj_alpha",
            project_type="python:fastapi",
            status="passed",
            build={"status": "passed", "exit_code": 0},
            tests={"status": "passed", "exit_code": 0},
            lint={"status": "passed", "exit_code": 0},
            security={"status": "passed", "exit_code": 0},
            dependencies={"status": "passed", "exit_code": 0},
            repair_attempts=1,
            duration=12.4
        )

        store.save_run(sample_res)

        # Retrieve runs by project
        runs = store.get_runs(project_id="proj_alpha")
        assert len(runs) == 1
        assert runs[0].run_id == "run_101"
        assert runs[0].status == "passed"
        assert runs[0].repair_attempts == 1

        # Retrieve specific run
        run_item = store.get_run_by_id("run_101")
        assert run_item is not None
        assert run_item.project_id == "proj_alpha"

        # Verify disk persistence
        store2 = CIHistoryStore(storage_path=tmp_path / "runs.json")
        runs2 = store2.get_runs(project_id="proj_alpha")
        assert len(runs2) == 1
        assert runs2[0].run_id == "run_101"
