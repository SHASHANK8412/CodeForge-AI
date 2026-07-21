import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.project_manager")

class TaskScheduler:
    """
    Decides assignment agents and maps schedules chronologically.
    """

    def __init__(self) -> None:
        self.agent_map = {
            "database": "DatabaseAgent",
            "backend": "BackendAgent",
            "frontend": "FrontendAgent",
            "testing": "TestingAgent",
            "deployment": "DeploymentAgent",
            "documentation": "DocumentationAgent"
        }

    def schedule_tasks(self, ordered_tasks: List[str]) -> List[Dict[str, Any]]:
        schedule = []
        for idx, task in enumerate(ordered_tasks):
            schedule.append({
                "task_name": task,
                "assigned_agent": self.agent_map.get(task.lower(), "GeneralAgent"),
                "order": idx + 1,
                "status": "Pending"
            })
        return schedule
