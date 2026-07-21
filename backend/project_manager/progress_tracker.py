import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.project_manager")

class ProgressTracker:
    """
    Computes overall project progress based on task states checklist.
    """

    def __init__(self) -> None:
        pass

    def calculate_progress(self, tasks: Dict[str, Dict[str, Any]]) -> float:
        if not tasks:
            return 0.0
        
        total = len(tasks)
        completed = sum(1 for info in tasks.values() if info.get("status") == "Completed")
        
        progress = (completed / total) * 100.0
        return round(progress, 1)
