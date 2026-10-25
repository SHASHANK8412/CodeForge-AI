"""
Project states as file maps {relative path: content hash} and their reconstruction from recorded changes.

  current_map     the project's source files now (the same files a working copy holds)
  revision_of     the fingerprint of a file map - identical to evolution_engine.service.source_revision of a
                  folder holding exactly those files, so recorded revisions can be matched
  chain           walking back from the current state through recorded changes (patch_applied, rollbacks,
                  restores): each step reverts one change, and only if the files still hold exactly what that
                  change wrote; an unrecorded modification stops the walk (it is reported, never overwritten)
  materialize     writes a file map into a new, isolated folder from the content store
"""

import hashlib
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.evolution.autopilot.workspace import COPY_SKIP
from backend.time_machine.ledger import Event, Ledger

CHANGE_TYPES = ("patch_applied", "rollback_performed", "restore_performed")
MAX_FILES = 4000


def current_map(project: Path, ledger: Ledger, store: bool = True) -> Tuple[Dict[str, str], List[str]]:
    """({path: sha256}, paths whose content could not be stored). Binary files are hashed from bytes."""
    project = Path(project).resolve()
    out: Dict[str, str] = {}
    unstored: List[str] = []
    for p in sorted(project.rglob("*")):
        rel = p.relative_to(project)
        if COPY_SKIP & set(rel.parts) or p.is_symlink() or not p.is_file():
            continue
        if len(out) >= MAX_FILES:
            break
        data = p.read_bytes()
        key = rel.as_posix()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            out[key] = hashlib.sha256(data).hexdigest()
            unstored.append(key)
            continue
        if store:
            sha, ok = ledger.put_blob(text)
            if not ok:
                unstored.append(key)
        else:
            sha = hashlib.sha256(data).hexdigest()
        out[key] = sha
    return out, unstored


def revision_of(files: Dict[str, str]) -> str:
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode() + b"\0" + bytes.fromhex(files[rel]))
    return h.hexdigest()


def changes(events: List[Event]) -> List[Event]:
    return [e for e in events if e.type in CHANGE_TYPES and e.files and e.outcome in ("success", "info")]


def revert(state: Dict[str, str], change: Event) -> Tuple[Optional[Dict[str, str]], List[str]]:
    """The state before `change`, or (None, conflicting paths) if the files no longer hold what it wrote."""
    conflicts = [f["path"] for f in change.files if state.get(f["path"]) != f.get("after")]
    if conflicts:
        return None, conflicts
    prev = dict(state)
    for f in change.files:
        if f.get("before") is None:
            prev.pop(f["path"], None)
        else:
            prev[f["path"]] = f["before"]
    return prev, []


def apply(state: Dict[str, str], change: Event) -> Tuple[Optional[Dict[str, str]], List[str]]:
    conflicts = [f["path"] for f in change.files if state.get(f["path"]) != f.get("before")]
    if conflicts:
        return None, conflicts
    nxt = dict(state)
    for f in change.files:
        if f.get("after") is None:
            nxt.pop(f["path"], None)
        else:
            nxt[f["path"]] = f["after"]
    return nxt, []


def chain(current: Dict[str, str], events: List[Event]) -> Dict[str, Any]:
    """States from now back through recorded changes: [{after_change: event|None, files, revision}], newest first."""
    states = [{"after_change": None, "files": current, "revision": revision_of(current)}]
    stopped = None
    state = current
    for ch in reversed(changes(events)):
        prev, conflicts = revert(state, ch)
        if prev is None:
            stopped = {"change": ch.id, "summary": ch.summary, "conflicts": conflicts,
                       "reason": "the project no longer holds what this change wrote (modified afterwards without a "
                                 "recorded change); older states cannot be reconstructed from here"}
            break
        states[-1]["after_change"] = ch.id
        states.append({"after_change": None, "files": prev, "revision": revision_of(prev)})
        state = prev
    return {"states": states, "stopped": stopped}


def materialize(files: Dict[str, str], ledger: Ledger, name: str = "state") -> Tuple[Optional[Path], List[str]]:
    """Write a file map into a new isolated folder. Returns (folder, missing paths); folder is None if any is missing."""
    missing = [p for p, sha in files.items() if ledger.get_blob(sha) is None]
    if missing:
        return None, missing
    root = Path(tempfile.mkdtemp(prefix="aiforge_timemachine_")) / name
    for rel, sha in files.items():
        target = (root / rel).resolve()
        if root.resolve() not in target.parents:
            raise ValueError(f"unsafe path in a recorded state: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(ledger.get_blob(sha), encoding="utf-8", newline="")
    return root, []
