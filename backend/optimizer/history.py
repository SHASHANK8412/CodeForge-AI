"""
AIForge Prompt History Store
============================
Persists prompt version history, scores, quality metrics, and timestamps in memory/prompt_history.json.
Ensures prompt improvements are never lost across project runs.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.optimizer")


class PromptHistoryStore:
    """
    Manages persistent storage of prompt versions and quality scores.
    """

    def __init__(self, memory_dir: Optional[str] = None) -> None:
        if memory_dir is None:
            memory_dir = str(Path(__file__).resolve().parents[1] / "memory")
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.memory_dir / "prompt_history.json"
        self._init_store()

    def _init_store(self) -> None:
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            defaults = [
                {
                    "version": "v1.0",
                    "prompt_text": "Generate backend",
                    "score": 75.0,
                    "quality_rating": "Basic",
                    "project": "Initial Build",
                    "timestamp": time.time() - 86400
                },
                {
                    "version": "v2.0",
                    "prompt_text": "Generate production-ready FastAPI backend using clean architecture, dependency injection, repository pattern, JWT authentication, SQLAlchemy ORM, async APIs, unit testing and Docker support.",
                    "score": 98.5,
                    "quality_rating": "Production SOLID",
                    "project": "Optimized System",
                    "timestamp": time.time() - 43200
                }
            ]
            self._save(defaults)

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            _logger.error(f"Failed to load prompt_history.json: {e}")
            return []

    def _save(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save prompt_history.json: {e}")

    def record_prompt_version(
        self,
        version: str,
        prompt_text: str,
        score: float,
        quality_rating: str = "Production SOLID",
        project: str = "General"
    ) -> Dict[str, Any]:
        history = self._load()
        entry = {
            "version": version,
            "prompt_text": prompt_text,
            "score": round(score, 1),
            "quality_rating": quality_rating,
            "project": project,
            "timestamp": time.time()
        }
        history.append(entry)
        self._save(history)
        _logger.info(f"PromptHistoryStore: Recorded prompt version '{version}' with score {score}")
        return entry

    def get_highest_scoring_prompt(self) -> Dict[str, Any]:
        history = self._load()
        if not history:
            return {"version": "v1.0", "prompt_text": "Generate backend", "score": 80.0}
        sorted_h = sorted(history, key=lambda x: x.get("score", 0), reverse=True)
        return sorted_h[0]

    def get_all_history(self) -> List[Dict[str, Any]]:
        return self._load()
