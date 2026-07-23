"""
AIForge Sprint Progress Tracker
===============================
Tracks live sprint progress:
Displays Completed Tasks, Running Tasks, Waiting Tasks, Failed Tasks,
Overall Completion Percentage (%), and Estimated Remaining Time (seconds).
"""

import logging
from typing import Dict, Any, List
from backend.sprint.task import SprintTask

_logger = logging.getLogger("aiforge.sprint")


class SprintProgressTracker:
    """
    Tracks live task statuses and calculates sprint completion percentage.
    """

    def get_progress_metrics(self, tasks: List[SprintTask]) -> Dict[str, Any]:
        total = len(tasks)
        if total == 0:
            return {
                "completed_tasks": 0,
                "running_tasks": 0,
                "waiting_tasks": 0,
                "failed_tasks": 0,
                "overall_completion_pct": 100.0,
                "estimated_remaining_time_seconds": 0.0
            }

        completed = sum(1 for t in tasks if t.status == "Completed")
        running = sum(1 for t in tasks if t.status == "Running")
        waiting = sum(1 for t in tasks if t.status in ["Pending", "Assigned", "Retry"])
        failed = sum(1 for t in tasks if t.status == "Failed")

        completion_pct = round((completed / total) * 100.0, 1)
        remaining_time = sum(t.estimated_time_seconds for t in tasks if t.status != "Completed")

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "running_tasks": running,
            "waiting_tasks": waiting,
            "failed_tasks": failed,
            "overall_completion_pct": completion_pct,
            "estimated_remaining_time_seconds": round(remaining_time, 1)
        }
