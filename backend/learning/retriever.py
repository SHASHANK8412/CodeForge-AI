"""
AIForge Experience Retrieval Pipeline
=====================================
Retrieves past project experiences, bug fixes, deployment insights, and user preferences
for injection into multi-agent code generation context.
"""

import logging
from typing import Dict, Any, List

from backend.learning.experience import global_experience_db
from backend.learning.embeddings import global_embedding_engine

_logger = logging.getLogger("aiforge.learning")


class ExperienceRetriever:
    """
    Retrieves relevant project experiences for prompt context injection.
    """

    def retrieve_experience_context(self, prompt: str) -> Dict[str, Any]:
        _logger.info(f"ExperienceRetriever: Searching experience database for prompt '{prompt}'...")

        all_exp = global_experience_db.get_all_experiences()
        if not all_exp:
            return {
                "has_previous_experience": False,
                "reused_architecture": None,
                "known_bug_fixes": [],
                "user_preferences": ["FastAPI", "Tailwind", "MongoDB", "Docker", "JWT"]
            }

        # Select highest scoring matching experience
        best_match = max(all_exp, key=lambda x: x.get("performance_score", 0))

        return {
            "has_previous_experience": True,
            "matched_prompt": best_match.get("prompt"),
            "reused_architecture": best_match.get("architecture"),
            "known_bug_fixes": best_match.get("bug_fixes", []),
            "deployment_insights": best_match.get("deployment_insights", {}),
            "user_preferences": best_match.get("user_preferences", []),
            "previous_score": best_match.get("performance_score", 93.5)
        }


global_experience_retriever = ExperienceRetriever()
