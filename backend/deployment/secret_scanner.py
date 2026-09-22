"""
AIForge Secret Scanner Module
=============================
Scans project files and configuration for committed secrets, API keys, tokens,
and private credentials before deployment. Blocks deployment if any unmasked
secrets are detected.
"""

import re
import logging
from typing import Dict, List, Any
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.deployment.secret_scanner")


class SecretFinding(BaseModel):
    file_path: str
    line_number: int
    secret_type: str
    masked_value: str
    recommendation: str = "Move credential to an environment variable in .env"


class SecretScanResult(BaseModel):
    is_clean: bool = True
    total_findings: int = 0
    findings: List[SecretFinding] = Field(default_factory=list)
    message: str = "No committed secrets detected."


class SecretScanner:
    """
    Regex and heuristic scanner for credential leaks.
    """

    PATTERNS = [
        ("AWS Access Key", r"(?i)(?:aws_access_key_id|aws_secret_access_key)\s*=\s*['\"]([A-Za-z0-9/+=]{16,40})['\"]"),
        ("JWT Secret Key", r"(?i)(?:jwt_secret|jwt_secret_key)\s*=\s*['\"]([A-Za-z0-9_\-\.]{16,})['\"]"),
        ("Generic API Key", r"(?i)(?:api_key|apikey|secret_key)\s*=\s*['\"]([A-Za-z0-9_\-\.]{16,})['\"]"),
        ("Database Connection with Password", r"(?i)(?:postgres|postgresql|mysql|mongodb(?:\+srv)?):\/\/[^:\/\s]+:([^@\/\s]{4,})@[^:\/\s]+"),
        ("Private Key Header", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        ("Slack / Discord Token", r"(?i)(?:xoxb-|xoxp-|discord_token)\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?"),
        ("OpenAI / Anthropic Key", r"(?i)(?:sk-[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9]{20,})")
    ]

    SAFE_KEYWORDS = {
        "placeholder", "your_secret", "dummy", "replace_me", "getenv", "process.env",
        "os.environ", "example", "mock", "test_secret", "aiforge_dev_secret", "<secret>"
    }

    def mask_secret(self, secret: str) -> str:
        if not secret or len(secret) <= 4:
            return "••••"
        return f"{secret[:2]}••••••••{secret[-2:]}"

    def scan_files(self, files_manifest: Dict[str, str]) -> SecretScanResult:
        findings: List[SecretFinding] = []

        for path, content in files_manifest.items():
            # Skip documentation, example files, and test files with known dummy data
            if path.endswith(".example") or path.endswith(".md") or "dummy" in path:
                continue

            lines = content.splitlines()
            for line_idx, line in enumerate(lines, start=1):
                # Ignore commented out descriptions in code
                stripped = line.strip()
                if stripped.startswith("#") and "example" in stripped.lower():
                    continue

                for label, pattern in self.PATTERNS:
                    match = re.search(pattern, line)
                    if match:
                        secret_val = match.group(1) if match.groups() else match.group(0)
                        # Check if it's safe placeholder
                        if any(safe in secret_val.lower() for safe in self.SAFE_KEYWORDS):
                            continue

                        findings.append(SecretFinding(
                            file_path=path,
                            line_number=line_idx,
                            secret_type=label,
                            masked_value=self.mask_secret(secret_val),
                            recommendation=f"Move {label} in '{path}' at line {line_idx} to an environment variable."
                        ))

        is_clean = (len(findings) == 0)
        msg = "No committed secrets detected. Project is safe for deployment." if is_clean else f"🚨 DEPLOYMENT BLOCKED: {len(findings)} committed secret(s) detected."

        if not is_clean:
            _logger.warning("SecretScanner detected %d potential leak(s).", len(findings))

        return SecretScanResult(
            is_clean=is_clean,
            total_findings=len(findings),
            findings=findings,
            message=msg
        )


global_secret_scanner = SecretScanner()
