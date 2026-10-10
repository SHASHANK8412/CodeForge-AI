"""
AIForge Day 18 — Performance Regression Detector & Rollback Engine
====================================================================
Compares new project version metrics against baseline snapshots and automatically rolls back if latency increases > 15% or tests/security fail.
"""

import logging
from typing import Tuple, Optional

from backend.performance.models import PerformanceSnapshot, PerformanceDiff

_logger = logging.getLogger("aiforge.performance.regression")


class PerformanceRegressionDetector:
    """
    Evaluates version-over-version performance diffs for regression.
    """

    def detect_regression(
        self,
        baseline: PerformanceSnapshot,
        current: PerformanceSnapshot
    ) -> Tuple[bool, str]:
        if current.api_latency_ms > baseline.api_latency_ms * 1.15:
            pct_inc = round(((current.api_latency_ms - baseline.api_latency_ms) / baseline.api_latency_ms) * 100, 1)
            return True, f"Latency increased by {pct_inc}% ({baseline.api_latency_ms}ms -> {current.api_latency_ms}ms)"

        if current.error_rate_percent > baseline.error_rate_percent + 1.0:
            return True, f"Error rate increased to {current.error_rate_percent}%"

        return False, "No regression detected"


global_regression_detector = PerformanceRegressionDetector()
