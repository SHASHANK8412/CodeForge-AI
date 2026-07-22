"""
Day 43 - Negotiation Agent
==========================
Resolves detected inter-agent conflicts automatically using confidence scoring and resolution strategies.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from backend.collaboration.conflict_detector import Conflict


@dataclass
class ResolutionDecision:
    conflict_id: str
    category: str
    strategy: str  # SchemaAuthority, APIFirst, HighestConfidence, Consensus
    winner_agent: str
    resolved_value: Any
    confidence_score: float
    reasoning: str


class NegotiationAgent:
    """Mediates inter-agent design conflicts and decides winning resolutions."""

    STRATEGIES = {
        "schema_mismatch": "SchemaAuthority",
        "api_mismatch": "APIFirst",
        "doc_mismatch": "APIFirst",
        "test_mismatch": "APIFirst"
    }

    def resolve(self, conflicts: List[Conflict], agent_outputs: Dict[str, Any]) -> List[ResolutionDecision]:
        decisions: List[ResolutionDecision] = []

        for conflict in conflicts:
            strategy = self.STRATEGIES.get(conflict.category, "Consensus")

            if strategy == "SchemaAuthority":
                winner = "Database"
                resolved_val = conflict.lhs_value  # Database snake_case naming wins
                confidence = 0.95
                reason = "Database schema has primary authority over field naming conventions."

            elif strategy == "APIFirst":
                winner = "Backend"
                resolved_val = conflict.rhs_value  # Backend endpoint path wins
                confidence = 0.92
                reason = "Backend API contract defines authoritative REST endpoints."

            else:
                winner = "Backend"
                resolved_val = conflict.rhs_value
                confidence = 0.88
                reason = "Consensus strategy resolved conflict to match primary backend implementation."

            decisions.append(ResolutionDecision(
                conflict_id=conflict.id,
                category=conflict.category,
                strategy=strategy,
                winner_agent=winner,
                resolved_value=resolved_val,
                confidence_score=confidence,
                reasoning=reason
            ))

        return decisions
