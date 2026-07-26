import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.debugging.logger")


class DebugLogger:
    """
    DebugLogger stores structured execution, self-healing, and diagnostic logs for projects.
    """

    def __init__(self):
        self.logs_history: Dict[str, List[Dict[str, Any]]] = {}

    def log_execution(self, project_id: str, entry: Dict[str, Any]) -> None:
        logs = self.logs_history.setdefault(project_id, [])
        entry["timestamp"] = time.time()
        logs.append(entry)

    def get_logs(self, project_id: str) -> List[Dict[str, Any]]:
        return self.logs_history.get(project_id, [])


# Global DebugLogger Instance
global_debug_logger = DebugLogger()
