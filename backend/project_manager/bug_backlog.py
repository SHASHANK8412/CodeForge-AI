import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.project_manager")

class BugBacklog:
    """
    Manages outstanding project bug reports and tracking statuses.
    """

    def __init__(self) -> None:
        self.bugs: List[Dict[str, Any]] = []

    def log_bug(self, title: str, severity: str, details: str = "") -> None:
        self.bugs.append({
            "title": title,
            "severity": severity,
            "details": details,
            "status": "Open"
        })
        _logger.warning(f"Logged backlog bug: '{title}' (Severity: {severity})")

    def resolve_bug(self, title: str) -> None:
        for bug in self.bugs:
            if bug["title"] == title:
                bug["status"] = "Resolved"
                _logger.info(f"Resolved backlog bug: '{title}'")
                break

    def get_open_bugs(self) -> List[Dict[str, Any]]:
        return [b for b in self.bugs if b["status"] == "Open"]
