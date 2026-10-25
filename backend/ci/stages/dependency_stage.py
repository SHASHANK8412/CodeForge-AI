"""
CI Dependency Installation Stage
================================
Installs dependencies inside the isolated sandbox workspace using the appropriate package manager.
"""

import sys
import time
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.ci.models import CIStageResult, CIStageStatus
from backend.ci.stages.base_stage import CIStageBase
from backend.execution.project_detector import DetectedProjectConfig
from backend.execution.execution_backend import ExecutionBackend

_logger = logging.getLogger("aiforge.ci.dependency_stage")


class DependencyStage(CIStageBase):
    """
    Executes dependency installation for Python, Node.js, and React/Vite projects.
    """

    def __init__(self):
        super().__init__(name="dependencies")

    def resolve_command(self, sandbox_path: Path, project_cfg: DetectedProjectConfig) -> Optional[List[str]]:
        pm = project_cfg.package_manager.lower()
        if pm in ["npm", "yarn", "pnpm"] or (sandbox_path / "package.json").exists():
            npm_cmd = "npm.cmd" if sys.platform == "win32" and shutil.which("npm.cmd") else (shutil.which("npm") or "npm")
            return [npm_cmd, "install", "--no-audit", "--no-fund"]
        elif pm == "pip" or (sandbox_path / "requirements.txt").exists():
            return [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
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
                stdout="No dependencies declaration found. Skipping installation.",
                duration=elapsed,
                command="skip"
            )

        cmd_str = " ".join(cmd)
        exec_res = backend.execute_command(
            command=cmd,
            cwd=str(sandbox_path),
            timeout_seconds=timeout * 2,  # Dependencies get slightly higher timeout
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
            command=cmd_str,
            details={"package_manager": project_cfg.package_manager}
        )
