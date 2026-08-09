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

_logger = logging.getLogger("aiforge.execution.project_runner")


class ProjectRunner:
    """
    Executes real project builds and test suites on disk using SandboxExecutor.
    """

    def __init__(self, limits: Optional[ExecutionLimits] = None):
        self.limits = limits or ExecutionLimits(timeout_seconds=15.0)

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
        py_files = list(project_path.glob("**/*.py"))
        if py_files:
            has_tests = any("test" in p.name.lower() for p in py_files)
            if has_tests and shutil.which("pytest"):
                return [sys.executable, "-m", "pytest"], "python"
            return [sys.executable, "-m", "compileall", "-e", "."], "python"

        return [], "unknown"


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

        _logger.info(f"ProjectRunner executing '{' '.join(cmd)}' inside '{proj_path}'...")

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
