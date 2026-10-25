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


def mask_secret_lines(path: str, text: str):
    """
    For sending a file to a model: every line that holds a secret-like value is replaced by a marker
    comment, so the model sees the code but never the value. Returns (masked text, {marker: original line}).
    """
    hidden = {}
    lines = text.split("\n")
    comment = "//" if path.endswith((".js", ".jsx", ".ts", ".tsx")) else "#"
    for i, line in enumerate(lines):
        if redact(line) != line:
            marker = f"{comment} AIFORGE_HIDDEN_LINE_{len(hidden) + 1}: holds a secret; keep this line exactly as it is"
            hidden[marker] = line
            lines[i] = line[:len(line) - len(line.lstrip())] + marker
    return "\n".join(lines), hidden


def unmask_secret_lines(text: str, hidden: dict) -> str:
    """Put the original lines back. Raises ValueError when the model dropped, changed or duplicated a marker."""
    lines = text.split("\n")
    for marker, original in hidden.items():
        at = [i for i, line in enumerate(lines) if line.strip() == marker]
        if len(at) != 1:
            raise ValueError("a line hidden from the model because it holds a secret was removed or changed; "
                             "keep every AIFORGE_HIDDEN_LINE marker exactly as it is")
        lines[at[0]] = original
    return "\n".join(lines)
