"""
AIForge Change Impact Analyzer Module
=====================================
Analyzes incremental user change requests ("Add Google OAuth", "Add Stripe payments"),
computes requirement deltas, identifies affected files/agents, and prevents full regeneration.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.requirements.models import ProjectSpecification, Requirement, ChangeImpact

_logger = logging.getLogger("aiforge.requirements.impact_analyzer")


class ChangeImpactAnalyzer:
    """
    Performs impact analysis for requirement modifications and feature additions.
    """

    def analyze_change(
        self,
        change_request: str,
        current_spec: ProjectSpecification,
        existing_files: Dict[str, str]
    ) -> ChangeImpact:
        _logger.info(f"ChangeImpactAnalyzer: Analyzing change request '{change_request}'...")
        req_lower = change_request.lower()

        new_reqs = []
        affected_files = []
        affected_agents = []
        affected_tests = []

        if "google" in req_lower or "oauth" in req_lower:
            new_reqs.append(Requirement(
                id=f"FR-019",
                category="FUNCTIONAL",
                title="Google OAuth 2.0 Integration",
                description="Users can log in using Google OAuth credentials.",
                priority="HIGH"
            ))
            new_reqs.append(Requirement(
                id=f"SEC-008",
                category="SECURITY",
                title="OAuth Token Verification",
                description="Verify OAuth ID tokens on backend authentication routes.",
                priority="HIGH"
            ))

            for path in existing_files:
                if "auth" in path or "Login" in path or "App" in path or "config" in path:
                    affected_files.append(path)

            affected_agents = ["BackendAgent", "FrontendAgent", "SecurityAgent", "TestingAgent"]
            affected_tests = ["tests/test_auth.py"]

        elif "payment" in req_lower or "stripe" in req_lower:
            new_reqs.append(Requirement(
                id=f"FR-020",
                category="FUNCTIONAL",
                title="Stripe Payment Processing",
                description="Users can checkout securely via Stripe API.",
                priority="HIGH"
            ))
            for path in existing_files:
                if "checkout" in path.lower() or "cart" in path.lower() or "routes" in path.lower():
                    affected_files.append(path)

            affected_agents = ["BackendAgent", "FrontendAgent", "TestingAgent"]
            affected_tests = ["tests/test_payments.py"]

        else:
            new_reqs.append(Requirement(
                id=f"FR-{len(current_spec.functional_requirements) + 1:03d}",
                category="FUNCTIONAL",
                title=change_request[:30],
                description=change_request,
                priority="MEDIUM"
            ))
            affected_agents = ["BackendAgent", "FrontendAgent"]

        return ChangeImpact(
            new_requirements=new_reqs,
            affected_files=affected_files,
            affected_agents=affected_agents,
            affected_tests=affected_tests,
            requires_full_regeneration=False,
            estimated_files_count=len(affected_files)
        )


global_change_impact_analyzer = ChangeImpactAnalyzer()
