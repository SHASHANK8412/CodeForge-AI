"""
AIForge Learning Database & Pattern Store
=========================================
Manages persistent learning database (patterns.db / patterns_store.json).
Stores best prompts, folder structures, APIs, authentication, UI patterns, and testing strategies.
Maintains pattern leaderboard with rating scores (React Arch: 97, FastAPI: 95, Auth: 98, Docker: 96).
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning.storage")


class LearningDatabaseStore:
    """
    Persistent Learning Database Store for reusable patterns and leaderboards.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            storage_dir = Path(__file__).resolve().parent
            storage_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(storage_dir / "patterns_store.json")
        self.db_file = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        if not self.db_file.exists():
            default_data = {
                "patterns": [
                    {
                        "pattern_id": "pat_001",
                        "name": "Authentication Pattern",
                        "category": "authentication",
                        "score": 98,
                        "description": "JWT Stateless Authentication Controller & Middleware",
                        "content": "from fastapi import Depends, HTTPException, status\n..."
                    },
                    {
                        "pattern_id": "pat_002",
                        "name": "React Architecture",
                        "category": "frontend",
                        "score": 97,
                        "description": "Modular Component & Service Layer Architecture",
                        "content": "export function Component() { ... }"
                    },
                    {
                        "pattern_id": "pat_003",
                        "name": "Docker Pattern",
                        "category": "devops",
                        "score": 96,
                        "description": "Multi-stage Dockerfile & compose setup",
                        "content": "FROM node:18-alpine AS builder..."
                    },
                    {
                        "pattern_id": "pat_004",
                        "name": "FastAPI Boilerplate",
                        "category": "backend",
                        "score": 95,
                        "description": "Scalable REST API with Dependency Injection",
                        "content": "from fastapi import FastAPI, APIRouter..."
                    }
                ],
                "prompts": [
                    {
                        "prompt_id": "prm_001",
                        "role": "backend",
                        "score": 96,
                        "text": "Generate a scalable FastAPI backend using dependency injection, JWT authentication, logging, error handling, Swagger, unit tests, Docker, and production-ready architecture."
                    }
                ]
            }
            self._save_db(default_data)

    def _load_db(self) -> Dict[str, Any]:
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"patterns": [], "prompts": []}

    def _save_db(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save patterns_store.json: {e}")

    def add_pattern(
        self,
        name: str,
        category: str,
        score: int = 95,
        description: str = "",
        content: str = ""
    ) -> Dict[str, Any]:
        db = self._load_db()
        pat = {
            "pattern_id": f"pat_{len(db['patterns']) + 1:03d}",
            "name": name,
            "category": category,
            "score": score,
            "description": description,
            "content": content
        }
        db["patterns"].append(pat)
        self._save_db(db)
        _logger.info(f"LearningDatabaseStore: Stored pattern '{name}' (Score={score})")
        return pat

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        db = self._load_db()
        patterns = db.get("patterns", [])
        return sorted(patterns, key=lambda x: x.get("score", 0), reverse=True)

    def get_all_patterns(self) -> List[Dict[str, Any]]:
        return self._load_db().get("patterns", [])

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        return self._load_db().get("prompts", [])


global_learning_db = LearningDatabaseStore()
