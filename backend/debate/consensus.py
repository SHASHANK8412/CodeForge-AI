import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.debate")

class ConsensusEngine:
    """
    Evaluates agent opinions, flags design conflicts (SQL vs NoSQL, REST vs GraphQL),
    and computes weighted decisions.
    """

    CONFLICT_PAIRS = [
        ("REST", "GraphQL"),
        ("SQL", "NoSQL"),
        ("Microservices", "Monolith"),
        ("JWT", "Session"),
        ("Tailwind", "Material UI"),
        ("Docker", "Native")
    ]

    def __init__(self) -> None:
        pass

    def detect_conflicts(self, proposals: Dict[str, str]) -> List[str]:
        """
        Highlights conflicting architectural choices between different agent proposals.
        """
        conflicts = []
        choices = list(proposals.values())
        
        for c1 in choices:
            for c2 in choices:
                if c1 == c2:
                    continue
                # Check conflict pair map
                for pair in self.CONFLICT_PAIRS:
                    if (c1 in pair) and (c2 in pair):
                        ordered_pair = sorted([c1, c2])
                        conflict_msg = f"Architecture Conflict: '{ordered_pair[0]}' vs '{ordered_pair[1]}' proposed."
                        if conflict_msg not in conflicts:
                            conflicts.append(conflict_msg)

        if conflicts:
            _logger.warning(f"SRE Consensus: conflicts discovered: {conflicts}")
        return conflicts

    def calculate_winning_solution(
        self,
        weighted_tallies: Dict[str, float],
        conflicts: List[str]
    ) -> Dict[str, Any]:
        """
        Selects the architecture choice with the highest tally weight.
        """
        if not weighted_tallies:
            return {"solution": "REST + SQL", "reason": "Default fallback config"}

        winning_choice = max(weighted_tallies, key=lambda k: weighted_tallies[k])
        
        reason = f"Selected '{winning_choice}' based on highest weighted tally score ({weighted_tallies[winning_choice]:.2f})."
        if conflicts:
            reason += f" Resolved design conflicts: {', '.join(conflicts)}."

        _logger.info(f"SRE Consensus decision made: {winning_choice}")
        return {
            "solution": winning_choice,
            "reason": reason
        }
