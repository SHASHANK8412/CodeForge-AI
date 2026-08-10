"""
AIForge Day 22 — Centralized EngineeringMemoryService
=====================================================
Manages long-term engineering memory lifecycle (remember, retrieve, search, update, forget,
consolidate, promote, link, get_context), MemoryContextBuilder, feedback scoring, and Flight Recorder logging.
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.memory.models import (
    EngineeringMemory, MemoryType, MemoryImportance, MemoryConfidence,
    MemorySource, MemoryStatus, MemoryVisibility, MemoryContext, MemoryQualityScore
)
from backend.memory.repository import global_memory_repository
from backend.memory.importance import global_importance_scoring_engine
from backend.memory.retrieval import global_memory_retrieval_engine
from backend.memory.consolidation import global_memory_consolidation_engine
from backend.memory.graph import global_knowledge_graph_engine
from backend.autopilot.recorder import global_flight_recorder

_logger = logging.getLogger("aiforge.memory.service")


class EngineeringMemoryService:
    """
    Centralized service for Long-Term Engineering Memory & Knowledge Graph.
    """

    def remember(
        self,
        project_id: str,
        title: str,
        content: str,
        mem_type: MemoryType = MemoryType.ARCHITECTURE_DECISION,
        source: MemorySource = MemorySource.DEBATE,
        confidence: MemoryConfidence = MemoryConfidence.HIGH,
        tags: Optional[List[str]] = None,
        related_nodes: Optional[List[str]] = None
    ) -> EngineeringMemory:
        _logger.info(f"[EngineeringMemoryService] Remembering '{title}' for project '{project_id}'")

        try:
            global_flight_recorder.record_event(project_id, "MemoryEngine", "memory_created", {"title": title, "type": mem_type.value})
        except Exception:
            pass

        importance = global_importance_scoring_engine.calculate_importance(mem_type, title, content)
        mem_id = f"mem_{secrets.token_urlsafe(6)}"

        memory = EngineeringMemory(
            id=mem_id,
            project_id=project_id,
            type=mem_type,
            title=title,
            content=content,
            importance=importance,
            confidence=confidence,
            source=source,
            visibility=MemoryVisibility.USER_VISIBLE,
            version=1,
            status=MemoryStatus.ACTIVE,
            created_at=datetime.now().isoformat(),
            tags=tags or [],
            related_nodes=related_nodes or []
        )

        saved = global_memory_repository.save(memory)
        # Check and supersede conflicting historical memories
        global_memory_consolidation_engine.detect_and_handle_contradictions(project_id, saved)

        # Index vector embedding in pgvector / PostgresVectorStore
        try:
            from backend.rag.embedding_service import global_embedding_service
            from backend.database.service import global_database_service

            text_to_embed = f"{title}\n{content}"
            embeddings = global_embedding_service.embed_batch([text_to_embed])
            if embeddings:

                global_database_service.vector_store.add(
                    documents=[{
                        "id": saved.id,
                        "text": text_to_embed,
                        "source": "engineering_memory",
                        "document_type": "ENGINEERING_MEMORY",
                        "title": title,
                        "type": mem_type.value
                    }],
                    embeddings=embeddings,
                    project_id=project_id
                )
        except Exception as e:
            _logger.warning(f"[EngineeringMemoryService] Vector indexing notice: {e}")

        return saved


    def retrieve(
        self,
        project_id: str,
        task_query: str,
        agent_type: str = "Backend",
        top_k: int = 5
    ) -> List[EngineeringMemory]:
        mems = global_memory_retrieval_engine.retrieve_contextual_memories(project_id, task_query, agent_type, top_k)
        for m in mems:
            m.usage_count += 1
            m.last_used_at = datetime.now().isoformat()
            global_memory_repository.save(m)
            try:
                global_flight_recorder.record_event(project_id, "MemoryEngine", "memory_retrieved", {"mem_id": m.id, "agent": agent_type})
            except Exception:
                pass
        return mems

    def search(self, project_id: str, query: str) -> List[EngineeringMemory]:
        q_lower = query.lower()
        all_m = global_memory_repository.get_by_project(project_id, active_only=False)
        exact_matches = [m for m in all_m if q_lower in m.title.lower() or q_lower in m.content.lower()]
        if exact_matches:
            return exact_matches

        # Keyword match
        words = [w for w in q_lower.split() if len(w) > 3]
        if words:
            kw_matches = [m for m in all_m if any(w in m.title.lower() or w in m.content.lower() for w in words)]
            if kw_matches:
                return kw_matches

        # Semantic similarity search fallback
        try:
            from backend.rag.embedding_service import global_embedding_service
            from backend.database.service import global_database_service

            q_emb = global_embedding_service.embed_query(query)
            vec_res = global_database_service.vector_store.search(q_emb, project_id=project_id, top_k=5)
            doc_ids = set(r["id"] for r in vec_res)
            return [m for m in all_m if m.id in doc_ids]
        except Exception:
            return []


    def update(self, memory_id: str, new_content: str, reason: str = "Migration") -> EngineeringMemory:
        updated = global_memory_repository.update_version(memory_id, new_content, reason)
        try:
            global_flight_recorder.record_event(updated.project_id, "MemoryEngine", "memory_updated", {"mem_id": updated.id, "version": updated.version})
        except Exception:
            pass
        return updated

    def forget(self, memory_id: str) -> bool:
        mem = global_memory_repository.get(memory_id)
        if not mem:
            return False
        mem.status = MemoryStatus.ARCHIVED
        global_memory_repository.save(mem)
        try:
            global_flight_recorder.record_event(mem.project_id, "MemoryEngine", "memory_archived", {"mem_id": memory_id})
        except Exception:
            pass
        return True

    def consolidate(self, project_id: str) -> List[EngineeringMemory]:
        return global_memory_consolidation_engine.consolidate_project_memories(project_id)

    def get_context(self, project_id: str, task: str, agent_type: str) -> MemoryContext:
        mems = self.retrieve(project_id, task, agent_type, top_k=5)
        return MemoryContext(project_id=project_id, task=task, agent_type=agent_type, relevant_memories=mems)

    def get_quality_score(self, project_id: str) -> MemoryQualityScore:
        all_m = global_memory_repository.get_by_project(project_id, active_only=False)
        active = [m for m in all_m if m.status == MemoryStatus.ACTIVE]
        super_cnt = sum(1 for m in all_m if m.status == MemoryStatus.SUPERSEDED)
        arch_cnt = sum(1 for m in all_m if m.status == MemoryStatus.ARCHIVED)
        crit_cnt = sum(1 for m in active if m.importance == MemoryImportance.CRITICAL)
        high_cnt = sum(1 for m in active if m.importance == MemoryImportance.HIGH)

        return MemoryQualityScore(
            total_memories=len(all_m),
            active_count=len(active),
            superseded_count=super_cnt,
            archived_count=arch_cnt,
            critical_count=crit_cnt,
            high_count=high_cnt,
            duplicate_rate=0.0,
            contradiction_rate=0.0
        )


global_engineering_memory_service = EngineeringMemoryService()
