"""
AIForge Workspace Priority Manager
==================================
Manages project and task prioritization levels, dynamic priority escalation, and queue ordering.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.workspace.priorities")


class PriorityManager:
    """
    Handles priority levels and dynamic queue ordering across projects.
    """

    ALLOWED_PRIORITIES = ["Critical", "High", "Medium", "Low"]

    def __init__(self) -> None:
        self.project_priorities: Dict[str, str] = {
            "proj_ecommerce": "High",
            "proj_hospital": "Critical",
            "proj_airesume": "Medium",
            "proj_crm": "Low"
        }

    def get_project_priority(self, project_id: str) -> str:
        return self.project_priorities.get(project_id, "Medium")

    def set_project_priority(self, project_id: str, priority: str) -> Dict[str, Any]:
        if priority not in self.ALLOWED_PRIORITIES:
            raise ValueError(f"Invalid priority '{priority}'. Allowed: {self.ALLOWED_PRIORITIES}")
        
        old_p = self.get_project_priority(project_id)
        self.project_priorities[project_id] = priority
        _logger.info(f"PriorityManager: Project '{project_id}' priority changed from '{old_p}' to '{priority}'")

        return {
            "project_id": project_id,
            "old_priority": old_p,
            "new_priority": priority
        }

    def get_all_priorities(self) -> Dict[str, str]:
        return dict(self.project_priorities)

    def sort_tasks_by_priority(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        weights = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        return sorted(tasks, key=lambda t: weights.get(t.get("priority", "Medium"), 1), reverse=True)


global_priority_manager = PriorityManager()
