"""
backend/generation/store.py
============================
JSON-file-backed persistent store for generation records.

Survives FastAPI restarts, browser refreshes, and SSE reconnects.
Thread-safe via threading.Lock; async-safe via run_in_executor pattern.

Record schema
-------------
{
    "generation_id": "gen_abc123",
    "project_id":    "proj_xyz",
    "user_id":       "user_id",
    "status":        "queued|planning|architecting|building|reviewing|testing|
                       repairing|documenting|assembling|completed|failed|cancelled",
    "current_agent": "planner",
    "progress":      45,
    "agents":        [{"name": "planner", "status": "completed", "started_at": ...,
                       "completed_at": ..., "duration": 8.4, "retry_count": 0,
                       "error": null}],
    "events":        [{"id": "evt_...", "type": "agent_started", "agent": "planner",
                       "message": "...", "metadata": {}, "timestamp": "..."}],
    "started_at":    "2026-08-09T13:00:00",
    "completed_at":  null,
    "error":         null,
    "created_at":    "2026-08-09T13:00:00"
}
"""

from __future__ import annotations

import json
import logging
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_logger = logging.getLogger("aiforge.generation.store")

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_STORE_FILE = _DATA_DIR / "generations.json"

# ---------------------------------------------------------------------------
# Valid status strings
# ---------------------------------------------------------------------------
GENERATION_STATUSES = {
    "queued", "planning", "architecting", "building",
    "reviewing", "testing", "repairing", "documenting",
    "assembling", "completed", "failed", "cancelled",
}

AGENT_STATUSES = {"waiting", "running", "completed", "failed", "retrying", "skipped"}

# Weighted progress contribution per agent (must sum to 100)
AGENT_WEIGHTS: Dict[str, float] = {
    "planner":              7.0,
    "architect":            7.0,
    "frontend":             9.0,
    "backend":              9.0,
    "database":             5.0,
    "assembly":             3.0,
    "reviewer":             7.0,
    "documentation":        3.0,
    "build_validation":     3.0,
    "dependency_manager":   2.0,
    "security_scan":        2.0,
    "performance":          2.0,
    "execution_validation": 3.0,
    "testing":              7.0,
    "debug":                2.0,
    "patch":                2.0,
    "packaging":            1.0,
    "deployment":           2.0,
    "github_sync":          4.0,
    "ci_check":             4.0,
    "live_deploy":          6.0,
    "health_check":        10.0,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gen_id() -> str:
    return f"gen_{secrets.token_urlsafe(10)}"


def _evt_id() -> str:
    return f"evt_{secrets.token_urlsafe(8)}"


class GenerationStore:
    """
    Thread-safe, JSON-file-backed persistent store for all generation records.

    Usage
    -----
    store = GenerationStore()
    gen_id = store.create(project_id, user_id, prompt)
    store.update_status(gen_id, "planning")
    store.agent_started(gen_id, "planner")
    store.agent_completed(gen_id, "planner", duration=8.4)
    gen = store.get(gen_id)
    """

    def __init__(self, store_path: Optional[Path] = None) -> None:
        self._path = store_path or _STORE_FILE
        self._lock = threading.Lock()
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_file(self) -> None:
        if not self._path.exists():
            self._path.write_text(json.dumps({}), encoding="utf-8")

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _read(self) -> Dict[str, Any]:
        """Load under lock."""
        with self._lock:
            return self._load()

    def _write(self, data: Dict[str, Any]) -> None:
        """Save under lock."""
        with self._lock:
            self._save(data)

    def _get_record(self, gen_id: str) -> Optional[Dict[str, Any]]:
        data = self._load()
        return data.get(gen_id)

    def _update_record(self, gen_id: str, updates: Dict[str, Any]) -> bool:
        with self._lock:
            data = self._load()
            if gen_id not in data:
                return False
            data[gen_id].update(updates)
            self._save(data)
            return True

    def _compute_progress(self, agents: List[Dict[str, Any]]) -> int:
        total = 0.0
        for a in agents:
            name = a.get("name", "")
            weight = AGENT_WEIGHTS.get(name, 0.0)
            status = a.get("status", "waiting")
            if status == "completed":
                total += weight
            elif status == "running":
                total += weight * 0.5
        return min(int(total), 99)  # Never show 100 until truly completed

    # ------------------------------------------------------------------
    # Public API — Creation
    # ------------------------------------------------------------------

    def create(self, project_id: str, user_id: str, prompt: str, gen_id: Optional[str] = None) -> str:
        """Create a new generation record and return its ID."""
        gen_id = gen_id or _gen_id()
        now = _now_iso()

        agents = [
            {"name": name, "status": "waiting", "started_at": None,
             "completed_at": None, "duration": None, "retry_count": 0, "error": None}
            for name in AGENT_WEIGHTS
        ]
        record: Dict[str, Any] = {
            "generation_id": gen_id,
            "project_id": project_id,
            "user_id": user_id,
            "prompt": prompt,
            "status": "queued",
            "current_agent": None,
            "progress": 0,
            "agents": agents,
            "events": [],
            "started_at": None,
            "completed_at": None,
            "error": None,
            "created_at": now,
        }
        with self._lock:
            data = self._load()
            data[gen_id] = record
            self._save(data)
        _logger.info("[GENERATION] %s created (project=%s user=%s)", gen_id, project_id, user_id)
        return gen_id

    # ------------------------------------------------------------------
    # Public API — Status updates
    # ------------------------------------------------------------------

    def update_status(self, gen_id: str, status: str, error: Optional[str] = None) -> None:
        updates: Dict[str, Any] = {"status": status}
        if status in ("queued", "planning") and not self.get(gen_id, {}).get("started_at"):
            updates["started_at"] = _now_iso()
        if status in ("completed", "failed", "cancelled"):
            updates["completed_at"] = _now_iso()
            updates["progress"] = 100 if status == "completed" else self._get_progress(gen_id)
        if error is not None:
            updates["error"] = error
        self._update_record(gen_id, updates)
        _logger.info("[GENERATION] %s status → %s", gen_id, status)

    def _get_progress(self, gen_id: str) -> int:
        rec = self._get_record(gen_id)
        if not rec:
            return 0
        return self._compute_progress(rec.get("agents", []))

    # ------------------------------------------------------------------
    # Public API — Agent lifecycle
    # ------------------------------------------------------------------

    def agent_started(self, gen_id: str, agent_name: str) -> None:
        now = _now_iso()
        with self._lock:
            data = self._load()
            if gen_id not in data:
                return
            rec = data[gen_id]
            for a in rec["agents"]:
                if a["name"] == agent_name:
                    a["status"] = "running"
                    a["started_at"] = now
                    break
            rec["current_agent"] = agent_name
            rec["progress"] = self._compute_progress(rec["agents"])
            self._save(data)
        _logger.info("[%s] started", agent_name.upper())

    def agent_completed(self, gen_id: str, agent_name: str, duration: float = 0.0) -> None:
        now = _now_iso()
        with self._lock:
            data = self._load()
            if gen_id not in data:
                return
            rec = data[gen_id]
            for a in rec["agents"]:
                if a["name"] == agent_name:
                    a["status"] = "completed"
                    a["completed_at"] = now
                    a["duration"] = round(duration, 3)
                    break
            rec["progress"] = self._compute_progress(rec["agents"])
            self._save(data)
        _logger.info("[%s] completed duration=%.2fs", agent_name.upper(), duration)

    def agent_failed(self, gen_id: str, agent_name: str, error: str = "") -> None:
        now = _now_iso()
        with self._lock:
            data = self._load()
            if gen_id not in data:
                return
            for a in data[gen_id]["agents"]:
                if a["name"] == agent_name:
                    a["status"] = "failed"
                    a["completed_at"] = now
                    # Don't expose raw exceptions; store a safe summary
                    a["error"] = (error[:200] + "…") if len(error) > 200 else error
                    break
            self._save(data)
        _logger.warning("[%s] failed: %s", agent_name.upper(), error[:120])

    def agent_retrying(self, gen_id: str, agent_name: str) -> None:
        with self._lock:
            data = self._load()
            if gen_id not in data:
                return
            for a in data[gen_id]["agents"]:
                if a["name"] == agent_name:
                    a["status"] = "retrying"
                    a["retry_count"] = a.get("retry_count", 0) + 1
                    break
            self._save(data)

    # ------------------------------------------------------------------
    # Public API — Events
    # ------------------------------------------------------------------

    def add_event(
        self,
        gen_id: str,
        event_type: str,
        agent: Optional[str] = None,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append an event to the generation's event log. Returns the event dict."""
        event: Dict[str, Any] = {
            "id": _evt_id(),
            "type": event_type,
            "agent": agent,
            "message": message,
            "metadata": metadata or {},
            "timestamp": _now_iso(),
        }
        with self._lock:
            data = self._load()
            if gen_id in data:
                data[gen_id]["events"].append(event)
                self._save(data)
        return event

    # ------------------------------------------------------------------
    # Public API — Reads
    # ------------------------------------------------------------------

    def get(self, gen_id: str, default: Any = None) -> Any:
        rec = self._get_record(gen_id)
        return rec if rec is not None else default

    def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        data = self._read()
        return [r for r in data.values() if r.get("user_id") == user_id]

    def get_events(
        self, gen_id: str, offset: int = 0, limit: int = 200
    ) -> List[Dict[str, Any]]:
        rec = self._get_record(gen_id)
        if not rec:
            return []
        events = rec.get("events", [])
        return events[offset: offset + limit]

    def owns(self, gen_id: str, user_id: str) -> bool:
        rec = self._get_record(gen_id)
        return rec is not None and rec.get("user_id") == user_id

    def exists(self, gen_id: str) -> bool:
        return self._get_record(gen_id) is not None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
global_generation_store = GenerationStore()
