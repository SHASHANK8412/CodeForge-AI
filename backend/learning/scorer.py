import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.learning.scorer")


class KnowledgeScorer:
    """
    KnowledgeScorer computes confidence scores (0-10) for stored knowledge items
    based on reuse frequency, user feedback, and test success rates.
    """

    def calculate_confidence(self, reuse_count: int, success_rate: float = 0.98) -> float:
        base_score = 8.5
        boost = min(reuse_count * 0.05, 1.0)
        final_score = round(min(base_score + boost + (success_rate * 0.5), 10.0), 1)
        return final_score


# Global KnowledgeScorer Instance
global_knowledge_scorer = KnowledgeScorer()
