"""
AIForge V2 — Engineering Autopilot Decision Manager
===================================================
Captures, structures, and formats explainable Decision Cards from agent outputs,
Day 12 Memory, and Day 13 RAG citations.
"""

import time
import secrets
import logging
from typing import Dict, Any, List, Optional

from backend.autopilot.models import DecisionCardData, DecisionType

_logger = logging.getLogger("aiforge.autopilot.decisions")


class DecisionManager:
    """
    Manages structured AI Decision Cards for the Engineering Autopilot.
    """

    def __init__(self):
        self._decisions: Dict[str, List[DecisionCardData]] = {}  # gen_id -> [DecisionCardData]

    def record_decision(
        self,
        generation_id: str,
        type: DecisionType,
        title: str,
        summary: str,
        reason: str,
        evidence: Optional[List[str]] = None,
        impact: str = "",
        confidence: Optional[float] = None,
        sources: Optional[List[str]] = None
    ) -> DecisionCardData:
        d_id = f"dec_{secrets.token_urlsafe(8)}"
        card = DecisionCardData(
            id=d_id,
            generation_id=generation_id,
            type=type,
            title=title,
            summary=summary,
            reason=reason,
            evidence=evidence or [],
            impact=impact,
            confidence=confidence,
            timestamp=time.strftime("%H:%M:%S"),
            sources=sources or []
        )

        gen_list = self._decisions.setdefault(generation_id, [])
        gen_list.append(card)
        _logger.info(f"DecisionManager: Logged decision '{title}' for generation '{generation_id}' (Confidence: {confidence})")
        return card

    def get_decisions(self, generation_id: str) -> List[DecisionCardData]:
        cards = self._decisions.get(generation_id, [])
        if not cards:
            # Seed default demo decisions for aiforge-demo
            if generation_id in ("aiforge-demo", "aiforge_demo") or generation_id.startswith("aiforge-demo"):
                return self._seed_demo_decisions(generation_id)
        return cards

    def _seed_demo_decisions(self, generation_id: str) -> List[DecisionCardData]:
        demo_cards = [
            DecisionCardData(
                id="dec_demo_1",
                generation_id=generation_id,
                type=DecisionType.PLANNING,
                title="12 Requirements Identified",
                summary="Analyzed prompt and extracted core functional modules.",
                reason="User prompt specifies task platform with auth, projects, tasks, deadlines, search, and dashboard.",
                evidence=["User authentication", "PostgreSQL database", "React SPA UI"],
                impact="Requirements: +10",
                confidence=0.96,
                timestamp="14:21",
                sources=["[S1] User Requirements Spec"]
            ),
            DecisionCardData(
                id="dec_demo_2",
                generation_id=generation_id,
                type=DecisionType.ARCHITECTURE,
                title="PostgreSQL Selected",
                summary="Selected PostgreSQL as core relational database.",
                reason="Application contains strongly relational orders, payments, tasks, and user entities requiring ACID transactions.",
                evidence=["Task entities with FK to Users", "Project ownership constraints", "Strict relational integrity"],
                impact="Architecture: +8",
                confidence=0.92,
                timestamp="14:23",
                sources=["[S1] architecture.json", "[S2] database_schema.sql"]
            ),
            DecisionCardData(
                id="dec_demo_3",
                generation_id=generation_id,
                type=DecisionType.SECURITY,
                title="JWT Authentication Middleware",
                summary="Implemented stateless JWT authentication.",
                reason="Protects protected routes (/dashboard, /create, /projects) with HTTP Bearer token validation.",
                evidence=["Bcrypt password hashing", "Secret key sanitization"],
                impact="Security: +15",
                confidence=0.89,
                timestamp="14:27",
                sources=["[S1] auth.py", "[S2] security_scan.json"]
            ),
            DecisionCardData(
                id="dec_demo_4",
                generation_id=generation_id,
                type=DecisionType.REPAIR,
                title="Authentication Input Validation Fix",
                summary="Applied targeted patch to auth middleware.",
                reason="Missing schema validation caused 401 Unauthorized errors on valid login requests.",
                evidence=["Auth middleware modified", "Test pass count increased from 47 to 52"],
                impact="Quality: 86 → 96",
                confidence=0.94,
                timestamp="14:28",
                sources=["[S1] Repair Agent Audit Log #1"]
            )
        ]
        self._decisions[generation_id] = demo_cards
        return demo_cards


global_decision_manager = DecisionManager()
