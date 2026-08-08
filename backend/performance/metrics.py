"""
AIForge Quality Recovery Day 14 — Metrics Service & Latency Histograms
======================================================================
Provides MetricsService tracking quantitative counters, latency histograms,
and Time To First Token (TTFT).
"""

import time
import math
import threading
from typing import Dict, Any, List
import logging

logger = logging.getLogger("aiforge.performance.metrics")


class MetricsService:
    """Centralized metrics collection service."""

    def __init__(self):
        self._lock = threading.Lock()
        self.counters = {
            "requests_total": 0,
            "requests_failed": 0,
            "model_calls": 0,
            "tool_calls": 0,
            "cache_hits": 0,
            "retries": 0,
            "circuit_breaker_opens": 0,
            "security_blocks": 0,
        }
        self.latencies: Dict[str, List[float]] = {
            "request_total": [],
            "llm_generation": [],
            "rag_search": [],
            "rerank": [],
            "execution": [],
            "ttft": [],
        }

    def increment(self, counter_name: str, value: int = 1) -> None:
        with self._lock:
            if counter_name in self.counters:
                self.counters[counter_name] += value
            else:
                self.counters[counter_name] = value

    def observe_latency(self, metric_name: str, latency_ms: float) -> None:
        with self._lock:
            if metric_name not in self.latencies:
                self.latencies[metric_name] = []
            self.latencies[metric_name].append(latency_ms)

    def calculate_percentiles(self, metric_name: str) -> Dict[str, float]:
        with self._lock:
            vals = sorted(self.latencies.get(metric_name, []))
        if not vals:
            return {"count": 0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "mean": 0.0}

        count = len(vals)
        p50 = vals[int(count * 0.50)]
        p90 = vals[min(int(count * 0.90), count - 1)]
        p95 = vals[min(int(count * 0.95), count - 1)]
        mean = sum(vals) / count

        return {
            "count": count,
            "p50": round(p50, 2),
            "p90": round(p90, 2),
            "p95": round(p95, 2),
            "mean": round(mean, 2)
        }

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            c_copy = dict(self.counters)
        metrics_summary = {"counters": c_copy, "latencies": {}}
        for k in self.latencies:
            metrics_summary["latencies"][k] = self.calculate_percentiles(k)
        return metrics_summary


global_metrics_service = MetricsService()
