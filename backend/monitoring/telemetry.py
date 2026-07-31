"""
AIForge OpenTelemetry Distributed Tracing & Prometheus Metrics Engine
======================================================================
Provides OpenTelemetry span creation, agent latency tracking, and Prometheus metrics exporting.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.monitoring.telemetry")


class TelemetryEngine:
    """
    OpenTelemetry distributed tracing and Prometheus metric aggregator for multi-agent workflows.
    """

    def __init__(self):
        self.spans: List[Dict[str, Any]] = []

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        span = {
            "span_id": f"span_{int(time.time() * 1000)}",
            "name": name,
            "attributes": attributes or {},
            "start_time": time.time(),
            "status": "RUNNING"
        }
        self.spans.append(span)
        return span

    def end_span(self, span: Dict[str, Any], status: str = "OK") -> Dict[str, Any]:
        span["end_time"] = time.time()
        span["duration_ms"] = round((span["end_time"] - span["start_time"]) * 1000, 2)
        span["status"] = status
        _logger.info(f"TelemetryEngine: Span '{span['name']}' completed in {span['duration_ms']}ms")
        return span

    def get_prometheus_metrics(self) -> str:
        """
        Exports metrics in standard Prometheus exposition text format.
        """
        total_spans = len(self.spans)
        avg_dur = round(sum(s.get("duration_ms", 0) for s in self.spans) / max(1, total_spans), 2) if self.spans else 0.0

        return (
            f"# HELP aiforge_agent_spans_total Total agent execution spans created\n"
            f"# TYPE aiforge_agent_spans_total counter\n"
            f"aiforge_agent_spans_total {total_spans}\n\n"
            f"# HELP aiforge_agent_duration_ms Average agent execution duration in ms\n"
            f"# TYPE aiforge_agent_duration_ms gauge\n"
            f"aiforge_agent_duration_ms {avg_dur}\n"
        )


global_telemetry_engine = TelemetryEngine()
