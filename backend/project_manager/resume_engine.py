import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.project_manager")

class ResumeEngine:
    """
    Identifies task states inside 'project_state.json' to decide hot resume strategies.
    """

    def __init__(self) -> None:
        pass

    def get_incomplete_tasks(self, state: Dict[str, Any]) -> List[str]:
        """
        Filters task keys returning those that are pending, blocked, or failed.
        """
        incomplete = []
        tasks = state.get("tasks", {})
        
        for name, info in tasks.items():
            status = info.get("status", "Pending")
            if status in ("Pending", "Failed", "Blocked"):
                incomplete.append(name)
                
        _logger.info(f"Resume Engine: found {len(incomplete)} incomplete tasks to continue.")
        return incomplete
