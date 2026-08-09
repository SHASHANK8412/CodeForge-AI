"""
AIForge Quality Recovery Day 14 — Performance Profiler & Regression Diagnostics
================================================================================
Aggregates RequestTrace statistics, calculates latency percentiles (P50, P90, P95),
identifies slowest stages, and compares before/after benchmark baselines.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.performance.models import RequestTrace

logger = logging.getLogger("aiforge.performance.profiler")


class PerformanceProfiler:
    """Aggregates latency traces and generates empirical performance reports."""

    def analyze_traces(self, traces: List[RequestTrace]) -> Dict[str, Any]:
        """Analyzes a list of RequestTrace items and computes latency statistics."""
        if not traces:
            return {"count": 0, "p50_ms": 0.0, "p95_ms": 0.0, "stage_breakdown": {}}

        latencies = sorted([t.total_ms for t in traces])
        count = len(latencies)

        p50 = latencies[int(count * 0.50)]
        p95 = latencies[min(int(count * 0.95), count - 1)]
        mean = sum(latencies) / count

        # Stage-level aggregation
        stage_durations: Dict[str, List[float]] = {}
        for t in traces:
            for st in t.stages:
                if st.stage not in stage_durations:
                    stage_durations[st.stage] = []
                stage_durations[st.stage].append(st.duration_ms)

        stage_summary = {}
        for st_name, durs in stage_durations.items():
            st_durs = sorted(durs)
            st_count = len(st_durs)
            stage_summary[st_name] = {
                "count": st_count,
                "p50_ms": st_durs[int(st_count * 0.50)],
                "p95_ms": st_durs[min(int(st_count * 0.95), st_count - 1)],
                "mean_ms": round(sum(st_durs) / st_count, 2)
            }

        return {
            "count": count,
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "mean_ms": round(mean, 2),
            "min_ms": round(latencies[0], 2),
            "max_ms": round(latencies[-1], 2),
            "stage_breakdown": stage_summary
        }

    def compare_baselines(
        self,
        baseline: Dict[str, Any],
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compares baseline vs current performance data."""
        b_p50 = baseline.get("p50_ms", 0.0)
        c_p50 = current.get("p50_ms", 0.0)

        diff_p50 = round(c_p50 - b_p50, 2)
        pct_change = round(((c_p50 - b_p50) / b_p50) * 100.0, 2) if b_p50 > 0 else 0.0

        return {
            "baseline_p50_ms": b_p50,
            "current_p50_ms": c_p50,
            "difference_ms": diff_p50,
            "percent_change": pct_change,
            "improvement": diff_p50 < 0
        }


global_performance_profiler = PerformanceProfiler()
