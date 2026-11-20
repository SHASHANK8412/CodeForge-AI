from typing import Dict, Any, Tuple
from backend.monitoring.knowledge_base import IncidentKnowledgeBase

class RecoveryEngine:
    """
    Chooses recovery strategies (restarts, scale-ups, cache clears, configuration refreshes) from SRE policies,
    recommendations and the knowledge base. No executor is connected: execute_recovery raises
    NotImplementedError, and the SRE monitor reports a recommendation instead of a recovery.
    """

    def __init__(self, knowledge_base: IncidentKnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    def recommend(self, signature: str, recommendation: Dict[str, Any]) -> str:
        """The strategy a person (or a future executor) should apply; nothing is run."""
        return self.knowledge_base.get_best_strategy(signature) or recommendation.get("recommended_action") or "Investigate"

    def execute_recovery(
        self,
        signature: str,
        recommendation: Dict[str, Any],
        attempt_number: int = 1
    ) -> Tuple[str, float]:
        """Not implemented: no executor (Docker SDK, Kubernetes API, Redis client) is connected, so no
        recovery action can be run. Raises instead of returning a strategy and duration as if it had run."""
        raise NotImplementedError(
            "recovery execution is not implemented: AIForge has no recovery executor connected; "
            f"use recommend() for the suggested strategy (incident '{signature}' was not acted on)"
        )
