"""
AIForge Project Memory Store
============================
Stores persistent historical project metadata, language stacks, frameworks, databases, and architectural patterns.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.knowledge.project_memory")


class ProjectMemoryStore:
    """
    Persistent store for historical project profiles and architectural patterns.
    """

    def __init__(self) -> None:
        self.projects: Dict[str, Dict[str, Any]] = {
            "proj_resume": {
                "project_id": "proj_resume",
                "project_name": "AI Resume Analyzer",
                "language": "Python",
                "framework": "FastAPI",
                "database": "PostgreSQL",
                "patterns": ["JWT", "REST API", "Docker", "Async Engine"],
                "created_at": time.time() - 86400 * 10
            },
            "proj_hospital": {
                "project_id": "proj_hospital",
                "project_name": "Hospital Management System",
                "language": "Python / TypeScript",
                "framework": "FastAPI + React",
                "database": "PostgreSQL",
                "patterns": ["FHIR Standards", "JWT Auth", "Docker Compose", "Redis Cache"],
                "created_at": time.time() - 86400 * 5
            }
        }

    def record_project_memory(
        self,
        project_name: str,
        language: str = "Python",
        framework: str = "FastAPI",
        database: str = "PostgreSQL",
        patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        p_id = f"proj_{int(time.time() * 1000)}"
        entry = {
            "project_id": p_id,
            "project_name": project_name,
            "language": language,
            "framework": framework,
            "database": database,
            "patterns": patterns or ["JWT Auth", "REST API", "Docker Container"],
            "created_at": time.time()
        }
        self.projects[p_id] = entry
        _logger.info(f"ProjectMemoryStore: Recorded memory for project '{project_name}'")
        return entry

    def get_all_projects(self) -> List[Dict[str, Any]]:
        return list(self.projects.values())

    def find_projects_by_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        pat_lower = pattern.lower()
        return [
            p for p in self.projects.values()
            if any(pat_lower in pt.lower() for pt in p.get("patterns", []))
        ]


global_project_memory_store = ProjectMemoryStore()
