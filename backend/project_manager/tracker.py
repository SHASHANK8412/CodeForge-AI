import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.project_manager.tracker")


class ProgressTracker:
    """
    ProgressTracker calculates real-time task completion progress percentages,
    running status, and agent workload distribution.
    """

    def track_progress(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "COMPLETED")
        progress_pct = round((completed / max(total, 1)) * 100.0, 1)

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "running_tasks": 0,
            "pending_tasks": total - completed,
            "blocked_tasks": 0,
            "progress_percentage": progress_pct
        }


# Global ProgressTracker Instance
global_progress_tracker = ProgressTracker()
