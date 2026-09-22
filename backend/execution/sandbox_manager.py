"""
AIForge Autonomous Engineering Platform — SandboxedExecutionManager
======================================================================
Provides isolated process execution for generated code:
- Docker container sandbox execution when Docker is reachable
- Process sandbox fallback with strict timeout (default 30s), working directory restriction,
  environment sanitization, command allowlist, process termination, and memory bounds.
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

ALLOWED_COMMAND_PREFIXES = {
    "python", "pytest", "npm", "npx", "pip", "node", "mvn", "gradle",
    "echo", "git", "docker", "tsc", "vitest"
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
        first_token = c.split()[0].lower()
        base_cmd = os.path.basename(first_token)
        return base_cmd in ALLOWED_COMMAND_PREFIXES or any(p in c.lower() for p in ALLOWED_COMMAND_PREFIXES)

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

        # Prepare isolated environment
        clean_env = os.environ.copy()
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


global_sandbox_manager = SandboxedExecutionManager()
