"""
AIForge Day 26 — Database Telemetry Instrumentor
================================================
Captures database span telemetry (SELECT / INSERT / UPDATE durations and query operation types) without exposing credentials.
"""

import logging
from typing import Dict, Any

from backend.observability.models import TraceSpan, SpanKind
from backend.observability.tracer import global_opentelemetry_tracer

_logger = logging.getLogger("aiforge.observability.db_telemetry")


class DatabaseTelemetryInstrumentor:
    """
    Generates sanitized database telemetry spans.
    """

    def record_db_span(
        self,
        trace_id: str,
        operation_type: str,
        table_name: str,
        duration_ms: float,
        connection_info: str = "postgresql://localhost:5432/aiforge_db",
        statement: str = None
    ) -> TraceSpan:
        _logger.debug(f"[DBTelemetry] Recording '{operation_type}' on '{table_name}' ({duration_ms}ms)")

        # Connection info sanitization - ensure credentials stripped
        safe_conn = connection_info
        if "@" in safe_conn:
            # Replace credentials part
            proto, rest = safe_conn.split("://", 1) if "://" in safe_conn else ("", safe_conn)
            if "@" in rest:
                _, host_db = rest.split("@", 1)
                safe_conn = f"{proto}://[REDACTED_USER]:[REDACTED_PASSWORD]@{host_db}"

        safe_statement = statement or f"{operation_type.upper()} FROM {table_name}"
        # Sanitize sensitive literals from statement if provided
        for kw in ("password", "secret", "token", "api_key"):
            if kw in safe_statement.lower():
                safe_statement = "[REDACTED_SENSITIVE_STATEMENT]"

        attrs = {
            "db.system": "postgresql",
            "db.name": "aiforge_db",
            "db.operation": operation_type.upper(),
            "db.sql.table": table_name,
            "db.statement": safe_statement,
            "db.connection": safe_conn
        }

        return global_opentelemetry_tracer.create_span(
            trace_id=trace_id,
            name=f"PostgreSQL {operation_type.upper()} {table_name}",
            kind=SpanKind.DATABASE,
            duration_ms=duration_ms,
            status_code=200,
            attributes=attrs,
            dna_file_path="backend/repositories/orders.py"
        )


global_database_telemetry_instrumentor = DatabaseTelemetryInstrumentor()

