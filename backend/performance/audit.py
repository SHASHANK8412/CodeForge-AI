"""
AIForge Quality Recovery Day 14 — Security Audit Logger
======================================================
Provides AuditLogger recording consequential actions (repository edit, git commit, remote push, PR)
with mandatory secret redaction.
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional, List

from backend.performance.models import AuditEvent
from backend.repository.scanner import global_secret_scanner

logger = logging.getLogger("aiforge.performance.audit")


class AuditLogger:
    """Security and compliance audit logger."""

    def __init__(self):
        self._events: List[AuditEvent] = []

    def log_event(
        self,
        request_id: str,
        action: str,
        result: str,
        workflow_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Logs an audited event with secret redaction."""
        safe_meta = {}
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, str):
                    safe_meta[k] = global_secret_scanner.redact_secrets(v)
                else:
                    safe_meta[k] = v

        event = AuditEvent(
            event_id=f"audit_{uuid.uuid4().hex[:10]}",
            request_id=request_id,
            workflow_id=workflow_id,
            action=action,
            result=result,
            timestamp=time.time(),
            metadata=safe_meta
        )
        self._events.append(event)
        logger.info(f"[{request_id}]{f'[{workflow_id}]' if workflow_id else ''} AuditEvent: {action} -> {result}")
        return event

    def get_events(self) -> List[AuditEvent]:
        return list(self._events)


global_audit_logger = AuditLogger()
