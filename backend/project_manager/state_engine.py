import json
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_manager")

class ProjectStateEngine:
    """
    Manages persistent state logging of completed, pending, blocked, and failed tasks
    inside 'project_state.json' in the workspace.
    """

    def __init__(self, state_file: str = None) -> None:
        if state_file is None:
            state_file = str(Path(__file__).resolve().parent / "project_state.json")
        self.state_file = Path(state_file)
        self._init_state_file()

    def _init_state_file(self) -> None:
        if not self.state_file.exists() or self.state_file.stat().st_size == 0:
            self.save_state({
                "project_name": "AIForge Managed Project",
                "status": "Planning",
                "completion_percentage": 0.0,
                "tasks": {}
            })

    def load_state(self) -> Dict[str, Any]:
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            _logger.error(f"Failed to load project_state.json: {str(e)}")
            return {"project_name": "AIForge Managed Project", "status": "Error", "completion_percentage": 0.0, "tasks": {}}

    def save_state(self, state: Dict[str, Any]) -> None:
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to write project_state.json: {str(e)}")

    def update_task(self, task_name: str, status: str, details: str = "") -> None:
        """
        Updates target task status: 'Pending', 'Completed', 'Blocked', 'Failed'.
        """
        state = self.load_state()
        tasks = state.setdefault("tasks", {})
        
        tasks[task_name] = {
            "status": status,
            "details": details
        }
        
        # Calculate completion percentage
        total = len(tasks)
        if total > 0:
            completed = sum(1 for t in tasks.values() if t.get("status") == "Completed")
            state["completion_percentage"] = round((completed / total) * 100.0, 1)

        self.save_state(state)
        _logger.info(f"Task '{task_name}' updated to status: {status}")
