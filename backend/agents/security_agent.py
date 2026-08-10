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

    def scan_files(self, files_map: Dict[str, str], project_id: str = "default_project") -> SecurityReport:
        return self.analyze_project(project_id, files_map)

    def generate_security_report_markdown(self, report: SecurityReport) -> str:
        md = [f"# Security Audit Report\n**Score**: {report.score}/100\n"]
        if report.vulnerabilities:
            md.append("## Vulnerabilities Found:")
            for v in report.vulnerabilities:
                md.append(f"- **[{v.severity}]** {v.title}: {v.description}")
        else:
            md.append("✔ No high-severity vulnerabilities detected.")
        return "\n".join(md)


global_security_agent = SecurityAgent()
