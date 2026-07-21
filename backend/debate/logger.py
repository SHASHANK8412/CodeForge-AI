import logging
import time
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.debate")

class DebateLogger:
    """
    Manages structured SRE logging for Multi-Agent Debate sessions.
    """

    def __init__(self) -> None:
        self.logs: List[str] = []
        self.start_time = time.time()

    def log_event(self, event_name: str, details: Any = None) -> None:
        """
        Appends an event description to logs list and outputs it via the logger.
        """
        elapsed = time.time() - self.start_time
        log_str = f"[{elapsed:.2f}s] {event_name}"
        if details:
            log_str += f" | Details: {details}"
        self.logs.append(log_str)
        _logger.info(log_str)

    def log_round(self, round_num: int, message: str) -> None:
        self.log_event(f"ROUND {round_num}", message)

    def get_logs(self) -> List[str]:
        return self.logs
