"""
AIForge Day 27 — PostgreSQL Engineering Memory Repository
===========================================================
Persistent repository for Engineering Memories in PostgreSQL with versioning and project isolation.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.database.connection import SessionLocal
from backend.database.models import EngineeringMemoryModel
from backend.memory.models import EngineeringMemory, MemoryStatus, MemoryImportance, MemoryConfidence, MemoryType, MemorySource, MemoryVisibility

_logger = logging.getLogger("aiforge.database.repositories.memory")


class PostgresMemoryRepository:
    """
    PostgreSQL-backed persistent Engineering Memory repository.
    """

    def save(self, memory: EngineeringMemory) -> EngineeringMemory:
        db = SessionLocal()
        try:
            now_str = datetime.now().isoformat()
            tags_str = json.dumps(memory.tags or [])

            existing = db.query(EngineeringMemoryModel).filter(EngineeringMemoryModel.id == memory.id).first()
            if existing:
                existing.title = memory.title
                existing.content = memory.content
                existing.importance = memory.importance.value if hasattr(memory.importance, 'value') else str(memory.importance)
                existing.confidence = memory.confidence.value if hasattr(memory.confidence, 'value') else str(memory.confidence)
                existing.status = memory.status.value if hasattr(memory.status, 'value') else str(memory.status)
                existing.version = memory.version
                existing.tags_json = tags_str
                existing.updated_at = now_str
            else:
                record = EngineeringMemoryModel(
                    id=memory.id,
                    project_id=memory.project_id,
                    type=memory.type.value if hasattr(memory.type, 'value') else str(memory.type),
                    title=memory.title,
                    content=memory.content,
                    importance=memory.importance.value if hasattr(memory.importance, 'value') else str(memory.importance),
                    confidence=memory.confidence.value if hasattr(memory.confidence, 'value') else str(memory.confidence),
                    source=memory.source.value if hasattr(memory.source, 'value') else str(memory.source),
                    status=memory.status.value if hasattr(memory.status, 'value') else str(memory.status),
                    version=memory.version,
                    tags_json=tags_str,
                    created_at=memory.created_at or now_str,
                    updated_at=now_str
                )
                db.add(record)

            db.commit()
            _logger.info(f"[PostgresMemoryRepo] Saved memory '{memory.id}' for project '{memory.project_id}'")
            return memory
        except Exception as e:
            db.rollback()
            _logger.error(f"[PostgresMemoryRepo] Failed to save memory: {e}")
            raise e
        finally:
            db.close()

    def get(self, memory_id: str) -> Optional[EngineeringMemory]:
        db = SessionLocal()
        try:
            rec = db.query(EngineeringMemoryModel).filter(EngineeringMemoryModel.id == memory_id).first()
            if not rec:
                return None
            return self._to_domain(rec)
        finally:
            db.close()

    def get_by_project(self, project_id: str, active_only: bool = True) -> List[EngineeringMemory]:
        db = SessionLocal()
        try:
            query = db.query(EngineeringMemoryModel).filter(EngineeringMemoryModel.project_id == project_id)
            if active_only:
                query = query.filter(EngineeringMemoryModel.status == MemoryStatus.ACTIVE.value)

            records = query.all()
            return [self._to_domain(r) for r in records]
        finally:
            db.close()

    def _to_domain(self, rec: EngineeringMemoryModel) -> EngineeringMemory:
        tags = []
        if rec.tags_json:
            try:
                tags = json.loads(rec.tags_json)
            except Exception:
                tags = []

        return EngineeringMemory(
            id=rec.id,
            project_id=rec.project_id,
            type=MemoryType(rec.type) if rec.type in [e.value for e in MemoryType] else MemoryType.ARCHITECTURE_DECISION,
            title=rec.title,
            content=rec.content,
            importance=MemoryImportance(rec.importance) if rec.importance in [e.value for e in MemoryImportance] else MemoryImportance.HIGH,
            confidence=MemoryConfidence(rec.confidence) if rec.confidence in [e.value for e in MemoryConfidence] else MemoryConfidence.HIGH,
            source=MemorySource(rec.source) if rec.source in [e.value for e in MemorySource] else MemorySource.DEBATE,
            visibility=MemoryVisibility.USER_VISIBLE,
            status=MemoryStatus(rec.status) if rec.status in [e.value for e in MemoryStatus] else MemoryStatus.ACTIVE,
            version=rec.version or 1,
            created_at=rec.created_at or "",
            updated_at=rec.updated_at or "",
            tags=tags
        )


global_postgres_memory_repository = PostgresMemoryRepository()
