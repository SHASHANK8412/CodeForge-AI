"""
AIForge Dependency Manager Module
=================================
Automates dependency detection, installation caching, stdout/stderr capture,
and execution timing across multiple package managers (npm, pnpm, yarn, pip, poetry, uv, mvn, gradle).
"""

import os
import sys
import time
import shutil
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.execution.dependency_manager")


class DependencyResult(BaseModel):
    success: bool
    package_manager: str
    command: str
    duration_seconds: float
    stdout: str
    stderr: str
    cached: bool = False
    error_type: Optional[str] = None


class DependencyManager:
    """
    Installs project dependencies safely with caching to prevent duplicate runs.
    """

    def __init__(self):
        self._installed_hashes: Dict[str, str] = {}

    def _get_file_hash(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def detect_package_managers(self, project_path: Path) -> List[str]:
        """Detects applicable package managers in project directory."""
        managers = []
        if (project_path / "frontend" / "package.json").exists() or (project_path / "package.json").exists():
            if (project_path / "pnpm-lock.yaml").exists() or (project_path / "frontend" / "pnpm-lock.yaml").exists():
                managers.append("pnpm")
            elif (project_path / "yarn.lock").exists() or (project_path / "frontend" / "yarn.lock").exists():
                managers.append("yarn")
            else:
                managers.append("npm")

        if (project_path / "backend" / "requirements.txt").exists() or (project_path / "requirements.txt").exists():
            if (project_path / "pyproject.toml").exists():
                managers.append("poetry")
            elif (project_path / "uv.lock").exists():
                managers.append("uv")
            else:
                managers.append("pip")

        if (project_path / "pom.xml").exists():
            managers.append("mvn")
        elif (project_path / "build.gradle").exists():
            managers.append("gradle")

        return managers or ["pip", "npm"]

    def install_dependencies(
        self,
        project_path: Path,
        working_dir: Optional[Path] = None,
        package_manager: Optional[str] = None,
        force: bool = False
    ) -> DependencyResult:
        target_dir = working_dir or project_path
        if not target_dir.exists():
            return DependencyResult(
                success=False,
                package_manager=package_manager or "unknown",
                command="none",
                duration_seconds=0.0,
                stdout="",
                stderr=f"Target directory '{target_dir}' does not exist.",
                error_type="DirectoryNotFound"
            )

        pm = package_manager or (self.detect_package_managers(target_dir)[0] if self.detect_package_managers(target_dir) else "pip")

        # Determine manifest file to hash
        manifest_file = None
        if pm in ["npm", "pnpm", "yarn"]:
            manifest_file = target_dir / "package.json"
        elif pm in ["pip", "poetry", "uv"]:
            manifest_file = target_dir / "requirements.txt"
        elif pm == "mvn":
            manifest_file = target_dir / "pom.xml"
        elif pm == "gradle":
            manifest_file = target_dir / "build.gradle"

        file_hash = self._get_file_hash(manifest_file) if manifest_file else ""
        cache_key = f"{target_dir}:{pm}:{file_hash}"

        if not force and file_hash and self._installed_hashes.get(cache_key) == file_hash:
            _logger.info(f"DependencyManager: Cached dependency state for {pm} in '{target_dir}'")
            return DependencyResult(
                success=True,
                package_manager=pm,
                command="cached",
                duration_seconds=0.0,
                stdout="Dependencies already installed (cache hit).",
                stderr="",
                cached=True
            )

        # Build install command
        cmd_str = ""
        if pm == "npm":
            npm_bin = "npm.cmd" if sys.platform == "win32" and shutil.which("npm.cmd") else "npm"
            cmd_str = f"{npm_bin} install --no-audit --no-fund"
        elif pm == "pnpm":
            cmd_str = "pnpm install"
        elif pm == "yarn":
            cmd_str = "yarn install"
        elif pm == "pip":
            req_file = manifest_file if manifest_file and manifest_file.exists() else "requirements.txt"
            cmd_str = f"{sys.executable} -m pip install -r {req_file.name if isinstance(req_file, Path) else req_file}"
        elif pm == "poetry":
            cmd_str = "poetry install"
        elif pm == "uv":
            cmd_str = "uv pip install -r requirements.txt"
        elif pm == "mvn":
            cmd_str = "mvn dependency:resolve"
        elif pm == "gradle":
            cmd_str = "gradle dependencies"
        else:
            cmd_str = f"{sys.executable} -m pip install -r requirements.txt"

        _logger.info(f"DependencyManager running: '{cmd_str}' in '{target_dir}'")
        start_time = time.time()
        try:
            res = subprocess.run(
                cmd_str,
                shell=True,
                cwd=str(target_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            duration = round(time.time() - start_time, 2)
            success = (res.returncode == 0)

            if success and file_hash:
                self._installed_hashes[cache_key] = file_hash

            err_type = None
            if not success:
                err_type = "InstallFailed"
                if "ModuleNotFoundError" in res.stderr or "No matching distribution" in res.stderr:
                    err_type = "PackageNotFound"

            return DependencyResult(
                success=success,
                package_manager=pm,
                command=cmd_str,
                duration_seconds=duration,
                stdout=res.stdout,
                stderr=res.stderr,
                error_type=err_type
            )
        except subprocess.TimeoutExpired:
            return DependencyResult(
                success=False,
                package_manager=pm,
                command=cmd_str,
                duration_seconds=120.0,
                stdout="",
                stderr="Dependency installation timed out after 120s.",
                error_type="TimeoutError"
            )
        except Exception as e:
            return DependencyResult(
                success=False,
                package_manager=pm,
                command=cmd_str,
                duration_seconds=round(time.time() - start_time, 2),
                stdout="",
                stderr=str(e),
                error_type="ExecutionError"
            )


global_dependency_manager = DependencyManager()
