"""
How subsystems report what they actually did to the Time Machine ledger.

`emit` is called by the subsystem at the moment something happened (an Autopilot execution applied a patch,
the Security Guardian finished an assessment, ...). It never raises into the caller: recording is best
effort, and a failure to record is logged, not turned into a failed engineering task. Parents are recorded
links (`parents`) or the latest event carrying the same reference (`parent_ref`), never guesses.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.time_machine.ledger import Event, Ledger, new_id

_logger = logging.getLogger("aiforge.time_machine")
global_ledger = Ledger()


def fingerprint(project: Optional[Path]) -> Tuple[Optional[str], Optional[str]]:
    """(source-tree fingerprint, git commit or None)."""
    if project is None or not Path(project).is_dir():
        return None, None
    from backend.evolution_engine.service import source_revision
    try:
        revision = source_revision(Path(project))
    except OSError:
        revision = None
    commit = None
    if (Path(project) / ".git").exists():
        try:
            out = subprocess.run(["git", "-C", str(project), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
            commit = out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            commit = None
    return revision, commit


def file_records(before: Dict[str, Optional[str]], after: Dict[str, Optional[str]], ledger: Optional[Ledger] = None
                 ) -> List[Dict[str, Any]]:
    """Per changed file: content hashes before/after; contents stored by hash unless they hold secrets."""
    ledger = ledger or global_ledger
    out = []
    for path in sorted(set(before) | set(after)):
        b, a = before.get(path), after.get(path)
        if b == a:
            continue
        hb, sb = ledger.put_blob(b)
        ha, sa = ledger.put_blob(a)
        out.append({"path": path, "before": hb, "after": ha, "content_stored": sb and sa,
                    "change": "added" if b is None else "deleted" if a is None else "modified"})
    return out


def latest_with_ref(project_id: str, key: str, value: str, ledger: Optional[Ledger] = None) -> Optional[Event]:
    ledger = ledger or global_ledger
    found = [e for e in ledger.events(project_id) if e.refs.get(key) == value]
    return found[-1] if found else None


def emit(project_id: str, type: str, source: str, summary: str = "", outcome: str = "info",
         task_id: Optional[str] = None, refs: Optional[Dict[str, str]] = None, parents: Optional[List[str]] = None,
         parent_ref: Optional[Tuple[str, str]] = None, data: Optional[Dict[str, Any]] = None,
         config: Optional[Dict[str, Any]] = None, error: Optional[str] = None, project_dir: Optional[Path] = None,
         files: Optional[List[Dict[str, Any]]] = None, ledger: Optional[Ledger] = None) -> Optional[Event]:
    ledger = ledger or global_ledger
    try:
        revision, commit = fingerprint(project_dir)
        links = list(parents or [])
        if parent_ref:
            p = latest_with_ref(project_id, parent_ref[0], parent_ref[1], ledger)
            if p is not None and p.id not in links:
                links.append(p.id)
        return ledger.append(Event(
            id=new_id(), project_id=project_id, task_id=task_id, type=type, source=source, summary=summary,
            outcome=outcome, revision=revision, git_commit=commit, parents=links,
            refs={k: str(v) for k, v in (refs or {}).items() if v is not None}, files=files or [], data=data or {},
            config=config or {}, error=error))
    except Exception as e:  # noqa: BLE001 - recording must never break the engineering task itself
        _logger.warning("Time Machine: could not record %s for %s: %s", type, project_id, e)
        return None


def check_data(checks) -> Dict[str, Any]:
    """Compact, comparable view of Autopilot CheckResults."""
    out = {}
    for c in checks or []:
        out[c.check_id] = {"status": c.status, "counts": dict(c.counts), "environment": c.environment,
                           "finished_at": c.finished_at}
    return out
