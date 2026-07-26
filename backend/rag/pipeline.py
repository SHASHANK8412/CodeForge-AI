import logging
from typing import Dict, Any, List

from backend.rag.knowledge_base import global_knowledge_base, KnowledgeBase

logger = logging.getLogger("aiforge.rag.pipeline")


class RAGPipeline:
    """
    RAGPipeline connects the semantic retriever and KnowledgeBase to agent prompts,
    enriching prompt instructions with relevant documentation, coding standards, and guidelines.
    """

    def __init__(self, knowledge_base: KnowledgeBase = None):
        self.kb = knowledge_base or global_knowledge_base

    def query_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Queries knowledge base documents directly."""
        return self.kb.search(query, top_k=top_k)

    def build_augmented_prompt(self, user_prompt: str, agent_name: str, memory_context: str = "") -> str:
        """
        Retrieves top relevant documentation chunks for user_prompt + agent_name
        and constructs a RAG-augmented prompt string.
        """
        search_query = f"{user_prompt} {agent_name} best practices guidelines"
        rag_context = self.kb.get_context_for_prompt(search_query, top_k=3)

        sections = []

        if memory_context:
            sections.append(f"### Shared Memory Context\n{memory_context}")

        if rag_context:
            sections.append(f"### Retrieved Technical Knowledge & Guidelines\n{rag_context}")

        sections.append(f"### Current Task Instructions ({agent_name.upper()})\n{user_prompt}")

        return "\n\n".join(sections)

    def get_stats(self) -> Dict[str, Any]:
        """Returns knowledge base stats."""
        return self.kb.get_stats()


# Global RAGPipeline Instance
global_rag_pipeline = RAGPipeline()
