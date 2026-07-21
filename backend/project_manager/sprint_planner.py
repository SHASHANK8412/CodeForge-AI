import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.project_manager")

class SprintPlanner:
    """
    Formulates structured sprint plans from plan lists based on files or modules complexity parameters.
    """

    def __init__(self) -> None:
        pass

    def generate_sprints(self, tasks: List[str]) -> List[Dict[str, Any]]:
        """
        Groups tasks list into Sprints (e.g. Sprint 1: Setup & DB, Sprint 2: Core backend, Sprint 3: UI frontend).
        """
        sprints: List[Dict[str, Any]] = []
        if not tasks:
            return sprints

        # Base tasks split
        chunks = [tasks[i:i + 3] for i in range(0, len(tasks), 3)]
        
        for idx, chunk in enumerate(chunks):
            sprints.append({
                "sprint_name": f"Sprint {idx + 1}",
                "status": "Planned" if idx > 0 else "In Progress",
                "tasks": chunk,
                "complexity": "Medium" if len(chunk) > 2 else "Low"
            })

        _logger.info(f"Structured {len(sprints)} sprints successfully.")
        return sprints
