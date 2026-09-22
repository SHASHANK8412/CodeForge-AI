"""
AIForge V2 — Dependency Security Scanner Engine
===============================================
Analyzes requirements.txt, pyproject.toml, package.json for known vulnerabilities.
Returns structured counts and severity levels.
"""

import re
import logging
from typing import Dict, Any, List

from backend.security.models import DependencyScanResult, DependencyVulnerability, Severity

_logger = logging.getLogger("aiforge.security.dependencies")

KNOWN_VULNERABLE_PACKAGES = {
    "pyyaml": ("< 5.4", "CVE-2020-14343", Severity.HIGH, "Arbitrary code execution via UnsafeLoader"),
    "requests": ("< 2.31.0", "CVE-2023-32681", Severity.MEDIUM, "Proxy-Authorization header leak on redirect"),
    "urllib3": ("< 1.26.17", "CVE-2023-45803", Severity.MEDIUM, "Request body leak on redirect"),
    "express": ("< 4.19.2", "CVE-2024-29041", Severity.HIGH, "Open redirect vulnerability in res.location"),
    "axios": ("< 1.7.4", "CVE-2024-39338", Severity.HIGH, "Server-Side Request Forgery via relative URL path"),
}


class DependencyScanner:
    """
    Scans project dependency manifests for known CVEs.
    """

    def scan_manifests(self, files_map: Dict[str, str]) -> DependencyScanResult:
        vulnerabilities: List[DependencyVulnerability] = []

        manifest_found = False
        for path, content in files_map.items():
            fname = path.split("/")[-1].split("\\")[-1].lower()
            if fname in ("requirements.txt", "pyproject.toml", "package.json"):
                manifest_found = True
                for pkg_name, (version_spec, cve_id, severity, summary) in KNOWN_VULNERABLE_PACKAGES.items():
                    if re.search(r"\b" + re.escape(pkg_name) + r"\b", content, re.IGNORECASE):
                        vulnerabilities.append(
                            DependencyVulnerability(
                                package_name=pkg_name,
                                installed_version=version_spec,
                                vulnerability_id=cve_id,
                                severity=severity,
                                summary=summary
                            )
                        )

        if not manifest_found:
            return DependencyScanResult(
                total=0,
                critical=0,
                high=0,
                medium=0,
                low=0,
                vulnerabilities=[],
                status_message="Dependency scan unavailable (No manifest file found)"
            )

        crit = sum(1 for v in vulnerabilities if v.severity == Severity.CRITICAL)
        high = sum(1 for v in vulnerabilities if v.severity == Severity.HIGH)
        med = sum(1 for v in vulnerabilities if v.severity == Severity.MEDIUM)
        low = sum(1 for v in vulnerabilities if v.severity == Severity.LOW)

        return DependencyScanResult(
            total=len(vulnerabilities),
            critical=crit,
            high=high,
            medium=med,
            low=low,
            vulnerabilities=vulnerabilities,
            status_message=f"Dependency scan complete: {len(vulnerabilities)} vulnerabilities identified."
        )


global_dependency_scanner = DependencyScanner()
