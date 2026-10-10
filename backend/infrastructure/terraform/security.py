"""
AIForge Day 32 — Infrastructure Security Analyzer
==================================================
Audits HCL files for security vulnerabilities: public databases, open SSH ingress,
unencrypted storage, overly permissive IAM policies, and exposed secrets.
"""

import re
import logging
from typing import Dict, Any, List

from backend.infrastructure.terraform.models import SecurityAuditResult

_logger = logging.getLogger("aiforge.infrastructure.security")

SECURITY_RULES = [
    (re.compile(r'publicly_accessible\s*=\s*true'), "Public Database Violation: Database instance must not be publicly accessible (`publicly_accessible = false`)."),
    (re.compile(r'ingress\s*\{[^}]*from_port\s*=\s*22[^}]*0\.0\.0\.0/0'), "Unrestricted SSH Violation: Ingress port 22 must not allow 0.0.0.0/0."),
    (re.compile(r'storage_encrypted\s*=\s*false'), "Unencrypted Storage Violation: DB and EBS storage must enable encryption (`storage_encrypted = true`)."),
    (re.compile(r'Action\s*=\s*["\']\*["\']'), "Permissive IAM Violation: IAM policy contains wildcards Action='*'."),
    (re.compile(r'(?i)(password|secret|key|token)\s*=\s*["\'][a-zA-Z0-9_\-\.\:\@]{6,}["\']'), "Plaintext Secret Violation: Plaintext credential found in HCL. Use secret references.")
]


class InfrastructureSecurityAnalyzer:
    """
    Scans HCL infrastructure configurations for security policy violations.
    """

    def scan_infrastructure_security(self, files: Dict[str, str]) -> SecurityAuditResult:
        violations = []
        warnings = []

        for filename, content in files.items():
            if not isinstance(content, str):
                continue

            for pat, rule_msg in SECURITY_RULES:
                if pat.search(content):
                    violations.append(f"{rule_msg} (in '{filename}')")

        passed = len(violations) == 0
        if not passed:
            _logger.error(f"[InfraSecurity] Audit FAILED with {len(violations)} violation(s): {violations}")
        else:
            _logger.info("[InfraSecurity] Audit PASSED cleanly. Zero security violations found.")

        return SecurityAuditResult(passed=passed, violations=violations, warnings=warnings)


global_infra_security_analyzer = InfrastructureSecurityAnalyzer()
