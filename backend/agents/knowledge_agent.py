"""
AIForge Day 96 & 97 Knowledge Agent
===================================
Manages reusable components, templates, and architectural best practices for Day 96 & 97.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.learning.knowledge_base import global_knowledge_base

_logger = logging.getLogger("aiforge.agents.knowledge")


class KnowledgeAgent:
    """
    Knowledge Agent for managing reusable components & templates.
    """

    def get_reusable_templates(self) -> Dict[str, Any]:
        return global_knowledge_base.get_all_knowledge()

    def get_best_practices_for_topic(self, topic: str) -> Optional[Dict[str, Any]]:
        return global_knowledge_base.get_component(topic)


global_knowledge_agent = KnowledgeAgent()
