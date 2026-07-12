from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PROJECT_STATE: dict[str, Any] = {
    "current_project": "",
    "frontend_stack": [],
    "backend_stack": [],
    "database": "",
    "completed_tasks": [],
    "pending_tasks": [],
    "generated_files": [],
    "latest_plan": "",
    "latest_architecture": "",
    "last_agent": "",
    "last_task": "",
    "updated_at": "",
}


class ProjectMemory:

    def __init__(self, storage_root: Path | None = None):
        self.storage_root = storage_root or Path(__file__).resolve().parent / "store" / "projects"
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        safe_session_id = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "default")
        return self.storage_root / f"{safe_session_id}.json"

    def load_project(self, session_id: str) -> dict[str, Any]:
        file_path = self._session_file(session_id)
        if not file_path.exists():
            return deepcopy(DEFAULT_PROJECT_STATE)

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}

        project = deepcopy(DEFAULT_PROJECT_STATE)
        project.update(data)
        return project

    def save_project(self, session_id: str, project_data: dict[str, Any]) -> dict[str, Any]:
        project = deepcopy(DEFAULT_PROJECT_STATE)
        project.update(project_data)
        project["updated_at"] = datetime.now(timezone.utc).isoformat()

        file_path = self._session_file(session_id)
        file_path.write_text(json.dumps(project, indent=2, ensure_ascii=False), encoding="utf-8")
        return project

    def update_project(self, session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        project = self.load_project(session_id)
        for key, value in updates.items():
            if value is None:
                continue
            if isinstance(value, list) and isinstance(project.get(key), list):
                project[key] = value
            else:
                project[key] = value

        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.save_project(session_id, project)

    def clear_project(self, session_id: str) -> None:
        self.save_project(session_id, deepcopy(DEFAULT_PROJECT_STATE))
