"""
CI Build Stage
==============
Executes project compilation and asset building inside the isolated sandbox workspace.
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

_logger = logging.getLogger("aiforge.ci.build_stage")


class BuildStage(CIStageBase):
    """
    Build Stage validating syntax, compilation, and production bundles.
    """

    def __init__(self):
        super().__init__(name="build")

    def resolve_command(self, sandbox_path: Path, project_cfg: DetectedProjectConfig) -> List[str]:
        lang = project_cfg.language.lower()
        if lang == "python":
            entry = None
            if (sandbox_path / "backend" / "main.py").exists():
                entry = "backend/main.py"
            elif (sandbox_path / "main.py").exists():
                entry = "main.py"
            elif (sandbox_path / "app.py").exists():
                entry = "app.py"
            else:
                py_files = [p for p in sandbox_path.rglob("*.py") if ".git" not in p.parts and "test" not in p.name.lower()]
                if not py_files:
                    py_files = list(sandbox_path.rglob("*.py"))
                if py_files:
                    entry = str(py_files[0].relative_to(sandbox_path)).replace("\\", "/")

            if entry:
                return [sys.executable, "-m", "py_compile", entry]
            return [sys.executable, "-c", "import sys; sys.exit(0)"]

        elif lang in ["javascript", "typescript"]:
            pkg_json = sandbox_path / "package.json"
            npm_cmd = "npm.cmd" if sys.platform == "win32" and shutil.which("npm.cmd") else (shutil.which("npm") or "npm")
            if pkg_json.exists():
                try:
                    data = json.loads(pkg_json.read_text(encoding="utf-8"))
                    scripts = data.get("scripts", {})
                    if "build" in scripts:
                        return [npm_cmd, "run", "build"]
                except Exception:
                    pass

            entry = sandbox_path / "index.js"
            node_cmd = shutil.which("node") or "node"
            if entry.exists():
                return [node_cmd, "-c", "index.js"]
            return [node_cmd, "-v"]

        return [sys.executable, "--version"]

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
            command=cmd_str,
            details={"framework": project_cfg.framework}
        )
