"""
AIForge Conflict Resolution Engine
====================================
Resolves inter-agent conflicts and output discrepancies using predefined role priority hierarchy:
1. Project Manager
2. Reviewer Agent
3. Testing Agent
4. Architect Agent
5. Development Agents (Frontend, Backend, Database, DevOps)
"""

import time
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.communication.conflict")


class ConflictResolver:
    """
    Priority-based conflict resolution engine.
    """

    ROLE_PRIORITY: Dict[str, int] = {
        "Project Manager": 1,
        "Project Manager Agent": 1,
        "Reviewer Agent": 2,
        "Reviewer": 2,
        "Testing Agent": 3,
        "QA Agent": 3,
        "Architect Agent": 4,
        "Architect": 4,
        "Backend Agent": 5,
        "Frontend Agent": 5,
        "Database Agent": 5,
        "DevOps Agent": 5,
        "Security Agent": 5
    }

    def __init__(self) -> None:
        self.conflicts_history: List[Dict[str, Any]] = [
            {
                "conflict_id": "conflict_001",
                "topic": "Component Naming Standard",
                "agent_a": "Reviewer Agent",
                "proposal_a": "Rename UserCard.jsx to UserProfileCard.jsx for clarity",
                "agent_b": "Frontend Agent",
                "proposal_b": "Keep UserCard.jsx to match legacy routing",
                "winning_agent": "Reviewer Agent",
                "decision": "Applied proposal from Reviewer Agent (Higher Priority: 2 vs 5)",
                "resolved_at": time.time() - 3600
            }
        ]

    def resolve_conflict(
        self,
        topic: str,
        agent_a: str,
        proposal_a: str,
        agent_b: str,
        proposal_b: str
    ) -> Dict[str, Any]:
        prio_a = self.ROLE_PRIORITY.get(agent_a, 10)
        prio_b = self.ROLE_PRIORITY.get(agent_b, 10)

        if prio_a < prio_b:
            winner = agent_a
            winning_proposal = proposal_a
            winning_prio = prio_a
            losing_prio = prio_b
        elif prio_b < prio_a:
            winner = agent_b
            winning_proposal = proposal_b
            winning_prio = prio_b
            losing_prio = prio_a
        else:
            # Tie breaker goes to Project Manager
            winner = "Project Manager Agent"
            winning_proposal = f"Project Manager arbitration: Default to '{proposal_a}'"
            winning_prio = 1
            losing_prio = prio_a

        decision_msg = f"Resolved in favor of '{winner}' (Priority {winning_prio} vs {losing_prio}). Proposal: {winning_proposal}"
        
        conflict_entry = {
            "conflict_id": f"conflict_{int(time.time() * 1000)}",
            "topic": topic,
            "agent_a": agent_a,
            "proposal_a": proposal_a,
            "agent_b": agent_b,
            "proposal_b": proposal_b,
            "winning_agent": winner,
            "decision": decision_msg,
            "resolved_at": time.time()
        }
        self.conflicts_history.append(conflict_entry)
        _logger.info(f"ConflictResolver: {decision_msg}")
        return conflict_entry

    def get_conflict_history(self) -> List[Dict[str, Any]]:
        return list(self.conflicts_history)


global_conflict_resolver = ConflictResolver()
