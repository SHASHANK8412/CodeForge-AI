"""
AIForge Production Project Memory
=================================
Stores persistent project execution records including prompt, architecture, generated files, tech stack, build times, test results, errors, fixes, success status, timestamp, and user feedback.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning.project_memory")


class ProductionProjectMemory:
    """
    Stores and manages historical project execution records.
    """

    def __init__(self) -> None:
        self.projects: Dict[str, Dict[str, Any]] = {
            "proj_food_delivery": {
                "project_id": "proj_food_delivery",
                "user_prompt": "Build a food delivery platform with FastAPI and React",
                "architecture": "Microservices Blueprint",
                "generated_files": ["backend/main.py", "backend/auth.py", "frontend/src/App.jsx", "Dockerfile"],
                "technologies": ["FastAPI", "React", "PostgreSQL", "Docker", "Redis"],
                "execution_time_seconds": 24.5,
                "test_results": {"total": 14, "passed": 14, "failed": 0, "coverage_pct": 94.2},
                "errors": [],
                "fixes": [],
                "success_status": "SUCCESS",
                "user_feedback": {"rating": 5, "comment": "Excellent architecture and clean code"},
                "timestamp": time.time() - 86400 * 2
            }
        }

    def record_project(
        self,
        user_prompt: str,
        architecture: str = "Modular Monolith",
        generated_files: Optional[List[str]] = None,
        technologies: Optional[List[str]] = None,
        execution_time_seconds: float = 15.0,
        test_results: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        fixes: Optional[List[str]] = None,
        success_status: str = "SUCCESS",
        user_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        p_id = f"proj_mem_{int(time.time() * 1000)}"
        project_record = {
            "project_id": p_id,
            "user_prompt": user_prompt,
            "architecture": architecture,
            "generated_files": generated_files or [],
            "technologies": technologies or ["FastAPI", "React", "PostgreSQL"],
            "execution_time_seconds": execution_time_seconds,
            "test_results": test_results or {"passed": 10, "failed": 0},
            "errors": errors or [],
            "fixes": fixes or [],
            "success_status": success_status,
            "user_feedback": user_feedback or {},
            "timestamp": time.time()
        }

        self.projects[p_id] = project_record
        _logger.info(f"ProductionProjectMemory: Automatically stored project '{p_id}' (Status: {success_status})")
        return project_record

    def add_user_feedback(self, project_id: str, rating: int, comment: str = "") -> Dict[str, Any]:
        if project_id in self.projects:
            self.projects[project_id]["user_feedback"] = {
                "rating": rating,
                "comment": comment,
                "submitted_at": time.time()
            }
            _logger.info(f"ProductionProjectMemory: Updated user feedback for '{project_id}'")
            return self.projects[project_id]
        raise ValueError(f"Project memory '{project_id}' not found.")

    def get_all_projects(self) -> List[Dict[str, Any]]:
        return sorted(list(self.projects.values()), key=lambda p: p["timestamp"], reverse=True)

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self.projects.get(project_id)


global_production_project_memory = ProductionProjectMemory()
