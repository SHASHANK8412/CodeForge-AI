import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.debate")

class DebateVoting:
    """
    Handles weighted voting calculations based on agent specialization roles and confidence levels.
    """

    ROLE_WEIGHTS = {
        "architect": 5.0,
        "reviewer": 5.0,
        "security": 5.0,
        "backend": 4.0,
        "frontend": 4.0,
        "database": 4.0,
        "testing": 4.0,
        "planner": 3.0,
        "documentation": 2.0
    }

    def __init__(self) -> None:
        pass

    def calculate_weighted_votes(
        self,
        votes: Dict[str, str],
        confidence_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Tallies weighted score aggregates for each architectural option.
        """
        tally: Dict[str, float] = {}

        for agent, choice in votes.items():
            agent_lower = agent.lower().strip()
            # Determine weight baseline
            weight = self.ROLE_WEIGHTS.get(agent_lower, 3.0)
            
            # Incorporate confidence multiplier
            confidence = confidence_scores.get(agent_lower, 90.0)
            weighted_points = weight * (confidence / 100.0)

            tally[choice] = tally.get(choice, 0.0) + weighted_points

        _logger.info(f"Weighted voting results calculated: {tally}")
        return tally
