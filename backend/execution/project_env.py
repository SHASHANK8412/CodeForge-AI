"""
Per-project Python environments for generated projects.

A generated project's requirements.txt is written by an LLM. Installing it into AIForge's own
environment would let a hallucinated or typosquatted package land in the platform itself, and
mixes the project's dependencies with AIForge's. Each project instead gets its own virtualenv at
<project>/.venv (a folder name that export, rollback and pytest already skip).
"""

import hashlib
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_logger = logging.getLogger("aiforge.execution.project_env")

ENV_DIRNAME = ".venv"
_MARKER = ".aiforge_requirements.sha256"


def requirements_file(project_dir: Path) -> Optional[Path]:
    for candidate in (project_dir / "requirements.txt", project_dir / "backend" / "requirements.txt"):
        if candidate.is_file():
            return candidate
    return None


def env_python(project_dir: Path) -> Path:
    venv = project_dir / ENV_DIRNAME
    return venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def site_packages(project_dir: Path) -> Optional[Path]:
    venv = project_dir / ENV_DIRNAME
    if sys.platform == "win32":
        path = venv / "Lib" / "site-packages"
    else:
        path = venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    return path if path.is_dir() else None


def ensure_project_env(project_dir: Path, timeout: float = 900.0) -> Dict[str, Any]:
    """
    Create <project>/.venv and install the project's requirements into it. Re-installs only when
    requirements.txt changes. Returns {ok, skipped, cached, log}.
    """
    project_dir = Path(project_dir)
    req = requirements_file(project_dir)
    if req is None:
        return {"ok": True, "skipped": True, "cached": False, "log": "No requirements.txt"}

    digest = hashlib.sha256(req.read_bytes()).hexdigest()
    marker = project_dir / ENV_DIRNAME / _MARKER
    python = env_python(project_dir)
    if python.exists() and marker.exists() and marker.read_text(encoding="utf-8").strip() == digest:
        return {"ok": True, "skipped": False, "cached": True, "log": "Requirements unchanged"}

    log = []
    try:
        if not python.exists():
            created = subprocess.run([sys.executable, "-m", "venv", str(project_dir / ENV_DIRNAME)],
                                     capture_output=True, text=True, timeout=300)
            log.append(created.stdout + created.stderr)
            if created.returncode != 0:
                return {"ok": False, "skipped": False, "cached": False, "log": "\n".join(log)}
        installed = subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", str(req)],
            cwd=str(req.parent), capture_output=True, text=True, timeout=timeout,
        )
        log.append(installed.stdout[-4000:] + installed.stderr[-4000:])
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "skipped": False, "cached": False, "log": f"Timed out: {e}"}

    ok = installed.returncode == 0
    if ok:
        marker.write_text(digest, encoding="utf-8")
    else:
        _logger.warning("Installing %s into the project env failed", req)
    return {"ok": ok, "skipped": False, "cached": False, "log": "\n".join(log)}
