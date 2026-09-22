"""
AIForge Autonomous Engineering Platform — SecurityManager
==========================================================
Orchestrates secret, dependency, SAST, config, API, and Docker scanners.
Computes weighted Security Score (100 minus penalties), evaluates SECURITY_GATE,
and generates SECURITY_REPORT.md artifact.
"""

import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from backend.security.security_scanners import (
    SecretScanner, DependencyScanner, SASTScanner,
    ConfigScanner, APISecurityScanner, DockerGitScanner, SecurityFinding
)
from backend.security.sbom_generator import global_sbom_generator

_logger = logging.getLogger("aiforge.security.manager")


class SecurityReport(BaseModel):
    security_score: float = 100.0
    gate_status: str = "PASSED"  # "PASSED", "WARNING", "FAILED"
    risk_level: str = "LOW"  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    findings: List[SecurityFinding] = Field(default_factory=list)
    api_security_matrix: List[Dict[str, Any]] = Field(default_factory=list)
    sbom: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""


class SecurityManager:
    """
    Central Security Orchestrator for AIForge codebase auditing.
    """

    def __init__(self) -> None:
        self.secret_scanner = SecretScanner()
        self.dep_scanner = DependencyScanner()
        self.sast_scanner = SASTScanner()
        self.config_scanner = ConfigScanner()
        self.api_scanner = APISecurityScanner()
        self.docker_git_scanner = DockerGitScanner()

    def audit_project(self, project_name: str, files_manifest: Dict[str, str]) -> SecurityReport:
        _logger.info(f"[SecurityManager] Starting comprehensive security scan for '{project_name}'...")

        findings: List[SecurityFinding] = []
        findings.extend(self.secret_scanner.scan(files_manifest))
        findings.extend(self.dep_scanner.scan(files_manifest))
        findings.extend(self.sast_scanner.scan(files_manifest))
        findings.extend(self.config_scanner.scan(files_manifest))
        findings.extend(self.docker_git_scanner.scan(files_manifest))

        api_matrix = self.api_scanner.scan(files_manifest)
        sbom_report = global_sbom_generator.generate_sbom(project_name, files_manifest)

        # Calculate Security Score
        score = 100.0
        has_critical = False
        has_high = False

        for f in findings:
            if f.severity == "CRITICAL":
                score -= 20.0
                has_critical = True
            elif f.severity == "HIGH":
                score -= 10.0
                has_high = True
            elif f.severity == "MEDIUM":
                score -= 5.0
            elif f.severity == "LOW":
                score -= 2.0

        score = max(0.0, round(score, 1))

        # Gate Evaluation
        gate_status = "PASSED"
        if has_critical or score < 70.0:
            gate_status = "FAILED"
        elif has_high or score < 85.0:
            gate_status = "WARNING"

        risk_level = "CRITICAL" if has_critical else ("HIGH" if has_high else ("MEDIUM" if score < 90.0 else "LOW"))

        summary = f"Security Audit: {len(findings)} findings. Score: {score}/100. Gate Status: {gate_status}."

        return SecurityReport(
            security_score=score,
            gate_status=gate_status,
            risk_level=risk_level,
            findings=findings,
            api_security_matrix=api_matrix,
            sbom=sbom_report.model_dump(),
            summary=summary
        )

    def generate_security_markdown(self, report: SecurityReport) -> str:
        md = [
            "# 🛡 AIForge Security Audit Report",
            f"**Overall Security Score:** `{report.security_score}/100`  ",
            f"**Gate Status:** `{report.gate_status}` | **Risk Level:** `{report.risk_level}`\n",
            "## Summary Findings",
            f"- **Total Vulnerabilities:** {len(report.findings)}",
            f"- **Critical:** {sum(1 for f in report.findings if f.severity == 'CRITICAL')}",
            f"- **High:** {sum(1 for f in report.findings if f.severity == 'HIGH')}",
            f"- **Medium:** {sum(1 for f in report.findings if f.severity == 'MEDIUM')}\n",
            "## Detailed Findings"
        ]

        for f in report.findings:
            snippet_str = f"`{f.snippet}`" if f.snippet else ""
            md.append(f"### [{f.severity}] {f.description}")
            md.append(f"- **ID:** `{f.id}` | **File:** `{f.file}:{f.line}`")
            md.append(f"- **Recommendation:** {f.recommendation}")
            if snippet_str:
                md.append(f"- **Snippet:** {snippet_str}")
            md.append("")

        return "\n".join(md)


global_security_manager = SecurityManager()
