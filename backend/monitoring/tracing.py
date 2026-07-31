"""
AIForge OpenTelemetry Distributed Tracing Engine (Day 46)
=========================================================
Attaches unique trace_id to every workflow execution, measures step durations, and logs distributed JSON trace spans across multi-agent workflows.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.monitoring.tracing")


class DistributedTracingEngine:
    """
    OpenTelemetry distributed tracing engine tracking agent execution spans.
    """

    def __init__(self):
        self.traces: Dict[str, List[Dict[str, Any]]] = {}

    def start_trace(self, trace_id: str, workflow_name: str) -> Dict[str, Any]:
        """
        Initializes a distributed trace session.
        """
        trace_record = {
            "trace_id": trace_id,
            "workflow": workflow_name,
            "start_time": time.time(),
            "status": "IN_PROGRESS",
            "spans": []
        }
        self.traces[trace_id] = [trace_record]
        _logger.info(f"DistributedTracingEngine: Started trace '{trace_id}' for workflow '{workflow_name}'")
        return trace_record

    def record_agent_span(
        self,
        trace_id: str,
        agent_name: str,
        duration_ms: float,
        tokens: int = 150,
        status: str = "Success"
    ) -> Dict[str, Any]:
        """
        Appends an OpenTelemetry span for a specific agent execution stage.
        """
        span = {
            "trace_id": trace_id,
            "agent": agent_name,
            "duration_ms": duration_ms,
            "tokens": tokens,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        if trace_id in self.traces:
            self.traces[trace_id][0]["spans"].append(span)

        _logger.info(f"DistributedTracingEngine: Record span [{agent_name}] trace_id='{trace_id}' ({duration_ms}ms, {tokens} tokens)")
        return span

    def get_trace(self, trace_id: str) -> Optional[List[Dict[str, Any]]]:
        return self.traces.get(trace_id)


global_distributed_tracing = DistributedTracingEngine()
