"""
AIForge Day 26 — OpenTelemetry Tracer & Security Redaction Engine
==================================================================
Captures OpenTelemetry spans, generates trace IDs (trace_abc123), and redacts sensitive data (JWTs, API keys, passwords).
"""

import re
import secrets
import logging
from datetime import datetime
from typing import Dict, Any, List

from backend.observability.models import TraceSpan, SpanKind, DistributedTrace

_logger = logging.getLogger("aiforge.observability.tracer")

SECRET_PATTERNS = [
    re.compile(r'(?i)(bearer\s+|jwt\s+|token=)[a-zA-Z0-9_\-\.]+\b'),
    re.compile(r'(?i)(password|passwd|secret|api_key|apikey|private_key)=[^&\s]+'),
    re.compile(r'(?i)(postgres://|mysql://|mongodb://|sqlite://)[^:@]+:[^@]+@'),
    re.compile(r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----[^-]+-----END\s+(RSA\s+)?PRIVATE\s+KEY-----', re.DOTALL)
]


class OpenTelemetryTracer:
    """
    OpenTelemetry tracer with automatic security redaction.
    """

    def sanitize_attribute_value(self, val: Any) -> Any:
        if isinstance(val, str):
            sanitized = val
            for pat in SECRET_PATTERNS:
                sanitized = pat.sub('[REDACTED_SECRET]', sanitized)
            return sanitized
        elif isinstance(val, dict):
            return self.redact_attributes(val)
        elif isinstance(val, list):
            return [self.sanitize_attribute_value(item) for item in val]
        return val

    def redact_attributes(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        redacted = {}
        for k, v in attrs.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ("auth", "token", "password", "secret", "cookie", "api_key", "private_key")):
                redacted[k] = "[REDACTED_HEADER]"
            else:
                redacted[k] = self.sanitize_attribute_value(v)
        return redacted

    def create_span(
        self,
        trace_id: str,
        name: str,
        kind: SpanKind,
        duration_ms: float,
        status_code: int = 200,
        attributes: Dict[str, Any] = None,
        dna_file_path: str = None
    ) -> TraceSpan:
        span_id = f"span_{secrets.token_urlsafe(6)}"
        safe_attrs = self.redact_attributes(attributes or {})

        return TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            name=name,
            kind=kind,
            duration_ms=round(duration_ms, 2),
            status_code=status_code,
            attributes=safe_attrs,
            dna_file_path=dna_file_path,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat()
        )


global_opentelemetry_tracer = OpenTelemetryTracer()

