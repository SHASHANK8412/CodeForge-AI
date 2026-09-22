"""
AIForge Day 22 — Importance Scoring Engine
===========================================
Calculates memory importance (CRITICAL, HIGH, MEDIUM, LOW) based on architectural impact,
security relevance, reuse frequency, and project criticality.
"""

import logging
from backend.memory.models import MemoryImportance, MemoryType

_logger = logging.getLogger("aiforge.memory.importance")


class ImportanceScoringEngine:
    """
    Calculates importance levels for memories.
    """

    def calculate_importance(self, mem_type: MemoryType, title: str, content: str) -> MemoryImportance:
        t_lower = title.lower() + " " + content.lower()

        if mem_type in (MemoryType.ARCHITECTURE_DECISION, MemoryType.SECURITY_LESSON) or "security" in t_lower or "critical" in t_lower:
            return MemoryImportance.CRITICAL

        if mem_type in (MemoryType.INCIDENT_LESSON, MemoryType.PERFORMANCE_LESSON, MemoryType.DEPLOYMENT_LESSON, MemoryType.FAILED_APPROACH, MemoryType.SUCCESSFUL_APPROACH):
            return MemoryImportance.HIGH

        if "spacing" in t_lower or "color" in t_lower or "minor" in t_lower:
            return MemoryImportance.LOW

        return MemoryImportance.MEDIUM


global_importance_scoring_engine = ImportanceScoringEngine()
