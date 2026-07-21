import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.project_manager")

class DecisionStore:
    """
    Stores Architecture Decision Records (ADR) detailing technology selections.
    """

    def __init__(self) -> None:
        self.decisions: List[Dict[str, Any]] = []

    def record_decision(self, title: str, choice: str, status: str = "Accepted", justification: str = "") -> None:
        self.decisions.append({
            "title": title,
            "choice": choice,
            "status": status,
            "justification": justification
        })
        _logger.info(f"Recorded SRE ADR decision: '{title}' -> {choice} ({status})")

    def get_decisions(self) -> List[Dict[str, Any]]:
        return self.decisions
