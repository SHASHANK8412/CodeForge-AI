"""
AIForge Secure Sandbox Executor
===============================
Runs untrusted generated code in a throwaway Docker container: no network, non-root, no
capabilities, read-only filesystem, memory/CPU/process limits, timeout, output truncation.
Without Docker the code is not run, unless AIFORGE_TEST_SANDBOX=local explicitly allows a host
subprocess (credentials stripped from its environment) - meant for AIForge's own test suite.
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
        limits: Optional[ExecutionLimits] = None,
        extra_pythonpath: Optional[List[str]] = None
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
            return self._run_subprocess(work_dir, main_file_path, language, command_override, execution_type, active_limits, start_time, extra_pythonpath)

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

            return self._run_subprocess(tmpdir, main_file_path or os.path.join(tmpdir, "main.py"), language, command_override, execution_type, active_limits, start_time, extra_pythonpath)

    def _run_subprocess(
        self,
        work_dir: str,
        main_file_path: str,
        language: str,
        command_override: Optional[List[str]],
        execution_type: ExecutionType,
        active_limits: ExecutionLimits,
        start_time: float,
        extra_pythonpath: Optional[List[str]] = None
    ) -> ExecutionResult:
        # Model-written code runs in a container (no network, no capabilities, non-root, resource
        # limits). Without Docker it is not run, unless AIFORGE_TEST_SANDBOX=local allows the host.
        # compileall only byte-compiles and never executes the code, so it may run here.
        from backend.execution.docker_test_sandbox import not_run_result, sandbox_mode, should_use_docker
        compile_only = bool(command_override) and "compileall" in command_override
        if sandbox_mode() != "local" and not compile_only:
            if command_override or not should_use_docker():
                res = not_run_result(language)
                res.execution_type = execution_type.value if hasattr(execution_type, "value") else str(execution_type)
                return res
            return self._run_in_docker(work_dir, main_file_path, language, execution_type, active_limits, start_time)

        cmd = self._resolve_trusted_command(language, work_dir, main_file_path, command_override)
        isolated_env = self._build_isolated_environment()
        isolated_env["PYTHONPATH"] = os.pathsep.join([os.path.abspath(work_dir)] + list(extra_pythonpath or []))

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


    def _run_in_docker(
        self,
        work_dir: str,
        main_file_path: str,
        language: str,
        execution_type: ExecutionType,
        limits: ExecutionLimits,
        start_time: float,
    ) -> ExecutionResult:
        """One throwaway container per run; the code folder is mounted read-only."""
        import uuid
        from backend.execution.docker_test_sandbox import IMAGE, NODE_IMAGE, docker_env, docker_exe
        etype = execution_type.value if hasattr(execution_type, "value") else str(execution_type)
        lang = language.lower()
        rel = os.path.relpath(main_file_path, work_dir).replace("\\", "/")
        if lang == "python":
            image, cmd = IMAGE, ["python", rel]
        elif lang in ("javascript", "node", "js"):
            image, cmd = NODE_IMAGE, ["node", rel]
        else:
            return ExecutionResult(status=ExecutionStatus.UNSUPPORTED, exit_code=-1, language=language,
                                   execution_type=etype, stderr=f"The sandbox runs Python and JavaScript, not {language}.")
        name = f"aiforge_exec_{uuid.uuid4().hex[:12]}"
        docker = docker_exe() or "docker"
        argv = [
            docker, "run", "--rm", "--name", name, "--network", "none", "--user", "1000:1000",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64",
            "--memory", f"{limits.memory_mb}m", "--cpus", str(limits.cpu_count),
            "--read-only", "--tmpfs", "/tmp:rw,size=64m", "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-v", f"{os.path.abspath(work_dir)}:/work:ro", "-w", "/work", image,
            # The program's own limit is enforced inside the container (exit 124); the outer
            # timeout only adds a margin for container start-up.
            "timeout", "-k", "1s", f"{max(1, int(limits.timeout_seconds + 0.999))}s", *cmd,
        ]
        timed_out = False
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=limits.timeout_seconds + 20, env=docker_env())
            timed_out = proc.returncode == 124
        except subprocess.TimeoutExpired:
            subprocess.run([docker, "rm", "-f", name], capture_output=True, env=docker_env())
            timed_out = True
        if timed_out:
            return ExecutionResult(status=ExecutionStatus.TIMEOUT, exit_code=-1, timed_out=True, language=language,
                                   execution_type=etype, stderr=f"Execution timed out after {limits.timeout_seconds} seconds.",
                                   duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2))
        out, err = proc.stdout or "", proc.stderr or ""
        truncated = len(out) > limits.max_output_bytes or len(err) > limits.max_output_bytes
        status = ExecutionStatus.PASS if proc.returncode == 0 else ExecutionStatus.FAIL
        if proc.returncode == 125:   # docker itself failed (image, daemon), not the program
            status = ExecutionStatus.INFRASTRUCTURE_ERROR
        elif proc.returncode == 137:  # killed: out of memory
            status = ExecutionStatus.RESOURCE_LIMIT
        elif proc.returncode != 0 and "SyntaxError" in err:
            status = ExecutionStatus.COMPILE_ERROR
        return ExecutionResult(
            status=status, exit_code=proc.returncode, stdout=out[:limits.max_output_bytes],
            stderr=err[:limits.max_output_bytes], output_truncated=truncated, timed_out=False,
            duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2), language=language, execution_type=etype,
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

        return safe_env


global_sandbox_executor = SandboxExecutor()
