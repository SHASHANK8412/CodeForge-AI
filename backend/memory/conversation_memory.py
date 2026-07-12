from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ConversationMemory:

    def __init__(self, storage_root: Path | None = None):
        self.storage_root = storage_root or Path(__file__).resolve().parent / "store" / "conversations"
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        safe_session_id = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "default")
        return self.storage_root / f"{safe_session_id}.json"

    def _read_records(self, session_id: str) -> list[dict[str, Any]]:
        file_path = self._session_file(session_id)
        if not file_path.exists():
            return []

        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _write_records(self, session_id: str, records: list[dict[str, Any]]) -> None:
        file_path = self._session_file(session_id)
        file_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    def save_message(
        self,
        session_id: str,
        user_prompt: str,
        ai_response: str,
        agent_name: str = "",
        route: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_prompt": user_prompt,
            "ai_response": ai_response,
            "agent_name": agent_name,
            "route": route,
            "metadata": metadata or {},
        }

        records = self._read_records(session_id)
        records.append(record)
        self._write_records(session_id, records)
        return record

    def get_history(self, session_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        records = self._read_records(session_id)
        if limit is not None and limit > 0:
            return records[-limit:]
        return records

    def clear_history(self, session_id: str) -> None:
        file_path = self._session_file(session_id)
        if file_path.exists():
            file_path.unlink()

    def last_message(self, session_id: str) -> dict[str, Any] | None:
        records = self._read_records(session_id)
        return records[-1] if records else None
