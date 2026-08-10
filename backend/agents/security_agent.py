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


from backend.security.security_manager import global_security_manager, SecurityReport as ManagerReport


class SecurityAgent:
    """
    Dedicated Security Agent for LangGraph workflows and repair pipelines.
    """

    def scan_project(self, project_name: str, files_manifest: Dict[str, str]) -> ManagerReport:
        return global_security_manager.audit_project(project_name, files_manifest)

    def scan_files(self, files_map: Dict[str, str], project_id: str = "default_project") -> Any:
        return self.scan_project(project_id, files_map)

    def generate_security_report_markdown(self, report: Any) -> str:
        if hasattr(report, "security_score"):
            return global_security_manager.generate_security_markdown(report)
        md = [f"# Security Audit Report\n**Score**: {getattr(report, 'score', 100)}/100\n"]
        return "\n".join(md)


global_security_agent = SecurityAgent()
