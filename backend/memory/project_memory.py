"""
AIForge Project Memory Store
============================
Stores completed project memory: Name, Tech Stack, Performance Score, Success Status, Deployment, and Reuse Score.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.memory")


class ProjectMemoryStore:
    """
    Persistent store for completed project histories and reusable artifacts.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            mem_dir = Path(__file__).resolve().parent
            mem_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(mem_dir / "projects_memory.json")
        self.db_file = Path(db_path)
        self._init_memory()

    def _init_memory(self) -> None:
        if not self.db_file.exists():
            default_projects = [
                {
                    "project_id": "proj_001",
                    "project_name": "AI Resume Analyzer",
                    "tech_stack": ["FastAPI", "React", "MongoDB"],
                    "performance_score": 9.8,
                    "success_status": "Passed",
                    "deployment_status": "Successful",
                    "reuse_score_pct": 95.0,
                    "timestamp": time.time() - 86400 * 5
                }
            ]
            self._save_projects(default_projects)

    def _load_projects(self) -> List[Dict[str, Any]]:
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_projects(self, projects: List[Dict[str, Any]]) -> None:
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(projects, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save projects_memory.json: {e}")

    def store_project(
        self,
        project_name: str,
        tech_stack: List[str],
        performance_score: float = 9.5,
        success_status: str = "Passed",
        deployment_status: str = "Successful",
        reuse_score_pct: float = 95.0
    ) -> Dict[str, Any]:
        projects = self._load_projects()
        rec = {
            "project_id": f"proj_{len(projects) + 1:03d}",
            "project_name": project_name,
            "tech_stack": tech_stack,
            "performance_score": performance_score,
            "success_status": success_status,
            "deployment_status": deployment_status,
            "reuse_score_pct": reuse_score_pct,
            "timestamp": time.time()
        }
        projects.append(rec)
        self._save_projects(projects)
        _logger.info(f"ProjectMemoryStore: Stored project '{project_name}' (Reuse Score={reuse_score_pct}%)")
        return rec

    def get_all_projects(self) -> List[Dict[str, Any]]:
        return self._load_projects()


global_project_memory = ProjectMemoryStore()
