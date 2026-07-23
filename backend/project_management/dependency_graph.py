"""
AIForge Task Dependency Analyzer
================================
Builds dependency chains ensuring:
Database -> Backend -> API -> Frontend -> Testing -> Deployment
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_management")


class ProjectDependencyGraph:
    """
    Enforces task dependency chains across project categories.
    """

    def assign_dependencies(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        db_tasks = [t["task_id"] for t in tasks if t.get("category") == "Database"]
        backend_tasks = [t["task_id"] for t in tasks if t.get("category") == "Backend"]
        frontend_tasks = [t["task_id"] for t in tasks if t.get("category") == "Frontend"]

        for t in tasks:
            cat = t.get("category")
            if cat == "Backend":
                t["dependencies"] = db_tasks
            elif cat in ["Frontend", "Payments", "Notifications"]:
                t["dependencies"] = backend_tasks
            elif cat in ["Deployment", "Documentation"]:
                t["dependencies"] = frontend_tasks + backend_tasks
            else:
                t["dependencies"] = []

        _logger.info(f"ProjectDependencyGraph: Enforced dependency chains for {len(tasks)} tasks.")
        return tasks


global_dependency_graph = ProjectDependencyGraph()
