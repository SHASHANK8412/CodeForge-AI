"""
AIForge Day 18 — Benchmark System
==================================
Runs controlled local baseline benchmarks and creates versioned PerformanceSnapshot objects.
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any

from backend.performance.models import PerformanceSnapshot
from backend.performance.profiler import global_profiler

_logger = logging.getLogger("aiforge.performance.benchmark")


class BenchmarkEngine:
    """
    Executes controlled benchmarking workloads and outputs PerformanceSnapshots.
    """

    def run_benchmark(
        self,
        project_id: str,
        generation_id: str = "aiforge-demo",
        version: int = 1,
        is_optimized: bool = False
    ) -> PerformanceSnapshot:
        _logger.info(f"[BenchmarkEngine] Running benchmark for project '{project_id}' v{version}")
        metrics = global_profiler.profile(project_id, is_optimized)

        snap_id = f"snap_{secrets.token_urlsafe(6)}"
        return PerformanceSnapshot(
            snapshot_id=snap_id,
            project_id=project_id,
            generation_id=generation_id,
            version=version,
            timestamp=datetime.now().isoformat(),
            **metrics
        )


global_benchmark_engine = BenchmarkEngine()
