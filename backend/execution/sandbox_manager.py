"""
AIForge Autonomous Engineering Platform — SandboxedExecutionManager
======================================================================
Gates execution of generated-project commands:
- command allowlist (the program itself, no shell chaining)
- byte-compiling (py_compile / compileall) runs here; it never executes the project's code
- everything else runs through the execution service's Docker backend (no network, no
  capabilities, limits), or is reported as not run when Docker is unavailable. A host subprocess
  with a scrubbed environment is used only with the explicit AIFORGE_TEST_SANDBOX=local opt-in.
"""

import os
import shlex
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.execution.sandbox")

# `docker` is not allowed: a generated command could mount the host into a container.
ALLOWED_COMMAND_PREFIXES = {
    "python", "pytest", "npm", "npx", "pip", "node", "mvn", "gradle",
    "echo", "git", "tsc", "vitest"
}


class ExecutionResult(BaseModel):
    status: str = "success"  # "success", "failed", "timeout", "security_violation"
    exit_code: int = 0
    error_type: Optional[str] = None
    error_message: str = ""
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    failed_command: str = ""
    cwd: str = ""


class SandboxedExecutionManager:
    """
    Isolated execution manager gating execution of untrusted generated code.
    """

    def __init__(self, default_timeout: int = 30) -> None:
        self.default_timeout = default_timeout

    def is_docker_available(self) -> bool:
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
            return res.returncode == 0
        except Exception:
            return False

    def is_command_allowed(self, command_str: str) -> bool:
        c = command_str.strip()
        if not c:
            return False
        # Block shell chaining operators
        if any(op in c for op in [";", "&&", "||", "|", "`", "$("]):
            return False
        # The program itself must be allowlisted ("rm -rf x # python" used to pass because the
        # text merely contained an allowed word).
        first_token = c.split()[0].lower().replace("\\", "/")
        base_cmd = os.path.splitext(os.path.basename(first_token))[0]
        return base_cmd in ALLOWED_COMMAND_PREFIXES or base_cmd in ("python3",)

    def execute_command(
        self,
        command_str: str,
        cwd: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        t_out = timeout or self.default_timeout
        start_time = time.perf_counter()

        if not self.is_command_allowed(command_str):
            _logger.warning(f"Security Warning: Command disallowed in sandbox -> '{command_str}'")
            return ExecutionResult(
                status="security_violation",
                exit_code=126,
                error_type="security_violation",
                error_message="Command failed security sandbox allowlist validation.",
                duration_ms=0.0,
                failed_command=command_str
            )

        # Host runs get no credentials (this used to pass the full environment, keys included).
        from backend.execution.execution_backend import LocalExecutionBackend
        clean_env = LocalExecutionBackend()._build_sanitized_environment()
        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["CI"] = "true"
        if env_vars:
            clean_env.update(env_vars)

        target_cwd = cwd or os.getcwd()

        # Tokenize command for safe subprocess invocation without shell=True
        try:
            cmd_args = shlex.split(command_str)
        except Exception as e:
            return ExecutionResult(
                status="failed",
                exit_code=1,
                error_type="syntax_error",
                error_message=f"Command parsing failed: {str(e)}",
                duration_ms=0.0,
                failed_command=command_str
            )

        from backend.execution.docker_test_sandbox import sandbox_mode
        program = os.path.splitext(os.path.basename(cmd_args[0].replace("\\", "/")))[0].lower() if cmd_args else ""
        compile_only = program in ("python", "python3") and cmd_args[1:3] in (["-m", "py_compile"], ["-m", "compileall"])
        if not compile_only and program != "echo" and sandbox_mode() != "local":
            return self._run_in_container(cmd_args, command_str, target_cwd, t_out, start_time)

        try:
            res = subprocess.run(
                cmd_args,
                shell=False,
                cwd=target_cwd,
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=t_out
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            success = (res.returncode == 0)

            return ExecutionResult(
                status="success" if success else "failed",
                exit_code=res.returncode,
                error_type=None if success else "runtime_error",
                error_message="" if success else res.stderr or res.stdout,
                stdout=res.stdout,
                stderr=res.stderr,
                duration_ms=elapsed_ms,
                failed_command="" if success else command_str,
                cwd=target_cwd
            )
        except subprocess.TimeoutExpired as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            _logger.error(f"Sandbox execution timed out after {t_out}s for command: '{command_str}'")
            return ExecutionResult(
                status="timeout",
                exit_code=124,
                error_type="timeout",
                error_message=f"Execution timed out after {t_out} seconds.",
                stdout=exc.stdout or "" if hasattr(exc, "stdout") else "",
                stderr=exc.stderr or "" if hasattr(exc, "stderr") else "",
                duration_ms=elapsed_ms,
                failed_command=command_str,
                cwd=target_cwd
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ExecutionResult(
                status="failed",
                exit_code=-1,
                error_type="execution_error",
                error_message=f"Subprocess execution error: {str(e)}",
                duration_ms=elapsed_ms,
                failed_command=command_str,
                cwd=target_cwd
            )


    def _run_in_container(self, cmd_args: List[str], command_str: str, cwd: str, timeout: int,
                          start_time: float) -> ExecutionResult:
        """Runs the command through the execution service's Docker backend (or reports not run)."""
        from backend.execution.execution_service import global_execution_service
        backend = global_execution_service.get_backend(backend_name="docker")
        project_type = "javascript" if os.path.basename(cmd_args[0]).lower().split(".")[0] in ("npm", "npx", "node", "tsc", "vitest") else "python"
        res = backend.execute_command(cmd_args, cwd, timeout_seconds=timeout, max_output_bytes=100_000, project_type=project_type)
        ok = res.exit_code == 0
        return ExecutionResult(
            status="success" if ok else ("timeout" if res.timed_out else "failed"),
            exit_code=res.exit_code,
            error_type=None if ok else ("timeout" if res.timed_out else
                                        "not_run" if res.backend_used == "none" else "runtime_error"),
            error_message="" if ok else (res.stderr or res.stdout),
            stdout=res.stdout,
            stderr=res.stderr,
            duration_ms=round((time.perf_counter() - start_time) * 1000, 2),
            failed_command="" if ok else command_str,
            cwd=cwd,
        )


global_sandbox_manager = SandboxedExecutionManager()
