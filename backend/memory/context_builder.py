import logging
from typing import Dict, Any, Optional

from backend.rag.pipeline import global_rag_pipeline
from backend.memory.short_term import global_short_term_memory
from backend.memory.long_term import global_long_term_memory

logger = logging.getLogger("aiforge.memory.context_builder")


class ContextBuilder:
    """
    ContextBuilder retrieves and merges:
    1. Current User Request
    2. RAG Uploaded Documentation Context
    3. Short-Term Workflow State Memory
    4. Long-Term Persistent Project Memory
    into a unified context string for AI agent prompt injection.
    """

    def build_augmented_context(self, prompt: str, agent_name: str, project_id: Optional[str] = None) -> str:
        sections = []

        # 1. RAG Uploaded Documentation
        rag_context = global_rag_pipeline.get_context_string_for_agent(agent_name, prompt)
        if rag_context:
            sections.append(f"### RAG Uploaded Documentation Context\n{rag_context}")

        # 2. Long-Term Persistent Memory (Previous Project Record if resuming)
        if project_id:
            past_project = global_long_term_memory.get_project(project_id)
            if past_project:
                sections.append(
                    f"### Resuming Existing Project Memory ({past_project.get('name')})\n"
                    f"- Version: {past_project.get('version', 'v1')}\n"
                    f"- Tech Stack: {past_project.get('tech_stack')}\n"
                    f"- Database Schema:\n{past_project.get('database_schema')[:300]}\n"
                )

        # 3. Short-Term Workflow State Memory
        st_data = global_short_term_memory.get_all()
        if st_data:
            sections.append(f"### Active Workflow Short-Term Context\n{st_data}")

        sections.append(f"### Current Agent Request ({agent_name.upper()})\n{prompt}")
        return "\n\n".join(sections)


# Global ContextBuilder instance
global_context_builder = ContextBuilder()
