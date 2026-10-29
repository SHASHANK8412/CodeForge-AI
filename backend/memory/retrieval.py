"""
AIForge Day 22 — Contextual Memory Retrieval Engine
===================================================
Ranks memories using semantic relevance, project context, importance, recency, confidence,
and agent-role specialization (Architect, Backend, Frontend, Security, Performance, DevOps, Incident).
Maintains backwards compatibility with Day 12 MemoryRetriever.
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional

from backend.memory.models import (
    EngineeringMemory, MemoryType, MemoryImportance, MemoryStatus,
    ProjectMemory, DecisionRecord, ImportanceLevel
)
from backend.memory.repository import global_memory_repository
from backend.memory.short_term import global_short_term_memory
from backend.memory.long_term import global_long_term_memory
from backend.rag.pipeline import global_rag_pipeline

_logger = logging.getLogger("aiforge.memory.retrieval")

AGENT_TYPE_INTERESTS: Dict[str, List[MemoryType]] = {
    "Architect": [MemoryType.ARCHITECTURE_DECISION, MemoryType.PROJECT_CONSTRAINT, MemoryType.TECHNOLOGY_DECISION],
    "Backend": [MemoryType.CODING_PATTERN, MemoryType.ARCHITECTURE_DECISION, MemoryType.PERFORMANCE_LESSON],
    "Frontend": [MemoryType.USER_PREFERENCE, MemoryType.CODING_PATTERN, MemoryType.KNOWN_LIMITATION],
    "Security": [MemoryType.SECURITY_LESSON, MemoryType.INCIDENT_LESSON, MemoryType.PROJECT_CONSTRAINT],
    "Performance": [MemoryType.PERFORMANCE_LESSON, MemoryType.SUCCESSFUL_APPROACH, MemoryType.FAILED_APPROACH],
    "DevOps": [MemoryType.DEPLOYMENT_LESSON, MemoryType.PROJECT_CONSTRAINT, MemoryType.INCIDENT_LESSON],
    "Incident": [MemoryType.INCIDENT_LESSON, MemoryType.REPAIR_HISTORY, MemoryType.FAILED_APPROACH],
}


class MemoryRetrievalEngine:
    """
    Ranks and retrieves contextual memories for Day 22 Engineering Memory.
    """

    def retrieve_contextual_memories(
        self,
        project_id: str,
        task_query: str,
        agent_type: str = "Backend",
        top_k: int = 5
    ) -> List[EngineeringMemory]:
        _logger.info(f"[MemoryRetrieval] Querying memories for '{agent_type}' agent on task '{task_query[:30]}...'")

        all_memories = global_memory_repository.get_by_project(project_id, active_only=True)
        if not all_memories:
            return []

        q_lower = task_query.lower()
        preferred_types = AGENT_TYPE_INTERESTS.get(agent_type, [])

        def score_memory(mem: EngineeringMemory) -> float:
            score = 0.0
            if mem.type in preferred_types:
                score += 30.0
            if any(term in q_lower for term in mem.title.lower().split() + mem.content.lower().split()):
                score += 40.0
            if mem.importance == MemoryImportance.CRITICAL:
                score += 25.0
            elif mem.importance == MemoryImportance.HIGH:
                score += 15.0
            score += min(mem.usage_count * 2.0, 10.0)
            return score

        ranked = sorted(all_memories, key=score_memory, reverse=True)
        return ranked[:top_k]


global_memory_retrieval_engine = MemoryRetrievalEngine()


# Legacy Day 12 Compatibility Layer
MAX_MEMORY_ITEMS = 15
MAX_RAG_RESULTS = 5
MAX_CONTEXT_TOKENS = 3000


def _approx_token_count(text: str) -> int:
    return len(text) // 4


class MemoryRetriever:
    """
    Multi-tier memory retrieval strategy with strict context size control.
    """

    def retrieve_relevant_memory(
        self,
        project_id: str,
        query: str,
        agent_name: str,
        limit: int = MAX_MEMORY_ITEMS,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        generation_id: Optional[str] = None,
        long_term_store: Optional[Any] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        lt = long_term_store or global_long_term_memory

        st_data = global_short_term_memory.get_all()
        decisions: List[DecisionRecord] = lt.get_decisions(project_id)
        long_mems: List[ProjectMemory] = lt.search_memories(project_id=project_id, query=query, top_k=limit)

        rag_context = ""
        try:
            rag_context = global_rag_pipeline.get_context_string_for_agent(agent_name, query)
        except Exception as e:
            _logger.warning(f"RAG retrieval warning for agent '{agent_name}': {e}")

        context_parts: List[str] = []
        token_count = 0

        if decisions:
            dec_lines = [f"- {d.decision} (Reason: {d.reason}) [{d.agent}]" for d in decisions[:5]]
            dec_text = "### Key Architectural Decisions\n" + "\n".join(dec_lines)
            context_parts.append(dec_text)
            token_count += _approx_token_count(dec_text)

        if long_mems and token_count < max_tokens:
            mem_lines = []
            for m in long_mems[:limit]:
                val_str = json.dumps(m.value) if isinstance(m.value, (dict, list)) else str(m.value)
                if len(val_str) > 250:
                    val_str = val_str[:250] + "..."
                mem_lines.append(f"- [{m.memory_type}] {m.key}: {val_str} (Source: {m.source_agent})")

            mem_text = "### Relevant Project Memories\n" + "\n".join(mem_lines)
            if token_count + _approx_token_count(mem_text) <= max_tokens:
                context_parts.append(mem_text)
                token_count += _approx_token_count(mem_text)

        if rag_context and token_count < max_tokens:
            rag_text = f"### Relevant Documentation & Knowledge\n{rag_context[:1000]}"
            if token_count + _approx_token_count(rag_text) <= max_tokens:
                context_parts.append(rag_text)
                token_count += _approx_token_count(rag_text)

        context_string = "\n\n".join(context_parts)
        retrieval_ms = (time.perf_counter() - start_time) * 1000

        return {
            "project_id": project_id,
            "generation_id": generation_id,
            "agent_name": agent_name,
            "decisions": [d.model_dump() for d in decisions],
            "memories": [m.model_dump() for m in long_mems],
            "rag_context": rag_context,
            "context_string": context_string,
            "token_count": token_count,
            "retrieval_ms": round(retrieval_ms, 2)
        }


global_memory_retriever = MemoryRetriever()


def retrieve_relevant_memory(
    project_id: str,
    query: str,
    agent_name: str,
    limit: int = MAX_MEMORY_ITEMS,
    max_tokens: int = MAX_CONTEXT_TOKENS,
    generation_id: Optional[str] = None,
    long_term_store: Optional[Any] = None
) -> Dict[str, Any]:
    return global_memory_retriever.retrieve_relevant_memory(
        project_id=project_id,
        query=query,
        agent_name=agent_name,
        limit=limit,
        max_tokens=max_tokens,
        generation_id=generation_id,
        long_term_store=long_term_store
    )
