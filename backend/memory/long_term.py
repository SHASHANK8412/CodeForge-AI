import os
import json
import time
import math
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aiforge.memory.long_term")

PERSIST_FILE = Path(__file__).resolve().parent / "projects_memory.json"


class LongTermMemory:
    """
    LongTermMemory manages persistent long-term storage for completed and ongoing projects,
    user preferences, architecture decisions, and generated code files across sessions.
    """

    def __init__(self, storage_file: Path = PERSIST_FILE):
        self.storage_file = storage_file
        self.projects: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_file.exists():
            try:
                data = json.loads(self.storage_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.projects = data
            except Exception as e:
                logger.warning(f"Could not load long term memory from file: {e}")
                self.projects = {}

    def _save(self) -> None:
        try:
            self.storage_file.write_text(json.dumps(self.projects, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Could not save long term memory to file: {e}")

    def save_project(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates a project's long-term memory record."""
        now = time.time()
        existing = self.projects.get(project_id, {})

        record = {
            "project_id": project_id,
            "name": data.get("name", existing.get("name", "Untitled Project")),
            "prompt": data.get("prompt", existing.get("prompt", "")),
            "tech_stack": data.get("tech_stack", existing.get("tech_stack", {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL",
                "auth": "JWT"
            })),
            "architecture": data.get("architecture", existing.get("architecture", {})),
            "database_schema": data.get("database_schema", existing.get("database_schema", "")),
            "generated_files": data.get("generated_files", existing.get("generated_files", {})),
            "user_preferences": data.get("user_preferences", existing.get("user_preferences", {})),
            "version": data.get("version", existing.get("version", "v1")),
            "created_at": existing.get("created_at", now),
            "updated_at": now
        }

        self.projects[project_id] = record
        self._save()
        logger.info(f"LongTermMemory saved project '{project_id}' ({record['name']})")
        return record

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves long-term memory for a specific project."""
        return self.projects.get(project_id)

    def list_projects(self) -> List[Dict[str, Any]]:
        """Lists all stored project records ordered by updated_at descending."""
        records = list(self.projects.values())
        records.sort(key=lambda p: p.get("updated_at", 0), reverse=True)
        return records

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates specific fields of an existing project record."""
        if project_id not in self.projects:
            return None
        self.projects[project_id].update(updates)
        self.projects[project_id]["updated_at"] = time.time()
        self._save()
        return self.projects[project_id]

    def delete_project(self, project_id: str) -> bool:
        """Deletes a project record from long-term memory."""
        if project_id in self.projects:
            del self.projects[project_id]
            self._save()
            return True
        return False

    def search_semantic(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Performs semantic relevance search over stored project titles, prompts, and tech stacks."""
        if not self.projects:
            return []

        query_words = set(query.lower().split())
        results = []

        for p_id, p_data in self.projects.items():
            text_corpus = (
                f"{p_data.get('name', '')} {p_data.get('prompt', '')} "
                f"{json.dumps(p_data.get('tech_stack', {}))} {p_data.get('database_schema', '')}"
            ).lower()

            matches = sum(1 for w in query_words if w in text_corpus)
            score = round(matches / max(len(query_words), 1), 4)

            results.append({
                "score": score,
                "project": p_data
            })

        results.sort(key=lambda r: r["score"], reverse=True)
        return [r["project"] for r in results[:top_k]]


# Global LongTermMemory instance
global_long_term_memory = LongTermMemory()
