from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class VectorMemory:

    def __init__(self, storage_root: Path | None = None):
        self.storage_root = storage_root or Path(__file__).resolve().parent / "store" / "vectors"
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

    def add_text(self, session_id: str, text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "text": text,
            "metadata": metadata or {},
        }

        records = self._read_records(session_id)
        records.append(record)
        self._write_records(session_id, records)
        return record

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _cosine_similarity(self, left: str, right: str) -> float:
        left_tokens = Counter(self._tokenize(left))
        right_tokens = Counter(self._tokenize(right))

        if not left_tokens or not right_tokens:
            return 0.0

        common = set(left_tokens) & set(right_tokens)
        numerator = sum(left_tokens[token] * right_tokens[token] for token in common)
        left_norm = math.sqrt(sum(value * value for value in left_tokens.values()))
        right_norm = math.sqrt(sum(value * value for value in right_tokens.values()))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return numerator / (left_norm * right_norm)

    def search(self, session_id: str, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        records = self._read_records(session_id)
        scored_records = []

        for record in records:
            score = self._cosine_similarity(query, record.get("text", ""))
            if score > 0:
                scored_records.append({**record, "score": round(score, 4)})

        scored_records.sort(key=lambda item: item["score"], reverse=True)
        return scored_records[:top_k]

    def clear(self, session_id: str) -> None:
        file_path = self._session_file(session_id)
        if file_path.exists():
            file_path.unlink()
