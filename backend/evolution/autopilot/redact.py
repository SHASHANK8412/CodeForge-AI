"""Secret redaction for everything Autopilot stores, shows or sends to a model."""

import os
import re

from backend.rag.ingestion import redact_secrets as _redact_known_patterns

_PATTERNS = [
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9\-._~+/]{16,}=*"), r"\1 [REDACTED]"),
    (re.compile(r"(?i)(://[^:/\s]+:)[^@\s]+(@)"), r"\1[REDACTED]\2"),                      # user:pass@host
    (re.compile(r"(?i)\b((?:password|passwd|secret|token|api[_-]?key)\s*[=:]\s*)['\"]?[^\s'\",]{6,}"), r"\1[REDACTED]"),
]
_ENV_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL")
_env_cache: dict = {"snapshot": None, "secrets": []}


def _secret_env_values():
    """(name, value) of secret-looking environment variables; recomputed only when the environment changes."""
    snapshot = tuple(sorted(os.environ.items()))
    if snapshot != _env_cache["snapshot"]:
        _env_cache["snapshot"] = snapshot
        _env_cache["secrets"] = [(name.upper(), value) for name, value in snapshot
                                 if value and len(value) >= 8 and any(m in name.upper() for m in _ENV_MARKERS)]
    return _env_cache["secrets"]


def redact(text: str, limit: int = 0) -> str:
    """Known secret formats, credentials in URLs and assignments, and the values of this
    process's secret-looking environment variables are replaced; optionally truncated."""
    if not text:
        return ""
    out = _redact_known_patterns(text)
    for pattern, replacement in _PATTERNS:
        out = pattern.sub(replacement, out)
    for name, value in _secret_env_values():
        if value in out:
            out = out.replace(value, f"[REDACTED_{name}]")
    if limit and len(out) > limit:
        out = out[:limit] + f"\n[... {len(out) - limit} characters truncated]"
    return out
