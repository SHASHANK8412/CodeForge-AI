"""
AIForge Error Analyzer Module
=============================
Groups repeated HTTP 5xx errors and exceptions into categorized clusters
(e.g., DatabaseConnectionError, AuthenticationError, ValidationError).
"""

import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.observability.error_analyzer")


class ErrorCluster(BaseModel):
    category: str
    occurrences: int = 1
    sample_error: str
    affected_endpoints: List[str] = Field(default_factory=list)


class ErrorAnalyzer:
    """
    Error grouping engine for 5xx responses and application exceptions.
    """

    def __init__(self):
        self._clusters: Dict[str, ErrorCluster] = {}

    def classify_error(self, message: str) -> str:
        msg_lower = message.lower()
        if "db" in msg_lower or "database" in msg_lower or "postgres" in msg_lower or "connection" in msg_lower or "psycopg" in msg_lower or "operationalerror" in msg_lower:
            return "DatabaseConnectionError"
        if "auth" in msg_lower or "jwt" in msg_lower or "token" in msg_lower or "401" in msg_lower:
            return "AuthenticationError"
        if "validation" in msg_lower or "pydantic" in msg_lower or "valueerror" in msg_lower:
            return "ValidationError"
        if "import" in msg_lower or "module" in msg_lower:
            return "DependencyModuleError"
        return "InternalServerError"

    def record_error(self, message: str, endpoint: str = "/"):
        cat = self.classify_error(message)
        if cat in self._clusters:
            self._clusters[cat].occurrences += 1
            if endpoint not in self._clusters[cat].affected_endpoints:
                self._clusters[cat].affected_endpoints.append(endpoint)
        else:
            self._clusters[cat] = ErrorCluster(
                category=cat,
                occurrences=1,
                sample_error=message,
                affected_endpoints=[endpoint]
            )

    def get_clusters(self) -> List[ErrorCluster]:
        return sorted(list(self._clusters.values()), key=lambda c: c.occurrences, reverse=True)


global_error_analyzer = ErrorAnalyzer()
