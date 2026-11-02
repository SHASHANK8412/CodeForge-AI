"""
Performance facts for other AIForge modules (the readiness gate), read from the Performance
Engineer's real baseline runs. The previous implementation returned fixed numbers (420 ms before,
118 ms "optimized"); a project that was never measured now reports that it was not measured.
"""

from typing import Any, Dict, Optional


class PerformanceService:
    def latest_measurement(self, project_id: str) -> Optional[Dict[str, Any]]:
        """The latest completed baseline run of a project, summarized; None if it was never measured."""
        from backend.performance.engineer.service import global_performance_engineer
        try:
            run = global_performance_engineer.store.latest(project_id, "runs", "completed")
        except ValueError:                        # not a valid project id for the store
            return None
        if run is None or run.measurement is None or run.measurement.status != "measured":
            return None
        eps = [e for e in run.measurement.endpoints if e.median_ms is not None]
        worst = max(eps, key=lambda e: e.p95_ms or 0, default=None)
        return {
            "run_id": run.id, "finished_at": run.finished_at,
            "endpoints": len(run.measurement.endpoints),
            "worst_p95_ms": worst.p95_ms if worst else None,
            "worst_endpoint": f"{worst.method} {worst.path}" if worst else None,
            "max_error_rate_pct": max((e.error_rate_pct for e in run.measurement.endpoints), default=0.0),
            "startup_seconds": run.measurement.startup_seconds,
            "peak_memory_mb": run.measurement.resources.mem_max_mb,
        }


global_performance_service = PerformanceService()
