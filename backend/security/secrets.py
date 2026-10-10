"""
AIForge V2 — Secret Scanner Engine
===================================
Scans code, environment variables, RAG documents, and project outputs for credential leaks
(API keys, private keys, JWT secrets, passwords, database connection strings, cloud keys).
Redacts secrets automatically (e.g. sk-****abcd).
"""

import re
import logging
from typing import Dict, Any, List, Tuple

from backend.security.models import SecretFinding, Severity

_logger = logging.getLogger("aiforge.security.secrets")

SENSITIVE_FILENAME_PATTERNS = [
    r"^\.env(\..*)?$",
    r".*\.pem$",
    r".*\.key$",
    r"^id_rsa$",
    r"^credentials\.json$",
    r"^secrets\.json$",
]

SECRET_RULES: List[Tuple[str, str, Severity, str]] = [
    (
        "OPENAI_API_KEY",
        r"(sk-[a-zA-Z0-9]{20,})",
        Severity.CRITICAL,
        "Potential OpenAI API key detected"
    ),
    (
        "GENERIC_API_KEY",
        r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*[\"']?([a-zA-Z0-9_\-]{16,})[\"']?",
        Severity.CRITICAL,
        "Potential API key or secret token detected"
    ),
    (
        "AWS_ACCESS_KEY",
        r"(AKIA[0-9A-Z]{16})",
        Severity.CRITICAL,
        "Potential AWS Access Key ID detected"
    ),
    (
        "DATABASE_URL",
        r"(postgres(?:ql)?|mysql|mongodb(?:\+srv)?):\/\/[^\s:]+:[^\s@]+@[^\s\/]+",
        Severity.HIGH,
        "Database connection string with plain text credentials detected"
    ),
    (
        "PRIVATE_KEY",
        r"-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----",
        Severity.CRITICAL,
        "RSA / SSH Private Key block detected"
    ),
    (
        "JWT_SECRET",
        r"(?i)(jwt[_-]?secret|session[_-]?secret)\s*[:=]\s*[\"']?([a-zA-Z0-9_\-]{8,})[\"']?",
        Severity.HIGH,
        "Hardcoded JWT or Session signing secret detected"
    ),
]


class SecretScanner:
    """
    Scans project code files and text strings for sensitive secrets and credential leaks.
    """

    def is_sensitive_file(self, filename: str) -> bool:
        basename = filename.split("/")[-1].split("\\")[-1]
        for pattern in SENSITIVE_FILENAME_PATTERNS:
            if re.match(pattern, basename, re.IGNORECASE):
                return True
        return False

    def redact(self, value: str) -> str:
        if not value or len(value) <= 6:
            return "******"
        return f"{value[:3]}****{value[-4:]}"

    def scan_text(self, text: str, file_path: str = "raw_content") -> List[SecretFinding]:
        findings: List[SecretFinding] = []
        if not text:
            return findings

        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            for secret_type, pattern, severity, msg in SECRET_RULES:
                matches = re.finditer(pattern, line)
                for match in matches:
                    matched_val = match.group(1) if match.groups() else match.group(0)
                    findings.append(
                        SecretFinding(
                            type=secret_type,
                            file=file_path,
                            line=idx,
                            severity=severity,
                            message=msg,
                            redacted_sample=self.redact(matched_val)
                        )
                    )
        return findings

    def scan_files_map(self, files_map: Dict[str, str]) -> List[SecretFinding]:
        all_findings: List[SecretFinding] = []
        for path, content in files_map.items():
            if self.is_sensitive_file(path):
                all_findings.append(
                    SecretFinding(
                        type="SENSITIVE_FILE",
                        file=path,
                        line=1,
                        severity=Severity.CRITICAL,
                        message=f"Sensitive file '{path}' detected in project workspace",
                        redacted_sample="[RESTRICTED_FILE]"
                    )
                )
            all_findings.extend(self.scan_text(content, path))
        return all_findings


global_secret_scanner = SecretScanner()
