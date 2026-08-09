import json
import time
import logging
from typing import Dict, Any, List, Optional

from backend.memory.short_term import global_short_term_memory
from backend.memory.long_term import global_long_term_memory
from backend.memory.models import ProjectMemory, DecisionRecord, ImportanceLevel
from backend.rag.pipeline import global_rag_pipeline

logger = logging.getLogger("aiforge.memory.retrieval")

MAX_MEMORY_ITEMS = 15
MAX_RAG_RESULTS = 5
MAX_CONTEXT_TOKENS = 3000


def _approx_token_count(text: str) -> int:
    return len(text) // 4


class MemoryRetriever:
    """
    Implements multi-tier memory retrieval strategy with strict context size control and importance ranking.
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
        """
        Retrieves relevant context for an agent in prioritized order:
        1. Current generation state (short-term)
        2. Architectural decisions
        3. Relevant previous agent outputs
        4. Relevant long-term project memories (ranked by importance & relevance)
        5. RAG knowledge context
        """
        start_time = time.perf_counter()
        lt = long_term_store or global_long_term_memory

        # 1. Short-Term Generation Memory
        st_data = global_short_term_memory.get_all()

        # 2. Project Architectural Decisions
        decisions: List[DecisionRecord] = lt.get_decisions(project_id)

        # 3. Previous Agent Outputs from Long-Term & Short-Term
        agent_outputs = st_data.get("agent_outputs", {})

        # 4. Long-Term Project Memories (ranked)
        long_mems: List[ProjectMemory] = lt.search_memories(
            project_id=project_id,
            query=query,
            top_k=limit
        )

        # 5. RAG Retrieval Context
        rag_context = ""
        try:
            rag_context = global_rag_pipeline.get_context_string_for_agent(agent_name, query)
        except Exception as e:
            logger.warning(f"RAG retrieval warning for agent '{agent_name}': {e}")

        # Assemble and format context string while honoring max_tokens budget
        context_parts: List[str] = []
        token_count = 0

        # Include Decisions (Priority High)
        if decisions:
            dec_lines = [f"- {d.decision} (Reason: {d.reason}) [{d.agent}]" for d in decisions[:5]]
            dec_text = "### Key Architectural Decisions\n" + "\n".join(dec_lines)
            context_parts.append(dec_text)
            token_count += _approx_token_count(dec_text)

        # Include Relevant Long-Term Memories
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

        # Include RAG Context
        if rag_context and token_count < max_tokens:
            rag_text = f"### Relevant Documentation & Knowledge\n{rag_context[:1000]}"
            if token_count + _approx_token_count(rag_text) <= max_tokens:
                context_parts.append(rag_text)
                token_count += _approx_token_count(rag_text)

        context_string = "\n\n".join(context_parts)
        retrieval_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"[MEMORY] project={project_id} agent={agent_name} "
            f"retrieved={len(long_mems) + len(decisions)} context_size={len(context_string)} chars "
            f"tokens=~{token_count} time={retrieval_ms:.2f}ms"
        )

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


# Global MemoryRetriever instance
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
