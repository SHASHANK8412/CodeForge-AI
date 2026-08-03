"""
AIForge Performance Evaluator
=============================
Calculates latency statistics: Average, P50, P95, and category breakdown.
"""

from typing import List, Dict, Any


class PerformanceEvaluator:
    """
    Evaluator for latency performance metrics.
    """

    def calculate_metrics(self, latencies_ms: List[float]) -> Dict[str, float]:
        if not latencies_ms:
            return {"avg_latency_ms": 0.0, "p50_latency_ms": 0.0, "p95_latency_ms": 0.0}

        sorted_lat = sorted(latencies_ms)
        n = len(sorted_lat)

        avg_lat = sum(sorted_lat) / n
        p50_idx = int(n * 0.50)
        p95_idx = min(n - 1, int(n * 0.95))

        return {
            "avg_latency_ms": round(avg_lat, 2),
            "p50_latency_ms": round(sorted_lat[p50_idx], 2),
            "p95_latency_ms": round(sorted_lat[p95_idx], 2)
        }


global_performance_evaluator = PerformanceEvaluator()
