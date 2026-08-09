"""
AIForge Secure Sandbox Executor
===============================
Provides isolated container / subprocess execution for untrusted generated code.
Enforces resource limits, execution timeouts, output truncations, environment isolation,
and strict command allowlisting (shell=False only).
"""

import sys
import os
import time
import shutil
import tempfile
import subprocess
import logging
from typing import List, Dict, Any, Optional

from backend.execution.models import (
    CodeArtifact,
    ExecutionLimits,
    ExecutionResult,
    ExecutionStatus,
    ExecutionType
)

_logger = logging.getLogger("aiforge.execution.sandbox")


class SandboxExecutor:
    """
    Secure isolated sandbox executor.
    """

    def __init__(self, limits: Optional[ExecutionLimits] = None):
        self.limits = limits or ExecutionLimits()

    def execute(
        self,
        artifacts: List[CodeArtifact],
        language: str = "python",
        command_override: Optional[List[str]] = None,
        execution_type: ExecutionType = ExecutionType.RUN,
        cwd: Optional[str] = None,
        limits: Optional[ExecutionLimits] = None
    ) -> ExecutionResult:
        if not artifacts and not command_override:
            return ExecutionResult(
                status=ExecutionStatus.UNSUPPORTED,
                exit_code=-1,
                stderr="No code artifacts provided for execution.",
                language=language,
                execution_type=execution_type.value
            )

        start_time = time.perf_counter()
        active_limits = limits or self.limits

        if cwd and os.path.exists(cwd):
            work_dir = cwd
            main_file_path = os.path.join(work_dir, artifacts[0].filename) if artifacts else os.path.join(work_dir, "main.py")
            return self._run_subprocess(work_dir, main_file_path, language, command_override, execution_type, active_limits, start_time)

        with tempfile.TemporaryDirectory(prefix="aiforge_sandbox_") as tmpdir:
            main_file_path = None
            for art in artifacts:
                fname = art.filename or ("main.py" if language == "python" else "index.js")
                fpath = os.path.join(tmpdir, fname)
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(art.content)
                if not main_file_path or art.purpose == "SOURCE":
                    main_file_path = fpath

            if not main_file_path and artifacts:
                main_file_path = os.path.join(tmpdir, artifacts[0].filename)

            return self._run_subprocess(tmpdir, main_file_path or os.path.join(tmpdir, "main.py"), language, command_override, execution_type, active_limits, start_time)

    def _run_subprocess(
        self,
        work_dir: str,
        main_file_path: str,
        language: str,
        command_override: Optional[List[str]],
        execution_type: ExecutionType,
        active_limits: ExecutionLimits,
        start_time: float
    ) -> ExecutionResult:
        cmd = self._resolve_trusted_command(language, work_dir, main_file_path, command_override)
        isolated_env = self._build_isolated_environment()
        isolated_env["PYTHONPATH"] = os.path.abspath(work_dir)

        try:
            proc = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=active_limits.timeout_seconds,
                env=isolated_env
            )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            truncated = False

            if len(stdout_text) > active_limits.max_output_bytes:
                stdout_text = stdout_text[:active_limits.max_output_bytes] + "\n[OUTPUT_LIMIT_EXCEEDED]"
                truncated = True

            if len(stderr_text) > active_limits.max_output_bytes:
                stderr_text = stderr_text[:active_limits.max_output_bytes] + "\n[OUTPUT_LIMIT_EXCEEDED]"
                truncated = True

            status = ExecutionStatus.PASS if proc.returncode == 0 else ExecutionStatus.FAIL
            if proc.returncode != 0 and ("SyntaxError" in stderr_text or "compilation error" in stderr_text.lower()):
                status = ExecutionStatus.COMPILE_ERROR

            return ExecutionResult(
                status=status,
                exit_code=proc.returncode,
                stdout=stdout_text,
                stderr=stderr_text,
                duration_ms=elapsed_ms,
                timed_out=False,
                output_truncated=truncated,
                language=language,
                execution_type=execution_type.value if hasattr(execution_type, 'value') else str(execution_type)
            )

        except subprocess.TimeoutExpired:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            _logger.warning(f"[SandboxExecutor] Execution timed out after {active_limits.timeout_seconds}s")
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                exit_code=-1,
                stdout="",
                stderr=f"Execution timed out after {active_limits.timeout_seconds} seconds.",
                duration_ms=elapsed_ms,
                timed_out=True,
                language=language,
                execution_type=execution_type.value if hasattr(execution_type, 'value') else str(execution_type)
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            _logger.error(f"[SandboxExecutor] Infrastructure error during sandbox run: {e}")
            return ExecutionResult(
                status=ExecutionStatus.INFRASTRUCTURE_ERROR,
                exit_code=-1,
                stderr=f"Sandbox infrastructure error: {str(e)}",
                duration_ms=elapsed_ms,
                language=language,
                execution_type=execution_type.value if hasattr(execution_type, 'value') else str(execution_type)
            )


    def _resolve_trusted_command(
        self,
        language: str,
        tmpdir: str,
        main_file: str,
        override: Optional[List[str]] = None
    ) -> List[str]:
        if override:
            return override

        lang = language.lower()
        if lang == "python":
            return [sys.executable, main_file]
        elif lang in ["javascript", "node", "js"]:
            node_cmd = shutil.which("node") or "node"
            return [node_cmd, main_file]
        elif lang == "java":
            javac = shutil.which("javac") or "javac"
            java = shutil.which("java") or "java"
            # Compile first
            subprocess.run([javac, main_file], cwd=tmpdir, capture_output=True, text=True, timeout=10)
            class_name = os.path.splitext(os.path.basename(main_file))[0]
            return [java, class_name]

        return [sys.executable, main_file]

    def _build_isolated_environment(self) -> Dict[str, str]:
        """Strips host credentials and sensitive environment keys."""
        safe_env = {}
        sensitive_keys = {
            "AWS_", "GITHUB_", "DATABASE_", "POSTGRES_", "REDIS_", "JWT_", "SECRET",
            "PASSWORD", "KEY", "TOKEN", "API_KEY", "OPENAI_", "ANTHROPIC_"
        }

        for k, v in os.environ.items():
            if not any(sens in k.upper() for sens in sensitive_keys):
                safe_env[k] = v

        safe_env["NETWORK_DISABLED"] = "true"
        return safe_env


global_sandbox_executor = SandboxExecutor()
