"""
AIForge Day 22 — Memory Storage Repository & Versioning
=========================================================
Stores, updates, versions, and manages project-isolated memories.
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.memory.models import EngineeringMemory, MemoryStatus, MemoryVisibility
from backend.memory.policies import global_memory_security_policy

_logger = logging.getLogger("aiforge.memory.repository")


from backend.database.repositories.memory_repository import global_postgres_memory_repository


class MemoryRepository:
    """
    Project-isolated memory storage repository backed by PostgreSQL database with vector support.
    """

    def __init__(self):
        # memory_id -> EngineeringMemory
        self._memories: Dict[str, EngineeringMemory] = {}

    def save(self, memory: EngineeringMemory) -> EngineeringMemory:
        _, clean_content = global_memory_security_policy.sanitize_memory_content(memory.content)
        memory.content = clean_content
        now_str = datetime.now().isoformat()
        if not memory.created_at:
            memory.created_at = now_str
        memory.updated_at = now_str

        self._memories[memory.id] = memory

        try:
            global_postgres_memory_repository.save(memory)
        except Exception as e:
            _logger.warning(f"[MemoryRepo] Postgres save notice: {e}")

        _logger.info(f"[MemoryRepo] Saved memory '{memory.id}' ({memory.type.value}) for project '{memory.project_id}'")
        return memory

    def get(self, memory_id: str) -> Optional[EngineeringMemory]:
        if memory_id in self._memories:
            return self._memories[memory_id]
        try:
            mem = global_postgres_memory_repository.get(memory_id)
            if mem:
                self._memories[mem.id] = mem
                return mem
        except Exception:
            pass
        return None

    def get_by_project(self, project_id: str, active_only: bool = True) -> List[EngineeringMemory]:
        try:
            db_mems = global_postgres_memory_repository.get_by_project(project_id, active_only=active_only)
            for m in db_mems:
                self._memories[m.id] = m
            if db_mems:
                return db_mems
        except Exception:
            pass

        memories = [m for m in self._memories.values() if m.project_id == project_id]
        if active_only:
            memories = [m for m in memories if m.status == MemoryStatus.ACTIVE]
        return memories

    def update_version(self, old_memory_id: str, new_content: str, reason: str = "Migration") -> EngineeringMemory:
        old_mem = self.get(old_memory_id)
        if not old_mem:
            raise ValueError(f"Memory '{old_memory_id}' not found")

        old_mem.status = MemoryStatus.SUPERSEDED
        self.save(old_mem)

        new_mem = EngineeringMemory(
            id=f"mem_{secrets.token_urlsafe(6)}",
            project_id=old_mem.project_id,
            type=old_mem.type,
            title=old_mem.title,
            content=new_content,
            importance=old_mem.importance,
            confidence=old_mem.confidence,
            source=old_mem.source,
            visibility=old_mem.visibility,
            version=old_mem.version + 1,
            status=MemoryStatus.ACTIVE,
            tags=old_mem.tags,
            related_nodes=old_mem.related_nodes,
            related_memories=[old_mem.id] + old_mem.related_memories,
            metadata={"superseded_reason": reason}
        )

        return self.save(new_mem)


global_memory_repository = MemoryRepository()

