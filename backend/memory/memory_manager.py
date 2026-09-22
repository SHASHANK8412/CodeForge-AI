from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.memory.models import ProjectMemory, DecisionRecord, MemoryType, ImportanceLevel
from backend.memory.short_term import global_short_term_memory
from backend.memory.long_term import global_long_term_memory
from backend.memory.retrieval import global_memory_retriever

logger = logging.getLogger("aiforge.memory.memory_manager")


class MemoryManager:
    """
    Unified Memory Manager providing access to:
    - Short-term workflow state (current generation execution session)
    - Long-term persistent project memories and architectural decisions across sessions
    - Context-aware memory retrieval and ranking
    """

    def __init__(self):
        self.short_term = global_short_term_memory
        self.long_term = global_long_term_memory
        self.retriever = global_memory_retriever

    # --- Core Required API Methods ---

    def save(
        self,
        project_id: str,
        memory_type: MemoryType | str,
        key: str,
        value: Any,
        source_agent: str,
        importance: ImportanceLevel | str = ImportanceLevel.MEDIUM,
        generation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ProjectMemory:
        """Stores a memory record in long-term memory and short-term state."""
        try:
            mem = self.long_term.save_memory(
                project_id=project_id,
                memory_type=memory_type,
                key=key,
                value=value,
                source_agent=source_agent,
                importance=importance,
                generation_id=generation_id,
                user_id=user_id
            )
            self.short_term.set(f"mem_{key}", value)
            return mem
        except Exception as e:
            logger.error(f"MemoryManager.save failed safely: {e}")
            m_type = memory_type if isinstance(memory_type, MemoryType) else MemoryType(str(memory_type).split(".")[-1])
            return ProjectMemory(
                id="mem_err_fallback",
                project_id=project_id,
                memory_type=m_type,
                key=key,
                value=value,
                source_agent=source_agent,
                importance=ImportanceLevel.LOW,
                created_at="",
                updated_at=""
            )

    def save_decision(
        self,
        project_id: str,
        decision: str,
        reason: str,
        agent: str,
        importance: ImportanceLevel | str = ImportanceLevel.HIGH,
        generation_id: Optional[str] = None
    ) -> DecisionRecord:
        """Stores an architectural decision record."""
        try:
            rec = self.long_term.save_decision(
                project_id=project_id,
                decision=decision,
                reason=reason,
                agent=agent,
                importance=importance,
                generation_id=generation_id
            )
            self.short_term.add_decision(rec.model_dump())
            return rec
        except Exception as e:
            logger.error(f"MemoryManager.save_decision failed safely: {e}")
            return DecisionRecord(
                id="dec_err_fallback",
                project_id=project_id,
                decision=decision,
                reason=reason,
                agent=agent,
                timestamp="",
                importance=ImportanceLevel.HIGH
            )

    def retrieve(
        self,
        project_id: str,
        query: str = "",
        agent_name: str = "",
        limit: int = 10,
        max_tokens: int = 2000,
        generation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieves prioritized and ranked context string and memory objects."""
        return self.retriever.retrieve_relevant_memory(
            project_id=project_id,
            query=query,
            agent_name=agent_name,
            limit=limit,
            max_tokens=max_tokens,
            generation_id=generation_id,
            long_term_store=self.long_term
        )

    def update(self, project_id: str, memory_id: str, updates: Dict[str, Any]) -> Optional[ProjectMemory]:
        """Updates an existing memory record."""
        return self.long_term.update_memory(project_id, memory_id, updates)

    def delete(self, project_id: str, memory_id: str) -> bool:
        """Deletes a memory record."""
        return self.long_term.delete_memory(project_id, memory_id)

    def search(self, project_id: str, query: str, top_k: int = 5) -> List[ProjectMemory]:
        """Searches long-term project memories."""
        return self.long_term.search_memories(project_id, query, top_k=top_k)

    def summarize(self, project_id: str, max_items: int = 30) -> int:
        """Prunes/summarizes older LOW/MEDIUM memories if total items exceed limit."""
        return self.long_term.summarize_memories(project_id, max_items=max_items)

    def get_decisions(self, project_id: str) -> List[DecisionRecord]:
        """Returns all architectural decisions for a project."""
        return self.long_term.get_decisions(project_id)

    def explain_decision(self, project_id: str, query_or_topic: str) -> Dict[str, Any]:
        """
        Returns a concise explanation for a decision made by an agent.
        E.g., 'Why did AIForge choose PostgreSQL?'
        """
        decisions = self.get_decisions(project_id)
        if not decisions:
            return {
                "project_id": project_id,
                "topic": query_or_topic,
                "explanation": f"No stored decision records found for project '{project_id}'."
            }

        q_lower = query_or_topic.lower()
        matched_decision = None

        for d in decisions:
            if any(term in d.decision.lower() or term in d.reason.lower() for term in q_lower.split()):
                matched_decision = d
                break

        if not matched_decision and decisions:
            matched_decision = decisions[0]

        return {
            "project_id": project_id,
            "topic": query_or_topic,
            "decision": matched_decision.decision,
            "reason": matched_decision.reason,
            "agent": matched_decision.agent,
            "timestamp": matched_decision.timestamp,
            "explanation": f"The {matched_decision.agent} selected {matched_decision.decision} because {matched_decision.reason}"
        }

    # --- Short-Term Output Operations (Compatibility) ---

    def save_agent_output(self, session_id: str, agent_name: str, output: Any) -> None:
        self.short_term.set_agent_output(agent_name, output)

    def get_agent_output(self, session_id: str, agent_name: str) -> Any:
        return self.short_term.get_agent_output(agent_name)


# Global Singleton
global_memory_manager = MemoryManager()
memory_manager = global_memory_manager
