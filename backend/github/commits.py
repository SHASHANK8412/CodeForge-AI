"""
AIForge Day 30 — Commit Manager & Pre-Commit Secret Scanner
============================================================
Enforces pre-commit secret scanning (blocking commits if secrets are detected)
and creates structured, meaningful Git commits.
"""

import re
import secrets
import logging
from typing import Dict, Any, List, Tuple

from backend.github.models import CommitInfo, SecretScanResult

_logger = logging.getLogger("aiforge.github.commits")

SECRET_DETECTION_PATTERNS = [
    (re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}'), "Bearer JWT Token"),
    (re.compile(r'(?i)ghp_[a-zA-Z0-9]{36}'), "GitHub Personal Access Token"),
    (re.compile(r'(?i)sk_live_[a-zA-Z0-9]{24}'), "Stripe Live Secret Key"),
    (re.compile(r'-----BEGIN\s+(RSA|EC|PRIVATE)\s+KEY-----'), "Private Key"),
    (re.compile(r'(?i)(password|passwd|api_key|secret)\s*=\s*["\'][a-zA-Z0-9_\-\.\:\@]{8,}["\']'), "Plaintext Secret")
]


class PreCommitSecretScanner:
    """
    Scans code changes for credentials prior to committing.
    """

    def scan_changes(self, files_content: Dict[str, str]) -> SecretScanResult:
        found_secrets = []
        for filepath, content in files_content.items():
            if not isinstance(content, str):
                continue
            for pat, secret_type in SECRET_DETECTION_PATTERNS:
                if pat.search(content):
                    found_secrets.append(f"{secret_type} in '{filepath}'")

        if found_secrets:
            _logger.error(f"[SecretScanner] BLOCKED COMMIT! Found {len(found_secrets)} secret(s): {found_secrets}")
            return SecretScanResult(
                contains_secrets=True,
                secrets_found=found_secrets,
                blocked_commit=True
            )

        return SecretScanResult(contains_secrets=False, secrets_found=[], blocked_commit=False)


class CommitManager:
    """
    Creates meaningful commits after passing security scans.
    """

    def __init__(self):
        self.scanner = PreCommitSecretScanner()

    def create_commit(
        self,
        branch_name: str,
        message: str,
        files_content: Dict[str, str],
        author: str = "AIForge Agent <agent@aiforge.dev>"
    ) -> CommitInfo:
        scan_res = self.scanner.scan_changes(files_content)
        if scan_res.blocked_commit:
            raise SecurityError(f"Commit blocked by Pre-Commit Secret Scanner! Credentials detected: {scan_res.secrets_found}")

        sha = f"sha_{secrets.token_hex(4)}"
        _logger.info(f"[CommitManager] Created commit '{sha[:7]}' on branch '{branch_name}': '{message}'")
        return CommitInfo(
            sha=sha,
            message=message,
            author=author,
            files_changed=list(files_content.keys())
        )


class SecurityError(Exception):
    pass


global_commit_manager = CommitManager()
