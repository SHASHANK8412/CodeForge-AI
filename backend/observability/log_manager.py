"""
AIForge Log Manager & Secret Redaction Module
=============================================
Collects, normalizes, and redacts logs across services (frontend, backend, containers, deployment, E2E).
Redacts passwords, tokens, API keys, JWTs, and database credentials to prevent secret leaks.
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.observability.log_manager")


class LogEntry(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    formatted_time: str = ""
    service: str  # frontend, backend, database, deployment, e2e
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message: str
    request_id: Optional[str] = None
    deployment_id: Optional[str] = None


class LogManager:
    """
    Central log aggregator with automatic secret redaction.
    """

    def __init__(self):
        self._logs: List[LogEntry] = []

    def redact_secrets(self, text: str) -> str:
        if not text:
            return ""

        # Redact Authorization Bearer tokens
        text = re.sub(r"(?i)(authorization:\s*bearer\s+)[^\s'\"]+", r"\1********", text)
        # Redact passwords in connection strings or JSON
        text = re.sub(r"(?i)(password|secret|key|jwt_secret)=['\"]?[^'\";\s]+['\"]?", r"\1=********", text)
        # Redact postgresql://user:pass@host
        text = re.sub(r"(postgresql|mysql|mongodb)(\+[\w+]+)?://([^:]+):([^@]+)@", r"\1://\3:********@", text)

        return text

    def log(
        self,
        service: str,
        level: str,
        message: str,
        request_id: Optional[str] = None,
        deployment_id: Optional[str] = None
    ) -> LogEntry:
        clean_msg = self.redact_secrets(message)
        ts = time.time()
        entry = LogEntry(
            timestamp=ts,
            formatted_time=time.strftime("%H:%M:%S", time.localtime(ts)),
            service=service,
            level=level.upper(),
            message=clean_msg,
            request_id=request_id,
            deployment_id=deployment_id
        )
        self._logs.insert(0, entry)

        if len(self._logs) > 2000:
            self._logs.pop()

        return entry

    def get_logs(
        self,
        service: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        results = list(self._logs)
        if service:
            results = [l for l in results if l.service == service]
        if level:
            results = [l for l in results if l.level == level.upper()]
        return results[:limit]


global_log_manager = LogManager()
