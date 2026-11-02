"""
The engineering event ledger: append-only, one JSON line per event per project, hash-chained.

  append      events are validated, redacted (secret values never reach disk) and appended with
              seq, prev_hash and hash = sha256(canonical event + prev_hash); nothing is rewritten.
              A correction is a new event of type "correction" that references the corrected one.
  verify      recomputes the chain and reports the first broken link (tampering or a damaged file)
  query       filters + bounded pagination (limit <= 200), newest first or oldest first
  blobs       file contents are stored once by content hash (blobs/<sha256>); a file holding
              secret-like values is NOT stored (its change is recorded with "content_stored": false)

Only subsystems that actually did something emit events (recorder.py); the ledger never infers them.
"""

import hashlib
import json
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact

DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "time_machine"
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.\-]{1,120}$")
MAX_PAGE = 200
MAX_BLOB_BYTES = 512 * 1024

EVENT_TYPES = {
    "task_created", "plan_generated", "agent_started", "agent_completed", "artifact_generated", "file_changed",
    "review_completed", "test_executed", "security_finding", "security_verification", "performance_measured",
    "resilience_assessed", "repair_proposed", "approval_requested", "approval_granted", "approval_rejected",
    "patch_applied", "rollback_performed", "release_decision", "experiment_evaluated", "checkpoint_created",
    "restore_previewed", "restore_performed", "investigation_completed", "rerun_completed", "task_completed",
    "task_failed", "correction",
}
OUTCOMES = {"success", "failure", "rejected", "inconclusive", "cancelled", "info", "error"}


class Event(BaseModel):
    id: str
    seq: int = 0
    project_id: str
    task_id: Optional[str] = None             # plan / execution / experiment / assessment id it belongs to
    type: str
    at: str = Field(default_factory=now_iso)
    source: str                               # the subsystem or agent that emitted it
    summary: str = ""
    outcome: str = "info"
    revision: Optional[str] = None            # source-tree fingerprint at the time (sha256)
    git_commit: Optional[str] = None
    parents: List[str] = Field(default_factory=list)     # recorded causal links (event ids)
    refs: Dict[str, str] = Field(default_factory=dict)   # plan_id, execution_id, experiment_id, ...
    files: List[Dict[str, Any]] = Field(default_factory=list)   # {path, before, after, content_stored}
    data: Dict[str, Any] = Field(default_factory=dict)          # small, redacted details (counts, verdicts)
    config: Dict[str, Any] = Field(default_factory=dict)        # model / prompt / workload versions
    error: Optional[str] = None
    prev_hash: str = ""
    hash: str = ""


def _redact_value(v: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "[truncated]"
    if isinstance(v, str):
        return redact(v, 4000)
    if isinstance(v, dict):
        return {str(k)[:80]: _redact_value(x, depth + 1) for k, x in list(v.items())[:60]}
    if isinstance(v, (list, tuple)):
        return [_redact_value(x, depth + 1) for x in list(v)[:200]]
    return v


def _digest(payload: Dict[str, Any], prev: str) -> str:
    body = json.dumps({k: v for k, v in payload.items() if k != "hash"}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev + body).encode()).hexdigest()


class Ledger:
    def __init__(self, root: Optional[Path] = None):
        self._root = Path(root) if root else None
        self._lock = threading.Lock()

    @property
    def root(self) -> Path:
        # resolved on every use, so tests (and deployments) can point the global ledger elsewhere
        return self._root or Path(os.environ.get("AIFORGE_TIME_MACHINE_DIR") or DEFAULT_ROOT)

    # --- storage ---------------------------------------------------------------------------------------------

    def _path(self, project_id: str) -> Path:
        if not _SAFE_ID.match(project_id or "") or project_id in (".", ".."):
            raise ValueError("invalid project id")
        return self.root / "ledger" / f"{project_id}.jsonl"

    def _tail(self, path: Path) -> Tuple[int, str]:
        if not path.exists():
            return 0, ""
        last = None
        with path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            back = min(size, 65536)
            fh.seek(size - back)
            lines = fh.read().splitlines()
            for raw in reversed(lines):
                if raw.strip():
                    last = raw
                    break
        if last is None:
            return 0, ""
        e = json.loads(last)
        return int(e["seq"]), e["hash"]

    def append(self, event: Event) -> Event:
        if event.type not in EVENT_TYPES:
            raise ValueError(f"unknown event type {event.type}")
        if event.outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome {event.outcome}")
        if event.type == "correction" and not event.refs.get("corrects"):
            raise ValueError("a correction must reference the event it corrects")
        event.summary = redact(event.summary, 600)
        event.error = redact(event.error, 2000) if event.error else None
        event.data = _redact_value(event.data)
        event.config = _redact_value(event.config)
        event.refs = {k: redact(str(v), 200) for k, v in event.refs.items()}
        path = self._path(event.project_id)
        with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            seq, prev = self._tail(path)
            event.seq, event.prev_hash = seq + 1, prev
            event.hash = _digest(event.model_dump(mode="json"), prev)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.model_dump(mode="json"), separators=(",", ":")) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        return event

    def _iter(self, project_id: str) -> Iterator[Dict[str, Any]]:
        path = self._path(project_id)
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    try:
                        yield json.loads(line)
                    except ValueError:
                        yield {"__corrupt__": line[:200]}

    def events(self, project_id: str) -> List[Event]:
        return [Event(**e) for e in self._iter(project_id) if "__corrupt__" not in e]

    def get(self, project_id: str, event_id: str) -> Optional[Event]:
        return next((e for e in self.events(project_id) if e.id == event_id), None)

    def query(self, project_id: str, types: Optional[List[str]] = None, sources: Optional[List[str]] = None,
              task_id: Optional[str] = None, outcome: Optional[str] = None, q: Optional[str] = None,
              file: Optional[str] = None, offset: int = 0, limit: int = 50, newest_first: bool = True) -> Dict[str, Any]:
        limit = max(1, min(limit, MAX_PAGE))
        items = self.events(project_id)
        if types:
            items = [e for e in items if e.type in types]
        if sources:
            items = [e for e in items if e.source in sources]
        if task_id:
            items = [e for e in items if e.task_id == task_id or task_id in e.refs.values()]
        if outcome:
            items = [e for e in items if e.outcome == outcome]
        if file:
            items = [e for e in items if any(f.get("path") == file for f in e.files)]
        if q:
            ql = q.lower()
            items = [e for e in items if ql in f"{e.summary} {e.type} {e.source} {e.task_id}".lower()]
        if newest_first:
            items = list(reversed(items))
        return {"total": len(items), "offset": offset, "limit": limit, "items": items[offset:offset + limit]}

    def verify(self, project_id: str) -> Dict[str, Any]:
        prev, count = "", 0
        for raw in self._iter(project_id):
            if "__corrupt__" in raw:
                return {"valid": False, "events": count, "broken_at": count + 1, "reason": "unreadable line"}
            count += 1
            if raw.get("prev_hash") != prev or _digest(raw, prev) != raw.get("hash") or raw.get("seq") != count:
                return {"valid": False, "events": count, "broken_at": raw.get("seq"), "event_id": raw.get("id"),
                        "reason": "hash chain mismatch (the file was edited or damaged)"}
            prev = raw["hash"]
        return {"valid": True, "events": count}

    def projects(self) -> List[str]:
        d = self.root / "ledger"
        return sorted(p.stem for p in d.glob("*.jsonl")) if d.is_dir() else []

    # --- content-addressed file versions -----------------------------------------------------------------------

    def put_blob(self, content: Optional[str]) -> Tuple[Optional[str], bool]:
        """(sha256, stored). None content = the file does not exist. Secret-bearing or huge files are hashed, not stored."""
        if content is None:
            return None, True
        data = content.encode("utf-8")
        sha = hashlib.sha256(data).hexdigest()
        if redact(content) != content or len(data) > MAX_BLOB_BYTES:
            return sha, False
        path = self.root / "blobs" / sha[:2] / sha
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp" + uuid.uuid4().hex[:6])
            tmp.write_bytes(data)
            os.replace(tmp, path)
        return sha, True

    def get_blob(self, sha: Optional[str]) -> Optional[str]:
        if sha is None or not re.fullmatch(r"[0-9a-f]{64}", sha):
            return None
        path = self.root / "blobs" / sha[:2] / sha
        if not path.is_file():
            return None
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != sha:            # integrity check
            return None
        return data.decode("utf-8")

    def has_blob(self, sha: Optional[str]) -> bool:
        return sha is None or (bool(sha) and (self.root / "blobs" / sha[:2] / sha).is_file())


def new_id() -> str:
    return "tme_" + uuid.uuid4().hex[:14]
