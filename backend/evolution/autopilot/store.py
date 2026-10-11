"""
Persistence: one JSON document per project (analyses, findings, plans, executions), written
atomically under a lock so concurrent requests and background jobs do not lose updates.
"""

import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from backend.evolution.autopilot.models import Analysis, Execution, Finding, Plan

_DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data" / "evolution"
_SAFE_ID = re.compile(r"^[A-Za-z0-9_.\-]{1,120}$")
_KINDS: Dict[str, Type[BaseModel]] = {"analyses": Analysis, "findings": Finding, "plans": Plan, "executions": Execution}
M = TypeVar("M", bound=BaseModel)
KEEP_ANALYSES = 20
KEEP_EXECUTIONS = 50


class AutopilotStore:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root or os.environ.get("AIFORGE_EVOLUTION_DIR") or _DEFAULT_ROOT)
        self._lock = threading.RLock()

    def _path(self, project_id: str) -> Path:
        if not _SAFE_ID.match(project_id) or project_id in (".", ".."):
            raise ValueError("invalid project id")
        return self.root / f"{project_id}.json"

    def _load(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        path = self._path(project_id)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            data = {}
        except (OSError, ValueError):
            # Keep a corrupt file for inspection instead of overwriting it.
            path.replace(path.with_suffix(".corrupt.json"))
            data = {}
        return {kind: data.get(kind, {}) for kind in _KINDS}

    def _save(self, project_id: str, data: Dict[str, Any]) -> None:
        path = self._path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
        os.replace(tmp, path)

    # --- generic ---------------------------------------------------------------------------

    def get(self, project_id: str, kind: str, item_id: str) -> Optional[BaseModel]:
        with self._lock:
            raw = self._load(project_id)[kind].get(item_id)
        return _KINDS[kind](**raw) if raw else None

    def list(self, project_id: str, kind: str) -> List[BaseModel]:
        with self._lock:
            items = list(self._load(project_id)[kind].values())
        return [_KINDS[kind](**raw) for raw in items]

    def put(self, project_id: str, kind: str, item: BaseModel) -> None:
        with self._lock:
            data = self._load(project_id)
            data[kind][item.id] = item.model_dump(mode="json")
            self._prune(data)
            self._save(project_id, data)

    def update(self, project_id: str, kind: str, item_id: str, change: Callable[[Any], None]) -> Optional[BaseModel]:
        """Read-modify-write one record under the lock."""
        with self._lock:
            data = self._load(project_id)
            raw = data[kind].get(item_id)
            if raw is None:
                return None
            item = _KINDS[kind](**raw)
            change(item)
            data[kind][item_id] = item.model_dump(mode="json")
            self._save(project_id, data)
            return item

    def replace_findings(self, project_id: str, findings: Dict[str, Finding]) -> None:
        with self._lock:
            data = self._load(project_id)
            data["findings"] = {fid: f.model_dump(mode="json") for fid, f in findings.items()}
            self._save(project_id, data)

    def set_finding_status(self, project_id: str, ids: List[str], status: str) -> None:
        with self._lock:
            data = self._load(project_id)
            for fid in ids:
                if fid in data["findings"]:
                    data["findings"][fid]["status"] = status
            self._save(project_id, data)

    @staticmethod
    def _prune(data: Dict[str, Dict[str, Any]]) -> None:
        for kind, keep, key in (("analyses", KEEP_ANALYSES, "started_at"), ("executions", KEEP_EXECUTIONS, "started_at")):
            items = data[kind]
            if len(items) > keep:
                ordered = sorted(items, key=lambda k: items[k].get(key) or "")
                for k in ordered[:len(items) - keep]:
                    if items[k].get("status") not in ("queued", "running"):
                        del items[k]

    def mark_interrupted(self) -> int:
        """
        Jobs run in server threads; after a restart, records still 'queued'/'running' can never
        finish. They are closed as failed (a run that had not reached 'apply' left the project as it was).
        """
        from backend.evolution.autopilot.models import now_iso
        closed = 0
        if not self.root.is_dir():
            return 0
        with self._lock:
            for path in self.root.glob("*.json"):
                project_id = path.stem
                if not _SAFE_ID.match(project_id) or path.name.endswith(".corrupt.json"):
                    continue
                data = self._load(project_id)
                changed = False
                for kind in ("analyses", "executions"):
                    for item in data[kind].values():
                        if item.get("status") in ("queued", "running"):
                            item["status"], item["finished_at"] = "failed", now_iso()
                            item["error"] = "interrupted: the server stopped while this was running" + (
                                "" if kind == "analyses" or not item.get("applied_to_project") else
                                " (after the changes had been written)")
                            changed, closed = True, closed + 1
                for plan in data["plans"].values():
                    if plan.get("status") == "running":
                        plan["status"], changed = "failed", True
                if changed:
                    self._save(project_id, data)
        return closed

    def latest_analysis(self, project_id: str) -> Optional[Analysis]:
        analyses = self.list(project_id, "analyses")
        return max(analyses, key=lambda a: a.started_at or "", default=None)


global_autopilot_store = AutopilotStore()
