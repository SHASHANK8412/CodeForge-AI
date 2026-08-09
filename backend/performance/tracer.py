"""
AIForge Quality Recovery Day 14 — Telemetry, Request Tracing & Structured Logging
===================================================================================
Provides RequestTrace, StageTrace, correlation IDs (request_id, workflow_id),
context-managed stage tracking, and structured logging without heartbeat spam.
"""

import time
import uuid
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Generator

from backend.performance.models import RequestTrace, StageTrace, PipelinePath
from backend.performance.config import global_performance_config
from backend.repository.scanner import global_secret_scanner

logger = logging.getLogger("aiforge.performance.tracer")


class RequestTracer:
    """
    Centralized telemetry tracer managing active RequestTrace instances.
    Provides correlation IDs, timing, model/tool call counters, and secret redaction.
    """

    def __init__(self):
        self._active_traces: Dict[str, RequestTrace] = {}

    def start_trace(
        self,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        path: PipelinePath = PipelinePath.STANDARD
    ) -> RequestTrace:
        """Starts and registers a new RequestTrace."""
        req_id = request_id or f"req_{uuid.uuid4().hex[:10]}"
        trace = RequestTrace(
            request_id=req_id,
            session_id=session_id,
            workflow_id=workflow_id,
            start_time=time.time(),
            path=path,
            status="IN_PROGRESS"
        )
        self._active_traces[req_id] = trace
        logger.info(f"[{req_id}]{f'[{workflow_id}]' if workflow_id else ''} Started trace (path: {path.value})")
        return trace

    def get_trace(self, request_id: str) -> Optional[RequestTrace]:
        """Retrieves an active or completed trace."""
        return self._active_traces.get(request_id)

    def record_model_call(self, request_id: str, count: int = 1) -> None:
        """Increments the model call counter for a request."""
        trace = self._active_traces.get(request_id)
        if trace:
            trace.model_calls += count

    def record_tool_call(self, request_id: str, count: int = 1) -> None:
        """Increments the tool call counter for a request."""
        trace = self._active_traces.get(request_id)
        if trace:
            trace.tool_calls += count

    def record_cache_hit(self, request_id: str, count: int = 1) -> None:
        """Increments the cache hit counter for a request."""
        trace = self._active_traces.get(request_id)
        if trace:
            trace.cache_hits += count

    def record_error(self, request_id: str, error_type: str, message: str, stage: str = "UNKNOWN") -> None:
        """Records a correlation-tracked error."""
        trace = self._active_traces.get(request_id)
        safe_msg = global_secret_scanner.redact_secrets(message)
        err_entry = {
            "stage": stage,
            "type": error_type,
            "message": safe_msg,
            "timestamp": time.time()
        }
        if trace:
            trace.errors.append(err_entry)
        logger.error(f"[{request_id}] Error in stage '{stage}': [{error_type}] {safe_msg}")

    @contextmanager
    def trace_stage(
        self,
        request_id: str,
        stage_name: str,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Generator[StageTrace, None, None]:
        """Context manager to measure and record execution latency of a pipeline stage."""
        trace = self._active_traces.get(request_id)
        st_trace = StageTrace(
            stage=stage_name,
            started_at=time.time(),
            model=model,
            metadata=metadata or {}
        )
        t0 = time.perf_counter()
        try:
            yield st_trace
            st_trace.status = "SUCCESS"
        except Exception as ex:
            st_trace.status = "FAILED"
            self.record_error(request_id, error_type=type(ex).__name__, message=str(ex), stage=stage_name)
            raise
        finally:
            dur_ms = (time.perf_counter() - t0) * 1000.0
            st_trace.ended_at = time.time()
            st_trace.duration_ms = round(dur_ms, 2)
            if trace:
                trace.stages.append(st_trace)
            logger.info(f"[{request_id}] Stage '{stage_name}' completed in {st_trace.duration_ms}ms (status: {st_trace.status})")

    def end_trace(self, request_id: str, status: str = "COMPLETED") -> Optional[RequestTrace]:
        """Finalizes a RequestTrace and computes total latency."""
        trace = self._active_traces.get(request_id)
        if not trace:
            return None
        trace.end_time = time.time()
        trace.total_ms = round((trace.end_time - trace.start_time) * 1000.0, 2)
        trace.status = status
        logger.info(
            f"[{request_id}]{f'[{trace.workflow_id}]' if trace.workflow_id else ''} "
            f"Trace ended ({status}) in {trace.total_ms}ms | Model calls: {trace.model_calls} | "
            f"Tool calls: {trace.tool_calls} | Cache hits: {trace.cache_hits}"
        )
        return trace


global_request_tracer = RequestTracer()
