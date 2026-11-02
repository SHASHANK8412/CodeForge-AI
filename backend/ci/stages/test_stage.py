"""
CI Test Stage
=============
Executes unit and integration tests inside the isolated sandbox workspace.
"""

import sys
import time
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.ci.models import CIStageResult, CIStageStatus
from backend.ci.stages.base_stage import CIStageBase
from backend.execution.project_detector import DetectedProjectConfig
from backend.execution.execution_backend import ExecutionBackend

_logger = logging.getLogger("aiforge.ci.test_stage")


class TestStage(CIStageBase):
    """
    Test Stage executing pytest / npm test suites.
    """

    def __init__(self):
        super().__init__(name="tests")

    def resolve_command(self, sandbox_path: Path, project_cfg: DetectedProjectConfig) -> Optional[List[str]]:
        lang = project_cfg.language.lower()
        if lang == "python":
            py_files = list(sandbox_path.glob("**/*.py"))
            has_tests = any("test" in p.name.lower() for p in py_files)
            if has_tests:
                target_arg = "tests" if (sandbox_path / "tests").exists() else "."
                return [sys.executable, "-m", "pytest", target_arg, "--rootdir=.", "-p", "no:langsmith", "-p", "no:cacheprovider", "-q"]
            return None

        elif lang in ["javascript", "typescript"]:
            pkg_json = sandbox_path / "package.json"
            npm_cmd = "npm.cmd" if sys.platform == "win32" and shutil.which("npm.cmd") else (shutil.which("npm") or "npm")
            if pkg_json.exists():
                try:
                    data = json.loads(pkg_json.read_text(encoding="utf-8"))
                    scripts = data.get("scripts", {})
                    if "test" in scripts and "no test specified" not in scripts["test"]:
                        return [npm_cmd, "test"]
                except Exception:
                    pass
            return None

        return None

    def execute(
        self,
        sandbox_path: Path,
        project_cfg: DetectedProjectConfig,
        backend: ExecutionBackend,
        timeout: float,
        custom_env: Optional[Dict[str, str]] = None,
        files_manifest: Optional[Dict[str, str]] = None
    ) -> CIStageResult:
        start_time = time.perf_counter()
        cmd = self.resolve_command(sandbox_path, project_cfg)

        if not cmd:
            elapsed = round(time.perf_counter() - start_time, 3)
            return CIStageResult(
                stage=self.name,
                status=CIStageStatus.PASSED.value,
                exit_code=0,
                stdout="No test files or scripts identified. Stage passed trivially.",
                duration=elapsed,
                command="skip"
            )

        cmd_str = " ".join(cmd)
        exec_res = backend.execute_command(
            command=cmd,
            cwd=str(sandbox_path),
            timeout_seconds=timeout,
            max_output_bytes=50000,
            custom_env=custom_env,
            project_type=f"{project_cfg.language}:{project_cfg.framework}"
        )

        elapsed = round(time.perf_counter() - start_time, 3)
        status = CIStageStatus.PASSED.value if exec_res.exit_code == 0 else CIStageStatus.FAILED.value
        if exec_res.timed_out:
            status = CIStageStatus.TIMEOUT.value

        return CIStageResult(
            stage=self.name,
            status=status,
            exit_code=exec_res.exit_code,
            stdout=exec_res.stdout,
            stderr=exec_res.stderr,
            duration=elapsed,
            command=cmd_str
        )
