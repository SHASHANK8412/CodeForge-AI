"""
AIForge Day 92 Failure Learning & Prompt Improvement Engine
===========================================================
Failure Learning:
Stores failure problems and fix strategies (e.g. Problem: "JWT Middleware Missing", Fix: "Always generate middleware before routes").

Prompt Improvement:
Transforms short/vague prompts ("Generate backend") into production-grade enhanced prompts
("Generate a scalable FastAPI backend using dependency injection, JWT authentication, logging, error handling, Swagger, unit tests, Docker, and production-ready architecture.").
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning.improvement")


class ImprovementEngine:
    """
    Failure Learning & Prompt Improvement Engine.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            imp_dir = Path(__file__).resolve().parent
            imp_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(imp_dir / "failure_fixes_store.json")
        self.db_file = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        if not self.db_file.exists():
            default_failures = [
                {
                    "failure_id": "fail_001",
                    "problem": "Authentication broken / JWT Middleware Missing",
                    "fix": "Always generate JWT middleware before routes",
                    "category": "authentication",
                    "times_applied": 14
                },
                {
                    "failure_id": "fail_002",
                    "problem": "CORS Error on frontend requests",
                    "fix": "Set allow_origins=['*'] and allow_credentials=True in FastAPI CORSMiddleware",
                    "category": "security",
                    "times_applied": 22
                }
            ]
            self._save_failures(default_failures)

    def _load_failures(self) -> List[Dict[str, Any]]:
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_failures(self, records: List[Dict[str, Any]]) -> None:
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save failure_fixes_store.json: {e}")

    def record_failure(
        self,
        problem: str,
        fix: str,
        category: str = "general"
    ) -> Dict[str, Any]:
        failures = self._load_failures()
        rec = {
            "failure_id": f"fail_{len(failures) + 1:03d}",
            "problem": problem,
            "fix": fix,
            "category": category,
            "times_applied": 1
        }
        failures.append(rec)
        self._save_failures(failures)
        _logger.info(f"ImprovementEngine: Recorded failure fix '{problem}' -> '{fix}'")
        return rec

    def get_all_failures(self) -> List[Dict[str, Any]]:
        return self._load_failures()

    def improve_prompt(self, base_prompt: str) -> str:
        _logger.info(f"ImprovementEngine: Optimizing prompt '{base_prompt}'...")

        if "backend" in base_prompt.lower() and len(base_prompt.split()) <= 5:
            return (
                "Generate a scalable FastAPI backend using dependency injection, "
                "JWT authentication, logging, error handling, Swagger, unit tests, "
                "Docker, and production-ready architecture."
            )

        enhanced = base_prompt.strip()
        additions = []
        if "jwt" not in enhanced.lower() and "auth" not in enhanced.lower():
            additions.append("JWT authentication & middleware")
        if "test" not in enhanced.lower():
            additions.append("comprehensive unit tests")
        if "docker" not in enhanced.lower():
            additions.append("Docker containerization")

        if additions:
            enhanced += f" (Enhanced with {', '.join(additions)} and production-ready clean architecture)."

        return enhanced


global_improvement_engine = ImprovementEngine()
