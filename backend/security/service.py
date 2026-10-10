"""
AIForge V2 — Centralized SecurityService
========================================
Unifies code security scanning, secret scanning, dependency audits,
prompt injection defense, security scoring (0-100), audit logs, and false positive management.
"""

import json
import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from backend.security.models import (
    SecurityReport, SecurityFinding, SecretFinding, DependencyScanResult,
    Severity, FindingStatus, SecurityAuditEvent, PromptGuardResult
)
from backend.security.secrets import global_secret_scanner
from backend.security.scanner import global_code_security_scanner
from backend.security.dependencies import global_dependency_scanner
from backend.security.prompt_guard import global_prompt_guard
from backend.security.permissions import global_security_permissions
from backend.security.sandbox import global_docker_sandbox

_logger = logging.getLogger("aiforge.security.service")

AUDIT_LOG_FILE = "data/security_audit_logs.json"


class SecurityService:
    """
    Centralized Security Service orchestrating all AIForge cybersecurity operations.
    """

    def __init__(self):
        self._audit_logs: List[SecurityAuditEvent] = []

    def calculate_security_score(
        self,
        critical_count: int,
        high_count: int,
        medium_count: int,
        low_count: int,
        secrets_count: int
    ) -> float:
        """
        Calculates Security Score (0-100) based on weighted findings.
        Deductions:
        - Critical Finding / Secret: -25 pts each
        - High Finding: -10 pts each
        - Medium Finding: -4 pts each
        - Low Finding: -1 pt each
        """
        score = 100.0
        score -= secrets_count * 25.0
        score -= critical_count * 25.0
        score -= high_count * 10.0
        score -= medium_count * 4.0
        score -= low_count * 1.0
        return max(0.0, round(score, 1))

    def log_audit_event(self, event_type: str, project_id: str, user_id: str, details: Dict[str, Any]):
        evt = SecurityAuditEvent(
            id=f"audit_{secrets.token_urlsafe(6)}",
            event_type=event_type,
            project_id=project_id,
            user_id=user_id,
            details=details,
            timestamp=datetime.now().isoformat()
        )
        self._audit_logs.append(evt)
        _logger.info(f"[SecurityAudit] {event_type} for project '{project_id}' by user '{user_id}'")

    def run_full_security_scan(
        self,
        project_id: str,
        files_map: Dict[str, str],
        user_id: str = "demo_user"
    ) -> SecurityReport:
        self.log_audit_event("security_scan_started", project_id, user_id, {"file_count": len(files_map)})

        # 1. Secret Scanning
        secret_findings = global_secret_scanner.scan_files_map(files_map)
        if secret_findings:
            self.log_audit_event("secret_detected", project_id, user_id, {"count": len(secret_findings)})

        # 2. Code Vulnerability AST Scanning
        code_findings = global_code_security_scanner.scan_project_code(files_map)
        if code_findings:
            self.log_audit_event("vulnerability_detected", project_id, user_id, {"count": len(code_findings)})

        # 3. Dependency Scanning
        dep_result = global_dependency_scanner.scan_manifests(files_map)

        # Count active open findings
        open_code_findings = [f for f in code_findings if f.status == FindingStatus.OPEN]
        crit = sum(1 for f in open_code_findings if f.severity == Severity.CRITICAL)
        high = sum(1 for f in open_code_findings if f.severity == Severity.HIGH)
        med = sum(1 for f in open_code_findings if f.severity == Severity.MEDIUM)
        low = sum(1 for f in open_code_findings if f.severity == Severity.LOW)

        sec_score = self.calculate_security_score(crit, high, med, low, len(secret_findings))

        # Determine SECURITY_GATE decision
        if crit > 0 or len(secret_findings) > 0:
            decision = "BLOCK"
            self.log_audit_event("deployment_blocked", project_id, user_id, {"reason": "CRITICAL security finding or secret leak"})
        elif high > 0:
            decision = "WARN"
        else:
            decision = "PASS"

        report = SecurityReport(
            project_id=project_id,
            security_score=sec_score,
            decision=decision,
            total_findings=len(open_code_findings),
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            findings=open_code_findings,
            secrets=secret_findings,
            dependency_summary=dep_result,
            scanned_at=datetime.now().isoformat()
        )

        self.log_audit_event("security_scan_completed", project_id, user_id, {"score": sec_score, "decision": decision})
        return report

    def mark_false_positive(
        self,
        project_id: str,
        finding_id: str,
        reason: str,
        user_id: str = "demo_user"
    ) -> bool:
        self.log_audit_event("false_positive_marked", project_id, user_id, {"finding_id": finding_id, "reason": reason})
        return True


global_security_service = SecurityService()
