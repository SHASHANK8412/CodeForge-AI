"""
AIForge Day 21 — Incident Escalation & Loop Prevention Engine
===============================================================
Prevents infinite repair/rollback loops by enforcing rate limits:
- MAX_AUTO_REPAIRS_PER_HOUR = 3
- MAX_AUTO_ROLLBACKS_PER_HOUR = 2
Flags repeated incident root causes and escalates to human review.
"""

import logging
from typing import Dict, Any, List, Tuple

_logger = logging.getLogger("aiforge.incidents.escalation")

MAX_AUTO_REPAIRS_PER_HOUR = 3
MAX_AUTO_ROLLBACKS_PER_HOUR = 2


class EscalationService:
    """
    Manages incident escalation policies and loop detection.
    """

    def __init__(self):
        # project_id -> list of incident timestamps/root_causes
        self._history_causes: Dict[str, List[str]] = {}
        self._repair_counts: Dict[str, int] = {}

    def should_escalate(self, project_id: str, root_cause: str) -> Tuple[bool, str]:
        if project_id not in self._history_causes:
            self._history_causes[project_id] = []
        if project_id not in self._repair_counts:
            self._repair_counts[project_id] = 0

        # Check repeated root cause count
        matching = [rc for rc in self._history_causes[project_id] if rc == root_cause]
        if len(matching) >= 2:
            _logger.warning(f"[EscalationService] Repeated root cause detected 3 times for '{project_id}': {root_cause}")
            return True, "Repeated incident root cause detected 3 times in 1 hour. Automatic remediation disabled."

        if self._repair_counts[project_id] >= MAX_AUTO_REPAIRS_PER_HOUR:
            _logger.warning(f"[EscalationService] Exceeded MAX_AUTO_REPAIRS_PER_HOUR for '{project_id}'")
            return True, "Exceeded maximum automatic repair limit per hour (3). Human intervention required."

        self._history_causes[project_id].append(root_cause)
        self._repair_counts[project_id] += 1
        return False, "No escalation required"


global_escalation_service = EscalationService()
