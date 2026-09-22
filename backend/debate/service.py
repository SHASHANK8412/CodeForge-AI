"""
AIForge Day 16 — Centralized DebateService
==========================================
Manages active and historical debate sessions, Architecture Decision Records (ADRs),
and human approval actions.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.debate.models import DebateSession, ADRecord
from backend.debate.engine import global_debate_engine

_logger = logging.getLogger("aiforge.debate.service")


class DebateService:
    """
    Centralized service for multi-agent debate sessions and ADR history.
    """

    def __init__(self):
        # project_id -> list of DebateSessions
        self._project_sessions: Dict[str, List[DebateSession]] = {}

    def run_project_debate(
        self,
        project_id: str,
        requirement: str,
        generation_id: str = "aiforge-demo",
        force_debate: bool = True
    ) -> DebateSession:
        session = global_debate_engine.run_debate(project_id, requirement, generation_id, force_debate)

        if project_id not in self._project_sessions:
            self._project_sessions[project_id] = []
        self._project_sessions[project_id].append(session)

        return session

    def get_project_debates(self, project_id: str) -> List[DebateSession]:
        return self._project_sessions.get(project_id, [])

    def get_latest_session(self, project_id: str) -> Optional[DebateSession]:
        sessions = self.get_project_debates(project_id)
        if sessions:
            return sessions[-1]
        
        # Seed a default demo session if none exists
        demo = self.run_project_debate(
            project_id,
            "Build a highly scalable social media platform with authentication, user posts, cart, and payments.",
            "aiforge-demo",
            force_debate=True
        )
        return demo

    def get_all_adrs(self, project_id: str) -> List[ADRecord]:
        sessions = self.get_project_debates(project_id)
        adrs = []
        for s in sessions:
            if s.decision and s.decision.adr:
                adrs.append(s.decision.adr)
        return adrs

    def approve_decision(self, project_id: str, debate_id: str) -> bool:
        sessions = self.get_project_debates(project_id)
        session = next((s for s in sessions if s.debate_id == debate_id), None)
        if session and session.decision:
            session.status = "COMPLETED"
            if session.decision.adr:
                session.decision.adr.status = "ACCEPTED"
            _logger.info(f"[DebateService] Approved debate decision '{debate_id}' for project '{project_id}'")
            return True
        return False

    def reject_decision(self, project_id: str, debate_id: str) -> bool:
        sessions = self.get_project_debates(project_id)
        session = next((s for s in sessions if s.debate_id == debate_id), None)
        if session and session.decision:
            session.status = "REJECTED"
            if session.decision.adr:
                session.decision.adr.status = "REJECTED"
            _logger.info(f"[DebateService] Rejected debate decision '{debate_id}' for project '{project_id}'")
            return True
        return False


global_debate_service = DebateService()
