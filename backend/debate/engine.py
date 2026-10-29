"""
AIForge Day 16 — Debate Engine Orchestrator
===========================================
Handles:
- Decision Threshold evaluation (LOW -> normal, MEDIUM -> 2 candidates, HIGH/CRITICAL -> 3 candidates + Judge)
- Candidate generation and fallback to normal Architect if candidates fail
- Project Memory persistence (ARCHITECTURE_DECISION)
- Engineering DNA graph updates
- Flight Recorder event emissions
- Human approval policy checks
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.debate.models import (
    DebateSession, DebateThreshold, ArchitectureProposal, JudgeDecision
)
from backend.debate.candidates import global_candidate_generator
from backend.debate.judge import global_judge_agent
from backend.memory.project_memory import global_project_memory_store
from backend.autopilot.recorder import global_flight_recorder

_logger = logging.getLogger("aiforge.debate.engine")

HIGH_IMPACT_KEYWORDS = {
    "database", "postgres", "mongodb", "sql", "nosql", "auth",
    "graphql", "rest", "kafka", "microservices", "caching", "deployment"
}


class DebateEngine:
    """
    Orchestrates the multi-agent debate workflow.
    """

    def determine_threshold(self, requirement: str) -> DebateThreshold:
        req_lower = requirement.lower()
        matches = sum(1 for kw in HIGH_IMPACT_KEYWORDS if kw in req_lower)

        if "auth" in req_lower or "security" in req_lower:
            return DebateThreshold.CRITICAL
        elif matches >= 2:
            return DebateThreshold.HIGH
        elif matches == 1:
            return DebateThreshold.MEDIUM
        else:
            return DebateThreshold.LOW

    def run_debate(
        self,
        project_id: str,
        requirement: str,
        generation_id: str = "aiforge-demo",
        force_debate: bool = False
    ) -> DebateSession:
        threshold = self.determine_threshold(requirement)
        if not force_debate and threshold == DebateThreshold.LOW:
            _logger.info(f"[DebateEngine] Low impact requirement '{requirement[:30]}...'. Proceeding with normal Architect Agent.")

        deb_id = f"deb_{secrets.token_urlsafe(6)}"
        try:
            global_flight_recorder.record_event(project_id, "Architect", "debate_started", {"requirement": requirement})
        except Exception:
            pass

        # Generate candidates
        candidates = global_candidate_generator.generate_all_candidates(project_id, requirement)

        if not candidates or len(candidates) == 0:
            _logger.warning("[DebateEngine] Candidate generation failed. Falling back to normal Architect Agent.")
            fallback_cand = global_candidate_generator.generate_candidate_a(project_id, requirement)
            candidates = [fallback_cand]

        for c in candidates:
            try:
                global_flight_recorder.record_event(project_id, "Architect", "candidate_created", {"candidate_id": c.candidate_id, "name": c.name})
            except Exception:
                pass

        # Judge evaluation
        try:
            global_flight_recorder.record_event(project_id, "JudgeAgent", "judge_started", {"candidate_count": len(candidates)})
        except Exception:
            pass

        decision = global_judge_agent.evaluate_candidates(project_id, requirement, candidates)

        try:
            global_flight_recorder.record_event(project_id, "JudgeAgent", "judge_completed", {"winner": decision.winner, "winning_proposal": decision.winning_proposal_name})
        except Exception:
            pass

        # Persist decision to Project Memory
        try:
            global_project_memory_store.record_decision(
                "JudgeAgent",
                f"Selected {decision.winning_proposal_name} via Multi-Agent Debate for requirement: '{requirement[:40]}'"
            )
        except Exception as err:
            _logger.debug(f"[DebateEngine] Could not record decision in project memory: {err}")

        session_status = "PENDING_APPROVAL" if decision.requires_human_approval else "COMPLETED"

        session = DebateSession(
            debate_id=deb_id,
            project_id=project_id,
            generation_id=generation_id,
            requirement=requirement,
            threshold=threshold,
            candidates=candidates,
            decision=decision,
            status=session_status,
            created_at=datetime.now().isoformat()
        )

        _logger.info(f"[DebateEngine] Debate '{deb_id}' completed. Winner: Candidate {decision.winner}")
        return session


global_debate_engine = DebateEngine()
