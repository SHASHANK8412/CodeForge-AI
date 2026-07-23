"""
AIForge Workspace State Manager
===============================
Tracks global workspace state, active project context, running tasks, agent statuses,
and token metrics across multiple simultaneous software projects.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.workspace")


class WorkspaceStateManager:
    """
    Manages active project context and global system state metrics.
    """

    def __init__(self) -> None:
        self.active_project_id: Optional[str] = None
        self.agent_statuses: Dict[str, str] = {
            "Planner": "IDLE",
            "Architect": "IDLE",
            "Backend": "IDLE",
            "Frontend": "IDLE",
            "Testing": "IDLE",
            "Reviewer": "IDLE",
            "DevOps": "IDLE"
        }
        self.total_tokens_used: int = 145000
        self.active_tasks_queue: List[Dict[str, Any]] = []

    def set_active_project(self, project_id: str) -> str:
        self.active_project_id = project_id
        _logger.info(f"WorkspaceStateManager: Active project set to '{project_id}'")
        return project_id

    def update_agent_status(self, agent_name: str, status: str) -> None:
        self.agent_statuses[agent_name] = status

    def get_status_summary(self) -> Dict[str, Any]:
        return {
            "active_project_id": self.active_project_id,
            "agent_statuses": self.agent_statuses,
            "total_tokens_used": self.total_tokens_used,
            "queued_tasks_count": len(self.active_tasks_queue),
            "system_health": "ONLINE"
        }


global_workspace_state = WorkspaceStateManager()
