"""
Unit and Integration Tests for AIForge Docker-Based Isolated Code Execution Sandbox
==================================================================================
Covers:
1. Docker backend initialization
2. Successful Python execution
3. Successful Node.js execution
4. Test failure handling
5. Execution timeout enforcement
6. Container cleanup guarantees
7. Invalid project handling
8. Dependency installation failure
9. Resource-limit configuration
10. Backend selection logic
"""

import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from backend.execution.models import (
    ExecutionStatus,
    PipelineStep,
    AutonomousValidationConfig,
    ProjectExecutionResult,
)
from backend.execution.execution_backend import (
    ExecutionBackend,
    LocalExecutionBackend,
    DockerExecutionBackend,
)
from backend.execution.execution_service import ExecutionService
from backend.execution.autonomous_execution_engine import AutonomousExecutionEngine


class TestDockerExecutionBackend:
    """Test suite for DockerExecutionBackend."""

    def test_docker_backend_initialization(self):
        """1. Verify Docker backend initialization with defaults and custom parameters."""
        backend = DockerExecutionBackend(
            memory_limit="1g",
            cpu_limit=2.0,
            network_mode="bridge"
        )
        assert backend.memory_limit == "1g"
        assert backend.cpu_limit == 2.0
        assert backend.network_mode == "bridge"
        assert backend.select_docker_image("python:fastapi") == DockerExecutionBackend.IMAGE_PYTHON
        assert backend.select_docker_image("javascript:react") == DockerExecutionBackend.IMAGE_NODE
        assert backend.select_docker_image("node:express") == DockerExecutionBackend.IMAGE_NODE

    def test_successful_python_execution(self):
        """2. Verify successful Python execution inside Docker container."""
        mock_runner = MagicMock()
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "================ 3 passed in 0.12s ================"
        mock_proc.stderr = ""
        mock_runner.return_value = mock_proc

        backend = DockerExecutionBackend(
            memory_limit="512m",
            cpu_limit=1.0,
            network_mode="none",
            docker_cmd_runner=mock_runner
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            res: ProjectExecutionResult = backend.execute_command(
                command=["python", "-m", "pytest"],
                cwd=tmpdir,
                timeout_seconds=15.0,
                max_output_bytes=50000,
                project_type="python"
            )

            assert res.status == ExecutionStatus.PASS
            assert res.exit_code == 0
            assert "3 passed" in res.stdout
            assert res.backend_used == "docker"
            assert res.container_id is not None
            assert res.container_id.startswith("aiforge_exec_")

            # Verify docker CLI invocation flags
            invoked_cmd = mock_runner.call_args[0][0]
            assert invoked_cmd[0] == "docker"
            assert invoked_cmd[1] == "run"
            assert "--memory" in invoked_cmd
            assert "512m" in invoked_cmd
            assert "--cpus" in invoked_cmd
            assert "1.0" in invoked_cmd
            assert "--network" in invoked_cmd
            assert "none" in invoked_cmd
            assert "--security-opt" in invoked_cmd
            assert "no-new-privileges" in invoked_cmd
            assert DockerExecutionBackend.IMAGE_PYTHON in invoked_cmd

    def test_successful_nodejs_execution(self):
        """3. Verify successful Node.js execution inside Docker container."""
        mock_runner = MagicMock()
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "✔ 4 tests passed"
        mock_proc.stderr = ""
        mock_runner.return_value = mock_proc

        backend = DockerExecutionBackend(
            docker_cmd_runner=mock_runner
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            res: ProjectExecutionResult = backend.execute_command(
                command=["npm", "test"],
                cwd=tmpdir,
                timeout_seconds=15.0,
                max_output_bytes=50000,
                project_type="javascript:node"
            )

            assert res.status == ExecutionStatus.PASS
            assert res.exit_code == 0
            assert "4 tests passed" in res.stdout
            assert res.backend_used == "docker"

            invoked_cmd = mock_runner.call_args[0][0]
            assert DockerExecutionBackend.IMAGE_NODE in invoked_cmd

    def test_docker_test_failure(self):
        """4. Verify test failure captured correctly inside Docker container."""
        mock_runner = MagicMock()
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "FAILED tests/test_calc.py::test_discount - assert 70.0 == 80.0"
        mock_proc.stderr = "AssertionError: discount mismatch"
        mock_runner.return_value = mock_proc

        backend = DockerExecutionBackend(docker_cmd_runner=mock_runner)

        with tempfile.TemporaryDirectory() as tmpdir:
            res = backend.execute_command(
                command=["python", "-m", "pytest"],
                cwd=tmpdir,
                timeout_seconds=10.0,
                max_output_bytes=50000,
                project_type="python"
            )

            assert res.status == ExecutionStatus.FAIL
            assert res.exit_code == 1
            assert "FAILED" in res.stdout
            assert "AssertionError" in res.stderr
            assert res.backend_used == "docker"

    def test_docker_execution_timeout(self):
        """5. Verify timeout enforcement and container cleanup on timeout."""
        mock_runner = MagicMock()
        mock_runner.side_effect = [
            subprocess.TimeoutExpired(cmd=["docker", "run"], timeout=5.0, stderr=b"Process hung"),
            MagicMock(returncode=0)  # For docker rm -f
        ]

        backend = DockerExecutionBackend(docker_cmd_runner=mock_runner)

        with tempfile.TemporaryDirectory() as tmpdir:
            res = backend.execute_command(
                command=["python", "infinite_loop.py"],
                cwd=tmpdir,
                timeout_seconds=5.0,
                max_output_bytes=50000,
                project_type="python"
            )

            assert res.status == ExecutionStatus.TIMEOUT
            assert res.timed_out is True
            assert res.exit_code == -1
            assert "timed out after 5.0 seconds" in res.stderr

            # Check that docker rm -f was called to kill the container
            assert mock_runner.call_count == 2
            rm_call = mock_runner.call_args_list[1][0][0]
            assert rm_call[:3] == ["docker", "rm", "-f"]

    def test_container_cleanup(self):
        """6. Verify container tracking and explicit cleanup."""
        mock_runner = MagicMock()
        backend = DockerExecutionBackend(docker_cmd_runner=mock_runner)

        backend.active_containers = ["aiforge_exec_12345", "aiforge_exec_67890"]
        backend.cleanup()

        assert len(backend.active_containers) == 0
        assert mock_runner.call_count == 2
        calls = [call[0][0] for call in mock_runner.call_args_list]
        assert ["docker", "rm", "-f", "aiforge_exec_12345"] in calls
        assert ["docker", "rm", "-f", "aiforge_exec_67890"] in calls

    def test_invalid_project_handling(self):
        """7. Verify handling of invalid project workspace or empty command."""
        backend = DockerExecutionBackend()

        # Non-existent directory
        res_bad_dir = backend.execute_command(
            command=["python", "-v"],
            cwd="C:/non_existent_folder_xyz_123",
            timeout_seconds=5.0,
            max_output_bytes=50000
        )
        assert res_bad_dir.status == ExecutionStatus.INFRASTRUCTURE_ERROR
        assert res_bad_dir.exit_code == -1

        # Empty command
        with tempfile.TemporaryDirectory() as tmpdir:
            res_empty_cmd = backend.execute_command(
                command=[],
                cwd=tmpdir,
                timeout_seconds=5.0,
                max_output_bytes=50000
            )
            assert res_empty_cmd.status == ExecutionStatus.UNSUPPORTED
            assert res_empty_cmd.exit_code == -1

    def test_dependency_installation_failure_handled(self):
        """8. Verify dependency installation failure handled gracefully in Docker."""
        mock_runner = MagicMock()

        # Dependency install fails, tests pass
        dep_proc = MagicMock(returncode=1, stdout="", stderr="Could not find a version that satisfies the requirement non_existent_pkg")
        test_proc = MagicMock(returncode=0, stdout="OK", stderr="")
        mock_runner.side_effect = [dep_proc, test_proc]

        docker_backend = DockerExecutionBackend(docker_cmd_runner=mock_runner)
        exec_service = ExecutionService(docker_backend=docker_backend)
        # Force is_available to True
        docker_backend.is_available = MagicMock(return_value=True)

        engine = AutonomousExecutionEngine(execution_service=exec_service)

        files = {
            "requirements.txt": "non_existent_pkg==99.99.99\n",
            "backend/main.py": "def test_ok(): pass\n"
        }
        cfg = AutonomousValidationConfig(
            execution_backend="docker",
            install_dependencies=True,
            max_repair_attempts=1
        )

        report = engine.execute_and_validate(files, config=cfg)
        assert report.backend_used == "docker"
        dep_steps = [s for s in report.steps if s.step == PipelineStep.INSTALLING_DEPENDENCIES]
        assert len(dep_steps) >= 1
        assert dep_steps[-1].status == "FAILED"
        assert "Could not find a version" in dep_steps[-1].stderr

    def test_resource_limit_configuration(self):
        """9. Verify custom memory, cpu, and network mode configurations passed to docker."""
        mock_runner = MagicMock()
        mock_runner.return_value = MagicMock(returncode=0, stdout="", stderr="")

        backend = DockerExecutionBackend(
            memory_limit="256m",
            cpu_limit=0.5,
            network_mode="bridge",
            docker_cmd_runner=mock_runner
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            backend.execute_command(
                command=["python", "--version"],
                cwd=tmpdir,
                timeout_seconds=10.0,
                max_output_bytes=50000,
                project_type="python"
            )

            cmd = mock_runner.call_args[0][0]
            mem_idx = cmd.index("--memory")
            assert cmd[mem_idx + 1] == "256m"

            cpu_idx = cmd.index("--cpus")
            assert cmd[cpu_idx + 1] == "0.5"

            net_idx = cmd.index("--network")
            assert cmd[net_idx + 1] == "bridge"

    def test_backend_selection(self):
        """10. Verify backend selection priority and fallback mechanics."""
        local_backend = LocalExecutionBackend()
        docker_backend = DockerExecutionBackend()

        # Mock docker availability
        docker_backend.is_available = MagicMock(return_value=True)

        service = ExecutionService(
            local_backend=local_backend,
            docker_backend=docker_backend
        )

        # 1. Explicit local
        assert isinstance(service.get_backend("local"), LocalExecutionBackend)

        # 2. Explicit docker when available
        assert isinstance(service.get_backend("docker"), DockerExecutionBackend)

        # 3. Config with execution_backend='docker'
        cfg_docker = AutonomousValidationConfig(execution_backend="docker")
        assert isinstance(service.get_backend(config=cfg_docker), DockerExecutionBackend)

        # 4. Config with docker_enabled=True
        cfg_enabled = AutonomousValidationConfig(docker_enabled=True)
        assert isinstance(service.get_backend(config=cfg_enabled), DockerExecutionBackend)

        # 5. Docker unavailable -> graceful fallback to LocalExecutionBackend
        docker_backend.is_available.return_value = False
        fallback = service.get_backend("docker", strict_docker=False)
        assert isinstance(fallback, LocalExecutionBackend)

        # 6. Strict docker requested and unavailable -> raises RuntimeError
        with pytest.raises(RuntimeError, match="Docker is unavailable"):
            service.get_backend("docker", strict_docker=True)
