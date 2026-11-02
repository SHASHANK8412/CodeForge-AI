import logging
from typing import Dict, Any, Optional

from backend.services.context_builder import global_agent_context_builder, build_agent_context

logger = logging.getLogger("aiforge.memory.context_builder")


class ContextBuilder:
    """
    Adapter wrapper delegating to central backend.services.context_builder.
    """

    def build_augmented_context(self, prompt: str, agent_name: str, project_id: Optional[str] = None) -> str:
        return build_agent_context(
            project_id=project_id or "default_project",
            agent_name=agent_name,
            prompt=prompt
        )


global_context_builder = ContextBuilder()
