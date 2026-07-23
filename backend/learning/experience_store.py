"""
AIForge Learning - Experience Store
==================================
Manages historical project generation records in memory/experiences.json.
Tracks successes, failures, retry histories, error tracebacks, applied fixes,
execution times, and project quality ratings.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning")


class ExperienceStore:
    """
    Persistent store for project generation experiences.
    """

    def __init__(self, memory_dir: Optional[str] = None) -> None:
        if memory_dir is None:
            memory_dir = str(Path(__file__).resolve().parents[1] / "memory")
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.memory_dir / "experiences.json"
        self._init_store()

    def _init_store(self) -> None:
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            default_experiences = [
                {
                    "id": "exp_init_1",
                    "project": "Food Delivery App",
                    "language": "React/FastAPI",
                    "architecture": "MERN",
                    "success": True,
                    "execution_time": 42.0,
                    "errors": ["Missing authentication"],
                    "fixes": ["Added JWT"],
                    "rating": 95.0,
                    "user_prompt": "Build Food Delivery App with JWT",
                    "timestamp": time.time() - 86400
                },
                {
                    "id": "exp_init_2",
                    "project": "Chat Application",
                    "language": "React/FastAPI",
                    "architecture": "React + FastAPI + Redis + Postgres",
                    "success": True,
                    "execution_time": 38.5,
                    "errors": [],
                    "fixes": [],
                    "rating": 98.0,
                    "user_prompt": "Build real-time chat app",
                    "timestamp": time.time() - 43200
                }
            ]
            self._save(default_experiences)

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            _logger.error(f"Failed to load experiences.json: {e}")
            return []

    def _save(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save experiences.json: {e}")

    def add_experience(
        self,
        project: str,
        language: str = "React/FastAPI",
        architecture: str = "FastAPI + React",
        success: bool = True,
        execution_time: float = 30.0,
        errors: Optional[List[str]] = None,
        fixes: Optional[List[str]] = None,
        rating: float = 95.0,
        user_prompt: str = ""
    ) -> Dict[str, Any]:
        experiences = self._load()
        exp_id = f"exp_{int(time.time() * 1000)}"
        record = {
            "id": exp_id,
            "project": project,
            "language": language,
            "architecture": architecture,
            "success": success,
            "execution_time": round(execution_time, 2),
            "errors": errors or [],
            "fixes": fixes or [],
            "rating": round(rating, 1),
            "user_prompt": user_prompt,
            "timestamp": time.time()
        }
        experiences.append(record)
        self._save(experiences)
        _logger.info(f"ExperienceStore: Recorded experience '{exp_id}' for project '{project}' (Success={success})")
        return record

    def get_all_experiences(self) -> List[Dict[str, Any]]:
        return self._load()

    def search_experiences(self, query: str) -> List[Dict[str, Any]]:
        query_words = set(query.lower().split())
        experiences = self._load()
        results = []
        for exp in experiences:
            text = f"{exp.get('project', '')} {exp.get('architecture', '')} {exp.get('user_prompt', '')} {' '.join(exp.get('errors', []))}".lower()
            if any(w in text for w in query_words):
                results.append(exp)
        return results

    def get_stats(self) -> Dict[str, Any]:
        experiences = self._load()
        total = len(experiences)
        if total == 0:
            return {
                "total_projects": 0,
                "success_count": 0,
                "success_rate_pct": 100.0,
                "avg_execution_time": 0.0,
                "total_errors": 0,
                "total_fixes": 0
            }

        success_count = sum(1 for e in experiences if e.get("success", True))
        avg_time = sum(e.get("execution_time", 30.0) for e in experiences) / total
        total_errors = sum(len(e.get("errors", [])) for e in experiences)
        total_fixes = sum(len(e.get("fixes", [])) for e in experiences)

        return {
            "total_projects": total,
            "success_count": success_count,
            "success_rate_pct": round((success_count / total) * 100.0, 1),
            "avg_execution_time": round(avg_time, 1),
            "total_errors": total_errors,
            "total_fixes": total_fixes
        }
