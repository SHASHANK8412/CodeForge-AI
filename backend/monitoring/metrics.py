"""
AIForge Metrics Collector
=========================
Process and host resource usage (psutil) plus pipeline figures derived from recorded generation
runs: LLM latency and throughput from real token usage, run success rate and active runs.
Values that are not measured (GPU) are None rather than estimated.
"""

import time
import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.monitoring.metrics")

_ACTIVE = ("queued", "planning", "running", "building")


class MetricsCollector:
    def collect_system_metrics(self) -> Dict[str, Any]:
        rss_mb = cpu_pct = mem_pct = None
        try:
            import psutil
            rss_mb = round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
            cpu_pct = psutil.cpu_percent(interval=None)
            mem_pct = psutil.virtual_memory().percent
        except Exception as e:  # noqa: BLE001 - psutil missing or restricted
            _logger.debug("psutil metrics unavailable: %s", e)

        runs = []
        try:
            from backend.generation.store import global_generation_store
            runs = global_generation_store.list_all()
        except Exception as e:  # noqa: BLE001
            _logger.debug("generation store unavailable: %s", e)

        calls = llm_seconds = completion_tokens = 0
        for run in runs:
            usage = run.get("usage") or {}
            calls += (usage.get("llm_calls", 0) or 0) - (usage.get("cached_calls", 0) or 0)
            llm_seconds += usage.get("llm_seconds", 0.0) or 0.0
            completion_tokens += usage.get("completion_tokens", 0) or 0
        finished = [r for r in runs if r.get("status") in ("completed", "failed", "cancelled")]
        succeeded = sum(1 for r in finished if r.get("status") == "completed")

        return {
            "timestamp": time.time(),
            "agent_latency_avg_ms": round(llm_seconds / calls * 1000, 1) if calls else None,
            "tokens_per_sec": round(completion_tokens / llm_seconds, 2) if llm_seconds else None,
            "memory_usage_mb": rss_mb,
            "memory_usage_pct": mem_pct,
            "cpu_utilization_pct": cpu_pct,
            "gpu_utilization_pct": None,
            "gpu_memory_used_mb": None,
            "queue_length": sum(1 for r in runs if r.get("status") == "queued"),
            "active_workflows": sum(1 for r in runs if r.get("status") in _ACTIVE),
            "success_rate_pct": round(succeeded / len(finished) * 100, 1) if finished else None,
            "failure_rate_pct": round((len(finished) - succeeded) / len(finished) * 100, 1) if finished else None,
        }


global_metrics_collector = MetricsCollector()
