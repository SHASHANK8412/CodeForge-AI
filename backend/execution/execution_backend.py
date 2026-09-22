"""
AIForge Execution Backends
=========================
Modular execution backend abstractions:
- ExecutionBackend: Abstract base class
- LocalExecutionBackend: Subprocess-based local execution in isolated temp workspace
- DockerExecutionBackend: Isolated Docker container execution with memory/cpu caps,
  network isolation, and automatic container cleanup.
"""

import os
import sys
import time
import uuid
import shutil
import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.execution.models import (
    ExecutionStatus,
    ProjectExecutionResult,
    AutonomousValidationConfig,
)
from backend import config as app_config

_logger = logging.getLogger("aiforge.execution.backend")


class ExecutionBackend(ABC):
    """
    Abstract Base Class for project execution sandboxes.
    """

    @abstractmethod
    def execute_command(
        self,
        command: List[str],
        cwd: str,
        timeout_seconds: float,
        max_output_bytes: int,
        custom_env: Optional[Dict[str, str]] = None,
        project_type: Optional[str] = None
    ) -> ProjectExecutionResult:
        """
        Executes a command within the isolated backend environment.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleans up any allocated backend resources (containers, processes, temp files).
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Returns True if the execution backend runtime is available on the host system.
        """
        pass


class LocalExecutionBackend(ExecutionBackend):
    """
    Local Subprocess Execution Backend.
    Executes commands within a controlled temporary workspace on the host with
    scrubbed environment variables, strict timeouts, and output size caps.
    """

    def __init__(self):
        self.sensitive_patterns = {
            "AWS_", "GITHUB_", "DATABASE_", "POSTGRES_", "REDIS_", "JWT_",
            "SECRET", "PASSWORD", "KEY", "TOKEN", "API_KEY", "OPENAI_", "ANTHROPIC_"
        }

    def is_available(self) -> bool:
        return True

    def _build_sanitized_environment(self, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Builds an isolated environment stripping host secrets and sensitive keys."""
        safe_env = {}
        allowed_system_keys = {
            "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
            "HOME", "USERPROFILE", "LANG", "LC_ALL", "PATHEXT", "PYTHONPATH"
        }
        for k, v in os.environ.items():
            k_upper = k.upper()
            if any(sens in k_upper for sens in self.sensitive_patterns):
                continue
            if k_upper in allowed_system_keys or k_upper.startswith("PYTHON") or k_upper.startswith("NODE"):
                safe_env[k] = v

        safe_env["AI_FORGE_SANDBOX"] = "1"
        safe_env["PYTHONUNBUFFERED"] = "1"
        safe_env["CI"] = "true"

        if custom_env:
            for ck, cv in custom_env.items():
                if not any(sens in ck.upper() for sens in self.sensitive_patterns):
                    safe_env[ck] = cv

        return safe_env

    def execute_command(
        self,
        command: List[str],
        cwd: str,
        timeout_seconds: float,
        max_output_bytes: int,
        custom_env: Optional[Dict[str, str]] = None,
        project_type: Optional[str] = None
    ) -> ProjectExecutionResult:
        if not command:
            return ProjectExecutionResult(
                status=ExecutionStatus.UNSUPPORTED,
                exit_code=-1,
                command_executed="",
                stderr="No command specified for execution.",
                backend_used="local"
            )

        cmd_str = " ".join(command)
        start_time = time.perf_counter()

        cwd_path = Path(cwd).resolve()
        if not cwd_path.exists():
            return ProjectExecutionResult(
                status=ExecutionStatus.INFRASTRUCTURE_ERROR,
                exit_code=-1,
                command_executed=cmd_str,
                stderr=f"Sandbox working directory '{cwd}' does not exist.",
                backend_used="local"
            )

        env = self._build_sanitized_environment(custom_env)
        env["PYTHONPATH"] = str(cwd_path)

        try:
            proc = subprocess.run(
                command,
                cwd=str(cwd_path),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
                stdin=subprocess.DEVNULL,
                shell=False
            )
            elapsed = time.perf_counter() - start_time
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""

            if len(stdout_text) > max_output_bytes:
                stdout_text = stdout_text[:max_output_bytes] + "\n[OUTPUT_LIMIT_EXCEEDED]"

            if len(stderr_text) > max_output_bytes:
                stderr_text = stderr_text[:max_output_bytes] + "\n[OUTPUT_LIMIT_EXCEEDED]"

            status = ExecutionStatus.PASS if proc.returncode == 0 else ExecutionStatus.FAIL

            return ProjectExecutionResult(
                status=status,
                exit_code=proc.returncode,
                command_executed=cmd_str,
                stdout=stdout_text,
                stderr=stderr_text,
                execution_duration=round(elapsed, 3),
                duration_ms=round(elapsed * 1000.0, 2),
                timed_out=False,
                backend_used="local"
            )

        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - start_time
            stdout_out = exc.stdout or ""
            stderr_out = exc.stderr or ""
            if isinstance(stdout_out, bytes):
                stdout_out = stdout_out.decode("utf-8", errors="replace")
            if isinstance(stderr_out, bytes):
                stderr_out = stderr_out.decode("utf-8", errors="replace")

            return ProjectExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                exit_code=-1,
                command_executed=cmd_str,
                stdout=stdout_out,
                stderr=f"Execution timed out after {timeout_seconds} seconds.\n{stderr_out}".strip(),
                execution_duration=round(elapsed, 3),
                duration_ms=round(elapsed * 1000.0, 2),
                timed_out=True,
                backend_used="local"
            )

        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            return ProjectExecutionResult(
                status=ExecutionStatus.INFRASTRUCTURE_ERROR,
                exit_code=-1,
                command_executed=cmd_str,
                stdout="",
                stderr=f"Execution failed with unexpected system error: {str(exc)}",
                execution_duration=round(elapsed, 3),
                duration_ms=round(elapsed * 1000.0, 2),
                timed_out=False,
                backend_used="local"
            )

    def cleanup(self) -> None:
        """Local subprocesses are managed via subprocess.run context and finish automatically."""
        pass


class DockerExecutionBackend(ExecutionBackend):
    """
    Docker Isolated Container Execution Backend.
    Executes commands inside ephemeral, strictly bounded Docker containers:
    - Mounts ONLY the generated project workspace (`/workspace`)
    - Enforces memory limit (e.g. 512m) and CPU limit (e.g. 1.0)
    - Enforces network mode (`--network none` by default for zero exfiltration)
    - Enforces execution timeout with guaranteed container termination & removal
    - Strips host secrets, tokens, keys, and credentials
    - Selects appropriate image per project type (Python, Node.js, React/Vite)
    - Automatically cleans up container and resources after execution.
    """

    IMAGE_PYTHON = "python:3.11-slim"
    IMAGE_NODE = "node:20-slim"

    def __init__(
        self,
        memory_limit: Optional[str] = None,
        cpu_limit: Optional[float] = None,
        network_mode: Optional[str] = None,
        default_image: Optional[str] = None,
        docker_cmd_runner: Optional[Any] = None
    ):
        self.memory_limit = memory_limit or app_config.MEMORY_LIMIT
        self.cpu_limit = cpu_limit if cpu_limit is not None else app_config.CPU_LIMIT
        self.network_mode = network_mode or app_config.NETWORK_MODE
        self.default_image = default_image
        self._cmd_runner = docker_cmd_runner or subprocess.run
        self.active_containers: List[str] = []

        self.sensitive_patterns = {
            "AWS_", "GITHUB_", "DATABASE_", "POSTGRES_", "REDIS_", "JWT_",
            "SECRET", "PASSWORD", "KEY", "TOKEN", "API_KEY", "OPENAI_", "ANTHROPIC_"
        }

    def is_available(self) -> bool:
        """Checks if Docker binary is on PATH and daemon responds."""
        docker_bin = shutil.which("docker")
        if not docker_bin:
            return False
        try:
            res = self._cmd_runner(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return res.returncode == 0
        except Exception:
            return False

    def select_docker_image(self, project_type: Optional[str] = None) -> str:
        """Determines appropriate container base image from project type."""
        if self.default_image:
            return self.default_image

        pt = (project_type or "").lower()
        if "node" in pt or "react" in pt or "javascript" in pt or "typescript" in pt or "vite" in pt:
            return self.IMAGE_NODE
        return self.IMAGE_PYTHON

    def _build_docker_env_flags(self, custom_env: Optional[Dict[str, str]] = None) -> List[str]:
        """Builds -e flags for Docker, allowing safe variables while scrubbing sensitive host keys."""
        flags = [
            "-e", "AI_FORGE_SANDBOX=1",
            "-e", "PYTHONUNBUFFERED=1",
            "-e", "CI=true"
        ]
        if custom_env:
            for k, v in custom_env.items():
                if not any(sens in k.upper() for sens in self.sensitive_patterns):
                    flags.extend(["-e", f"{k}={v}"])
        return flags

    def execute_command(
        self,
        command: List[str],
        cwd: str,
        timeout_seconds: float,
        max_output_bytes: int,
        custom_env: Optional[Dict[str, str]] = None,
        project_type: Optional[str] = None
    ) -> ProjectExecutionResult:
        if not command:
            return ProjectExecutionResult(
                status=ExecutionStatus.UNSUPPORTED,
                exit_code=-1,
                command_executed="",
                stderr="No command specified for execution.",
                backend_used="docker"
            )

        cmd_str = " ".join(command)
        start_time = time.perf_counter()

        cwd_path = Path(cwd).resolve()
        if not cwd_path.exists():
            return ProjectExecutionResult(
                status=ExecutionStatus.INFRASTRUCTURE_ERROR,
                exit_code=-1,
                command_executed=cmd_str,
                stderr=f"Sandbox working directory '{cwd}' does not exist.",
                backend_used="docker"
            )

        container_id = f"aiforge_exec_{uuid.uuid4().hex[:12]}"
        self.active_containers.append(container_id)

        image = self.select_docker_image(project_type)
        mount_path = str(cwd_path).replace("\\", "/")

        # Adjust command for container environment if needed (e.g. replace host python exe with python)
        adjusted_command = list(command)
        if adjusted_command and ("python.exe" in adjusted_command[0].lower() or adjusted_command[0] == sys.executable):
            adjusted_command[0] = "python"
        elif adjusted_command and ("npm.cmd" in adjusted_command[0].lower() or "npm" in adjusted_command[0].lower()):
            adjusted_command[0] = "npm"
        elif adjusted_command and ("node.exe" in adjusted_command[0].lower() or "node" in adjusted_command[0].lower()):
            adjusted_command[0] = "node"

        docker_cmd = [
            "docker", "run",
            "--name", container_id,
            "--rm",
            "-v", f"{mount_path}:/workspace:rw",
            "-w", "/workspace",
            "--network", self.network_mode,
            "--memory", str(self.memory_limit),
            "--cpus", str(self.cpu_limit),
            "--security-opt", "no-new-privileges",
        ]
        docker_cmd.extend(self._build_docker_env_flags(custom_env))
        docker_cmd.append(image)
        docker_cmd.extend(adjusted_command)

        try:
            proc = self._cmd_runner(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                stdin=subprocess.DEVNULL
            )
            elapsed = time.perf_counter() - start_time
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""

            if len(stdout_text) > max_output_bytes:
                stdout_text = stdout_text[:max_output_bytes] + "\n[OUTPUT_LIMIT_EXCEEDED]"
            if len(stderr_text) > max_output_bytes:
                stderr_text = stderr_text[:max_output_bytes] + "\n[OUTPUT_LIMIT_EXCEEDED]"

            status = ExecutionStatus.PASS if proc.returncode == 0 else ExecutionStatus.FAIL

            return ProjectExecutionResult(
                status=status,
                exit_code=proc.returncode,
                command_executed=cmd_str,
                stdout=stdout_text,
                stderr=stderr_text,
                execution_duration=round(elapsed, 3),
                duration_ms=round(elapsed * 1000.0, 2),
                timed_out=False,
                container_id=container_id,
                backend_used="docker"
            )

        except subprocess.TimeoutExpired as exc:
            elapsed = time.perf_counter() - start_time
            self._force_remove_container(container_id)

            stdout_out = exc.stdout or ""
            stderr_out = exc.stderr or ""
            if isinstance(stdout_out, bytes):
                stdout_out = stdout_out.decode("utf-8", errors="replace")
            if isinstance(stderr_out, bytes):
                stderr_out = stderr_out.decode("utf-8", errors="replace")

            return ProjectExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                exit_code=-1,
                command_executed=cmd_str,
                stdout=stdout_out,
                stderr=f"Docker execution timed out after {timeout_seconds} seconds.\n{stderr_out}".strip(),
                execution_duration=round(elapsed, 3),
                duration_ms=round(elapsed * 1000.0, 2),
                timed_out=True,
                container_id=container_id,
                backend_used="docker"
            )

        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            self._force_remove_container(container_id)
            return ProjectExecutionResult(
                status=ExecutionStatus.INFRASTRUCTURE_ERROR,
                exit_code=-1,
                command_executed=cmd_str,
                stdout="",
                stderr=f"Docker container execution error: {str(exc)}",
                execution_duration=round(elapsed, 3),
                duration_ms=round(elapsed * 1000.0, 2),
                timed_out=False,
                container_id=container_id,
                backend_used="docker"
            )

        finally:
            if container_id in self.active_containers:
                self.active_containers.remove(container_id)

    def _force_remove_container(self, container_id: str) -> None:
        """Kills and removes container if still running."""
        try:
            self._cmd_runner(
                ["docker", "rm", "-f", container_id],
                capture_output=True,
                text=True,
                timeout=5
            )
        except Exception as e:
            _logger.debug(f"Container cleanup notice: {e}")

    def cleanup(self) -> None:
        """Cleans up all tracked active containers."""
        for cid in list(self.active_containers):
            self._force_remove_container(cid)
            if cid in self.active_containers:
                self.active_containers.remove(cid)
