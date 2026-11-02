"""
Isolated working copies. Autopilot never edits or runs anything in the project folder itself:
changes are made and checked in a copy, and only accepted changes are written back.
"""

import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Iterable, Optional

COPY_SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache",
             ".mypy_cache", "dist", "build", ".next", "coverage", ".turbo", ".cache"}
COPY_LIMIT_BYTES = 200 * 1024 * 1024


class WorkspaceError(Exception):
    pass


def _ignore(_dir, names):
    return [n for n in names if n in COPY_SKIP]


def create_workspace(project: Path, prefix: str = "aiforge_autopilot_") -> Path:
    """A disposable copy of the project's sources (dependency and cache folders are left out)."""
    project = Path(project).resolve()
    total = 0
    for p in project.rglob("*"):
        if COPY_SKIP & set(p.relative_to(project).parts):
            continue
        if p.is_file() and not p.is_symlink():
            total += p.stat().st_size
            if total > COPY_LIMIT_BYTES:
                raise WorkspaceError("project is larger than the 200 MB working-copy limit")
    root = Path(tempfile.mkdtemp(prefix=prefix))
    dest = root / project.name
    shutil.copytree(project, dest, ignore=_ignore, symlinks=True)
    return dest


def discard_workspace(workspace: Optional[Path]) -> None:
    if workspace is not None:
        shutil.rmtree(Path(workspace).parent, ignore_errors=True)


def file_hash(path: Path) -> Optional[str]:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def snapshot(project: Path, files: Iterable[str]) -> Dict[str, Optional[str]]:
    """Content hashes of the given files (None = missing), to detect edits made meanwhile."""
    project = Path(project)
    return {f: file_hash(project / f) for f in files}
