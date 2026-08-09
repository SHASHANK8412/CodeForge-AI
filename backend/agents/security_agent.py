"""
AIForge V2 — Dedicated SecurityAgent
====================================
Specialized agent that inspects generated project code, architecture specs,
and memory for vulnerabilities and produces structured security findings.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.security.models import SecurityReport
from backend.security.service import global_security_service

_logger = logging.getLogger("aiforge.agents.security_agent")


class SecurityAgent:
    """
    Dedicated Security Agent for LangGraph workflows and repair pipelines.
    """

    def analyze_project(
        self,
        project_id: str,
        files_map: Dict[str, str],
        user_id: str = "demo_user"
    ) -> SecurityReport:
        _logger.info(f"[SecurityAgent] Inspecting {len(files_map)} files for project '{project_id}'")
        return global_security_service.run_full_security_scan(project_id, files_map, user_id)


global_security_agent = SecurityAgent()
