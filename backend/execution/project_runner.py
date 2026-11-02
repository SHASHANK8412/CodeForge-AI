"""
AIForge Project Runner Service
==============================
Executes physical project builds and tests inside isolated sandbox workspaces.
Classifies error types and returns structured ExecutionResult objects.
"""

import sys
import os
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


from backend.execution.models import (
    ExecutionResult,
    ExecutionStatus,
    ExecutionLimits,
    CodeArtifact,
    ExecutionType
)
from backend.execution.sandbox_executor import global_sandbox_executor
from backend.execution.docker_sandbox import run_sandboxed, sandbox_backend

_logger = logging.getLogger("aiforge.execution.project_runner")


class ProjectRunner:
    """
    Executes real project builds and test suites on disk using SandboxExecutor.
    """

    def __init__(self, limits: Optional[ExecutionLimits] = None):
        self.limits = limits or ExecutionLimits(timeout_seconds=float(os.environ.get("AIFORGE_RUN_TIMEOUT", "60")))

    def classify_error_type(self, stderr: str, stdout: str) -> str:
        """Classifies stderr/stdout into structured error type categories."""
        combined = f"{stderr}\n{stdout}".lower()
        if "syntaxerror" in combined or "invalid syntax" in combined:
            return "SyntaxError"
        elif "importerror" in combined or "modulenotfounderror" in combined or "cannot import" in combined:
            return "ImportError"
        elif "assertionerror" in combined or "failed" in combined and "pytest" in combined:
            return "AssertionError"
        elif "timeout" in combined or "timed out" in combined:
            return "TimeoutError"
        elif "typeerror" in combined:
            return "TypeError"
        elif "nameerror" in combined:
            return "NameError"
        return "ExecutionError"

    def select_safe_command(self, project_path: Path) -> Tuple[List[str], str]:
        """
        Safely inspects project directory to select an allowed validation/build command.
        Returns (command_list, language).
        """
        if not project_path.exists():
            return [], "unknown"

        # Full-stack projects have both; the backend test suite is the stronger
        # signal, so real Python tests win over a root package.json.
        py_files = list(project_path.glob("**/*.py"))
        if any(self._is_real_test_file(p) for p in py_files) and (
                shutil.which("pytest") or sandbox_backend() == "docker"):
            # -rA prints one PASSED/FAILED line per test: the repair loop needs
            # per-test outcomes to tell an improvement from a regression.
            return [sys.executable, "-m", "pytest", "-rA"], "python"

        pkg_json_path = project_path / "package.json"
        if pkg_json_path.exists():
            npm_cmd = "npm.cmd" if sys.platform == "win32" and shutil.which("npm.cmd") else "npm"
            try:
                data = json.loads(pkg_json_path.read_text(encoding="utf-8"))
                scripts = data.get("scripts", {})
                if "build" in scripts:
                    return [npm_cmd, "run", "build"], "javascript"
                elif "test" in scripts:
                    return [npm_cmd, "test"], "javascript"
            except Exception:
                pass
            return [npm_cmd, "run", "build"], "javascript"

        # Check for Python project
        if py_files:
            # A file only counts as a test if it defines a test; placeholder files
            # like "# Pytest Integration Tests" would make pytest exit 5 (no tests).
            has_tests = any(self._is_real_test_file(p) for p in py_files)
            if has_tests and (shutil.which("pytest") or sandbox_backend() == "docker"):
                return [sys.executable, "-m", "pytest", "-rA"], "python"
            return [sys.executable, "-m", "compileall", "-e", "."], "python"

        return [], "unknown"


    @staticmethod
    def _is_real_test_file(path: Path) -> bool:
        name = path.name.lower()
        if not (name.startswith("test_") or name.endswith("_test.py")):
            return False
        try:
            return "def test" in path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False

    def _run_in_docker(self, proj_path: Path, cmd: List[str], lang: str) -> ExecutionResult:
        """Runs the validation command in the isolated Docker sandbox."""
        if lang != "python":
            return ExecutionResult(
                status=ExecutionStatus.UNSUPPORTED, exit_code=-1,
                stderr=f"Docker sandbox currently supports Python projects only (got {lang}).",
                language=lang, execution_type=ExecutionType.PROJECT_TEST.value,
            )
        # Host interpreter paths mean nothing inside the container.
        if cmd and cmd[0] == sys.executable:
            cmd = ["python", *cmd[1:]]
        if cmd[:3] == ["python", "-m", "pytest"] and "-p" not in cmd:
            cmd = cmd + ["-q", "-p", "no:cacheprovider"]
        try:
            res = run_sandboxed(str(proj_path), cmd, timeout_seconds=self.limits.timeout_seconds,
                                memory_mb=self.limits.memory_mb)
        except RuntimeError as exc:
            return ExecutionResult(
                status=ExecutionStatus.INFRASTRUCTURE_ERROR, exit_code=-1, stderr=str(exc),
                language=lang, execution_type=ExecutionType.PROJECT_TEST.value,
            )
        if res.timed_out:
            status = ExecutionStatus.TIMEOUT
        elif res.exit_code == 0:
            status = ExecutionStatus.PASS
        elif "SyntaxError" in res.stderr or "SyntaxError" in res.stdout:
            status = ExecutionStatus.COMPILE_ERROR
        else:
            status = ExecutionStatus.FAIL
        return ExecutionResult(
            status=status, exit_code=res.exit_code, stdout=res.stdout, stderr=res.stderr,
            duration_ms=res.duration_ms, timed_out=res.timed_out, language=lang,
            execution_type=ExecutionType.PROJECT_TEST.value,
        )

    def run_project(
        self,
        project_path_str: str,
        command_override: Optional[List[str]] = None
    ) -> ExecutionResult:
        """
        Executes safe validation/build command inside project directory on disk.
        """
        if not project_path_str:
            return ExecutionResult(
                status=ExecutionStatus.UNSUPPORTED,
                exit_code=-1,
                stderr="No project path provided.",
                language="unknown",
                execution_type=ExecutionType.PROJECT_TEST.value
            )

        proj_path = Path(project_path_str).resolve()
        if not proj_path.exists() or not proj_path.is_dir():
            return ExecutionResult(
                status=ExecutionStatus.UNSUPPORTED,
                exit_code=-1,
                stderr=f"Project directory '{project_path_str}' does not exist on disk.",
                language="unknown",
                execution_type=ExecutionType.PROJECT_TEST.value
            )

        cmd, lang = self.select_safe_command(proj_path)
        if command_override:
            cmd = command_override

        if not cmd:
            return ExecutionResult(
                status=ExecutionStatus.UNSUPPORTED,
                exit_code=-1,
                stderr="No safe validation command supported for this project layout.",
                language=lang,
                execution_type=ExecutionType.PROJECT_TEST.value
            )

        # "Build" = every Python source compiles. Running pytest alone can pass
        # while a module nobody imports has a SyntaxError.
        if lang == "python" and not command_override and "pytest" in cmd:
            compile_res = self._execute(proj_path, [sys.executable, "-m", "compileall", "-q", "."], lang)
            if compile_res.exit_code != 0:
                return compile_res

        return self._execute(proj_path, cmd, lang)

    def _execute(self, proj_path: Path, cmd: List[str], lang: str) -> ExecutionResult:
        _logger.info(f"ProjectRunner executing '{' '.join(cmd)}' inside '{proj_path}'...")

        if sandbox_backend() == "docker":
            res = self._run_in_docker(proj_path, cmd, lang)
            res.sandbox = "docker"
        else:
            res = self._execute_local(proj_path, cmd, lang)
            res.sandbox = "local"
        res.command = " ".join(cmd)
        return res

    def _execute_local(self, proj_path: Path, cmd: List[str], lang: str) -> ExecutionResult:

        # Create dummy artifact pointing to existing dir
        artifact = CodeArtifact(filename="main.py", language=lang, content="")

        # Execute using SandboxExecutor inside proj_path
        exec_res = global_sandbox_executor.execute(
            artifacts=[artifact],
            language=lang,
            command_override=cmd,
            execution_type=ExecutionType.PROJECT_TEST,
            cwd=str(proj_path),
            limits=self.limits
        )

        return exec_res



global_project_runner = ProjectRunner()
