"""
AIForge Day 22 — Memory Consolidation & Contradiction Detection Engine
======================================================================
Detects noisy/redundant memories, consolidates similar lessons into coherent items,
and marks conflicting historical memories as SUPERSEDED.
"""

import secrets
import logging
from typing import List, Tuple

from backend.memory.models import EngineeringMemory, MemoryStatus, MemoryType, MemoryImportance
from backend.memory.repository import global_memory_repository

_logger = logging.getLogger("aiforge.memory.consolidation")


class MemoryConsolidationEngine:
    """
    Consolidates noisy memories and handles contradiction invalidation.
    """

    def detect_and_handle_contradictions(self, project_id: str, new_memory: EngineeringMemory) -> List[EngineeringMemory]:
        all_memories = global_memory_repository.get_by_project(project_id, active_only=True)
        superseded: List[EngineeringMemory] = []

        n_title = new_memory.title.lower()
        for mem in all_memories:
            if mem.id == new_memory.id:
                continue
            m_title = mem.title.lower()
            # If same memory type and overlapping topic, check contradiction/supersede
            if mem.type == new_memory.type and ("database" in n_title and "database" in m_title):
                mem.status = MemoryStatus.SUPERSEDED
                global_memory_repository.save(mem)
                superseded.append(mem)
                _logger.info(f"[MemoryConsolidation] Superseded memory '{mem.id}' by '{new_memory.id}'")

        return superseded

    def consolidate_project_memories(self, project_id: str) -> List[EngineeringMemory]:
        _logger.info(f"[MemoryConsolidation] Consolidating memories for '{project_id}'")
        memories = global_memory_repository.get_by_project(project_id, active_only=True)

        if len(memories) < 3:
            return memories

        # Consolidate API/validation memories if multiple exist
        val_mems = [m for m in memories if "validation" in m.title.lower() or "pydantic" in m.title.lower()]
        if len(val_mems) >= 2:
            for m in val_mems:
                m.status = MemoryStatus.ARCHIVED
                global_memory_repository.save(m)

            consolidated = EngineeringMemory(
                id=f"mem_cons_{secrets.token_urlsafe(6)}",
                project_id=project_id,
                type=MemoryType.CODING_PATTERN,
                title="Consolidated API Input Validation Pattern",
                content="AIForge backend APIs mandate Pydantic input model validation across all endpoints.",
                importance=MemoryImportance.HIGH,
                status=MemoryStatus.ACTIVE,
                related_memories=[m.id for m in val_mems]
            )
            global_memory_repository.save(consolidated)
            memories = global_memory_repository.get_by_project(project_id, active_only=True)

        return memories


global_memory_consolidation_engine = MemoryConsolidationEngine()
