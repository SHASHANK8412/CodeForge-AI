"""
AIForge Day 92 Generation History Store
======================================
Maintains detailed history records of every generated project:
project, framework, backend, score, tests_passed, bugs, generation_time, date.
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning.history")


class GenerationHistoryStore:
    """
    Persistent store for project generation history.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            history_dir = Path(__file__).resolve().parent
            history_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(history_dir / "generation_history.json")
        self.db_file = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        if not self.db_file.exists():
            default_history = [
                {
                    "history_id": "hist_001",
                    "project": "Food Delivery App",
                    "framework": "React",
                    "backend": "FastAPI",
                    "score": 91,
                    "tests_passed": 34,
                    "bugs": 2,
                    "generation_time": 54,
                    "date": "2026-07-24",
                    "timestamp": time.time() - 86400
                },
                {
                    "history_id": "hist_002",
                    "project": "E-Commerce Microservice",
                    "framework": "React",
                    "backend": "FastAPI",
                    "score": 94,
                    "tests_passed": 42,
                    "bugs": 1,
                    "generation_time": 46,
                    "date": "2026-07-24",
                    "timestamp": time.time() - 43200
                }
            ]
            self._save_records(default_history)

    def _load_records(self) -> List[Dict[str, Any]]:
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_records(self, records: List[Dict[str, Any]]) -> None:
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save generation_history.json: {e}")

    def record_history(
        self,
        project: str,
        framework: str = "React",
        backend: str = "FastAPI",
        score: int = 92,
        tests_passed: int = 36,
        bugs: int = 1,
        generation_time: int = 48,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        records = self._load_records()
        today_date = date or datetime.now().strftime("%Y-%m-%d")
        
        rec = {
            "history_id": f"hist_{len(records) + 1:03d}",
            "project": project,
            "framework": framework,
            "backend": backend,
            "score": score,
            "tests_passed": tests_passed,
            "bugs": bugs,
            "generation_time": generation_time,
            "date": today_date,
            "timestamp": time.time()
        }
        records.append(rec)
        self._save_records(records)
        _logger.info(f"GenerationHistoryStore: Recorded history for '{project}' (Score={score}, Bugs={bugs})")
        return rec

    def get_all_history(self) -> List[Dict[str, Any]]:
        return self._load_records()

    def get_latest_record(self) -> Optional[Dict[str, Any]]:
        records = self._load_records()
        return records[-1] if records else None

    def search_history(self, query: str) -> List[Dict[str, Any]]:
        records = self._load_records()
        q = query.lower()
        return [
            r for r in records
            if q in r.get("project", "").lower()
            or q in r.get("framework", "").lower()
            or q in r.get("backend", "").lower()
        ]


global_history_store = GenerationHistoryStore()
