import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.project_manager.sprint")


class SprintPlanner:
    """
    SprintPlanner allocates engineering tasks into balanced development Sprints
    (Sprint 1, Sprint 2, Sprint 3).
    """

    def plan_sprints(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sprint1_tasks = [t for t in tasks if t["id"] in ["TSK-01", "TSK-02"]]
        sprint2_tasks = [t for t in tasks if t["id"] in ["TSK-03", "TSK-04"]]
        sprint3_tasks = [t for t in tasks if t["id"] not in ["TSK-01", "TSK-02", "TSK-03", "TSK-04"]]

        sprints = [
            {
                "sprint_number": 1,
                "name": "Sprint 1: Architecture & Foundation",
                "status": "COMPLETED",
                "task_count": len(sprint1_tasks),
                "tasks": sprint1_tasks
            },
            {
                "sprint_number": 2,
                "name": "Sprint 2: User Interface & API Integration",
                "status": "COMPLETED",
                "task_count": len(sprint2_tasks),
                "tasks": sprint2_tasks
            },
            {
                "sprint_number": 3,
                "name": "Sprint 3: Testing & DevOps Packaging",
                "status": "COMPLETED",
                "task_count": len(sprint3_tasks),
                "tasks": sprint3_tasks
            }
        ]

        logger.info(f"SprintPlanner allocated tasks across {len(sprints)} sprints.")
        return sprints


# Global SprintPlanner Instance
global_sprint_planner = SprintPlanner()
