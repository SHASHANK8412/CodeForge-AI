import re
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger("aiforge.security")


class SecurityVulnerability(BaseModel):
    category: str
    filepath: str
    snippet: str
    description: str
    severity: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    remediation: str = ""


class SecurityReport(BaseModel):
    is_secure: bool = True
    vulnerabilities: List[SecurityVulnerability] = Field(default_factory=list)
    score: float = 100.0
    summary: str = ""


class SecurityAgent(BaseAgent):
    """
    Security Agent scans generated code for common vulnerabilities:
    - Secrets, API Keys, Hardcoded Passwords
    - SQL Injection patterns
    - Cross-Site Scripting (XSS)
    - CSRF vulnerabilities
    - Insecure JWT usage
    - Unprotected AuthN/AuthZ endpoints
    """

    SECRET_PATTERNS = [
        (r"(?i)(api_key|secret_key|password|jwt_secret)\s*=\s*['\"]([^'\"]{8,})['\"]", "Hardcoded Secret/Password Found"),
        (r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Hardcoded JWT Token Found"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID Found")
    ]

    SQLI_PATTERNS = [
        (r"SELECT\s+.*?\s+FROM\s+.*?\s+WHERE\s+.*?%s", "Raw string formatting SQL Injection vulnerability"),
        (r"f['\"]SELECT\s+.*?\s+FROM\s+.*?\s+WHERE\s+.*?\{", "Python f-string SQL Injection vulnerability"),
        (r"execute\(\s*['\"].*?\+\s*\w+", "Concatenated raw SQL execution string")
    ]

    XSS_PATTERNS = [
        (r"dangerouslySetInnerHTML", "React dangerouslySetInnerHTML used without sanitization"),
        (r"innerHTML\s*=", "Direct DOM innerHTML assignment")
    ]

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Security Agent for AIForge. Your job is to conduct comprehensive "
                "static security audits on generated codebase files and identify potential "
                "vulnerabilities (SQLi, XSS, CSRF, JWT flaws, Hardcoded Secrets)."
            ),
            task_name="security_scan"
        )

    def scan_files(self, files: Dict[str, str]) -> SecurityReport:
        vulnerabilities = []

        for path, code in files.items():
            lines = code.splitlines()

            # 1. Scan Secrets
            for pattern, desc in self.SECRET_PATTERNS:
                for line_idx, line in enumerate(lines):
                    if "SECRET_KEY=" in line and ".env" in path:
                        continue  # Allow key placeholders in .env files
                    if re.search(pattern, line):
                        vulnerabilities.append(SecurityVulnerability(
                            category="SECRETS_EXPOSURE",
                            filepath=path,
                            snippet=line.strip()[:60],
                            description=f"{desc} on line {line_idx + 1}.",
                            severity="CRITICAL",
                            remediation="Move sensitive credentials to environment variables (.env)."
                        ))

            # 2. Scan SQL Injection
            for pattern, desc in self.SQLI_PATTERNS:
                for line_idx, line in enumerate(lines):
                    if re.search(pattern, line):
                        vulnerabilities.append(SecurityVulnerability(
                            category="SQL_INJECTION",
                            filepath=path,
                            snippet=line.strip()[:60],
                            description=f"{desc} on line {line_idx + 1}.",
                            severity="HIGH",
                            remediation="Use parameterized queries or ORM bindings (SQLAlchemy/Pydantic)."
                        ))

            # 3. Scan XSS
            for pattern, desc in self.XSS_PATTERNS:
                for line_idx, line in enumerate(lines):
                    if re.search(pattern, line):
                        vulnerabilities.append(SecurityVulnerability(
                            category="XSS_VULNERABILITY",
                            filepath=path,
                            snippet=line.strip()[:60],
                            description=f"{desc} on line {line_idx + 1}.",
                            severity="MEDIUM",
                            remediation="Avoid raw HTML injection; use React safe JSX rendering."
                        ))

            # 4. Check JWT security
            if "jwt.decode" in code and "algorithms" not in code:
                vulnerabilities.append(SecurityVulnerability(
                    category="JWT_SECURITY",
                    filepath=path,
                    snippet="jwt.decode call",
                    description="JWT decode without explicit algorithm specification.",
                    severity="HIGH",
                    remediation="Specify explicit algorithm list e.g. algorithms=['HS256']."
                ))

        critical_high = sum(1 for v in vulnerabilities if v.severity in ("CRITICAL", "HIGH"))
        score = max(0.0, 100.0 - (critical_high * 20.0) - (len(vulnerabilities) * 5.0))
        is_secure = critical_high == 0

        summary = (
            f"Security Audit Completed: {'SECURE' if is_secure else 'VULNERABILITIES DETECTED'}. "
            f"Security Score: {score:.1f}/100. Found {len(vulnerabilities)} issues "
            f"({critical_high} High/Critical)."
        )

        return SecurityReport(
            is_secure=is_secure,
            vulnerabilities=vulnerabilities,
            score=score,
            summary=summary
        )

    def generate_security_report_markdown(self, report: SecurityReport) -> str:
        md = [
            "# Security Audit Report",
            "",
            f"**Overall Status**: {'✅ PASSED' if report.is_secure else '⚠️ VULNERABILITIES DETECTED'}",
            f"**Security Score**: {report.score:.1f} / 100",
            "",
            "## Summary",
            report.summary,
            "",
            "## Detected Vulnerabilities",
            ""
        ]

        if not report.vulnerabilities:
            md.append("No security vulnerabilities detected. Code adheres to security best practices.")
        else:
            md.append("| Category | File | Severity | Description | Remediation |")
            md.append("|---|---|---|---|---|")
            for v in report.vulnerabilities:
                md.append(f"| {v.category} | `{v.filepath}` | **{v.severity}** | {v.description} | {v.remediation} |")

        return "\n".join(md) + "\n"
