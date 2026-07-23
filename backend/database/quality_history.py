"""
AIForge Quality History Database Store
======================================
Stores and retrieves historical project quality records:
Project, Timestamp, Quality, Latency, LLM, Tokens, Errors, Retries, Overall Score.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.database")


class QualityHistoryDB:
    """
    Persistent store for historical project quality metrics.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_dir = Path(__file__).resolve().parent
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "quality_history.json")
        self.db_file = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        if not self.db_file.exists():
            default_records = [
                {
                    "project_name": "E-Commerce Microservice",
                    "timestamp": time.time() - 86400 * 7,
                    "overall_score": 88.5,
                    "latency_ms": 1420,
                    "llm_model": "qwen2.5-coder:latest",
                    "tokens_used": 11200,
                    "errors_count": 1,
                    "retries": 1
                },
                {
                    "project_name": "Enterprise SaaS CRM",
                    "timestamp": time.time() - 86400 * 2,
                    "overall_score": 94.3,
                    "latency_ms": 980,
                    "llm_model": "qwen2.5-coder:latest",
                    "tokens_used": 12800,
                    "errors_count": 0,
                    "retries": 0
                }
            ]
            self._save_records(default_records)

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
            _logger.error(f"Failed to save quality_history.json: {e}")

    def add_record(
        self,
        project_name: str,
        overall_score: float,
        latency_ms: int = 1200,
        llm_model: str = "qwen2.5-coder:latest",
        tokens_used: int = 12500,
        errors_count: int = 0,
        retries: int = 0
    ) -> Dict[str, Any]:
        records = self._load_records()
        rec = {
            "project_name": project_name,
            "timestamp": time.time(),
            "overall_score": overall_score,
            "latency_ms": latency_ms,
            "llm_model": llm_model,
            "tokens_used": tokens_used,
            "errors_count": errors_count,
            "retries": retries
        }
        records.append(rec)
        self._save_records(records)
        _logger.info(f"QualityHistoryDB: Recorded history for '{project_name}' (Score={overall_score}%)")
        return rec

    def get_all_records(self) -> List[Dict[str, Any]]:
        return self._load_records()


global_quality_history_db = QualityHistoryDB()
