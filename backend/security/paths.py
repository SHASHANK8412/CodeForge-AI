"""
Path confinement for routes that turn a client-supplied id or path into a file on disk.

Every target is resolved (symlinks included) and must stay inside its base folder; secret files
(.env*, keys, certificates, databases) are refused even when they are inside it.
"""

import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Optional

from backend.memory.codebase_indexer import is_secret_or_excluded_file

# Project and generation ids: no separators and no leading dot, so never "." or "..".
_SAFE_ID = re.compile(r"^[A-Za-z0-9_\-][A-Za-z0-9_.\-]{0,119}$")
_NOT_IN_NAME = ("/", "\\", ":", "\x00")


def is_safe_id(value: str) -> bool:
    return bool(value) and _SAFE_ID.match(value) is not None


def is_plain_filename(name: str) -> bool:
    """A single file name: no folders, drive, or leading dot (which also rules out "." and "..")."""
    return (bool(name) and len(name) <= 255 and not name.startswith(".") and name == name.strip()
            and not any(ch in name for ch in _NOT_IN_NAME))


def resolve_inside(base: Path, rel_path: str) -> Optional[Path]:
    """`base / rel_path` resolved, or None if it is absolute, climbs out of `base` or names a secret file."""
    if not rel_path or "\x00" in rel_path:
        return None
    posix = rel_path.replace("\\", "/")
    win = PureWindowsPath(rel_path)
    if posix.startswith(("/", "~")) or win.drive or win.root or PurePosixPath(posix).is_absolute():
        return None
    parts = [p for p in posix.split("/") if p not in ("", ".")]
    if not parts or ".." in parts or any(":" in p for p in parts) or is_secret_or_excluded_file("/".join(parts)):
        return None
    try:
        root = base.resolve()
        target = root.joinpath(*parts).resolve()
    except (OSError, ValueError):
        return None
    return target if root in target.parents else None
