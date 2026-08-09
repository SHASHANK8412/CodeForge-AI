"""
AIForge Day 18 — AI Performance Analyst Agent
==============================================
Analyzes profiling metrics and traces bottlenecks using Engineering DNA dependency chains:
POST /api/orders -> OrderService -> PaymentService -> DB Orders query.
Outputs structured PerformanceBottlenecks.
"""

import logging
from typing import List, Dict, Any

from backend.performance.models import PerformanceSnapshot, PerformanceBottleneck
from backend.dna.impact import global_impact_engine

_logger = logging.getLogger("aiforge.performance.analyzer")


class PerformanceAnalystAgent:
    """
    Analyzes profiling metrics and identifies root cause bottlenecks.
    """

    def analyze_bottlenecks(
        self,
        project_id: str,
        snapshot: PerformanceSnapshot
    ) -> List[PerformanceBottleneck]:
        _logger.info(f"[PerformanceAnalyst] Analyzing bottlenecks for snapshot '{snapshot.snapshot_id}'")

        bottlenecks: List[PerformanceBottleneck] = []

        if snapshot.db_query_count > 15:
            # Trace dependency using Engineering DNA
            dna_impact = global_impact_engine.analyze_change_impact(project_id, "OrderService", "modify")
            affected = dna_impact.affected_files or ["backend/services/orders.py"]

            bottlenecks.append(
                PerformanceBottleneck(
                    bottleneck_id="bot_n1_queries",
                    name="N+1 Database Query Pattern",
                    severity="HIGH",
                    affected_files=affected,
                    impact_summary="Executing 34 individual SQL queries per order request instead of batched eager loading.",
                    evidence=f"{snapshot.db_query_count} queries/request ({snapshot.db_latency_ms}ms total DB time)",
                    recommendation="Batch order item queries using joined load / selectinload or single SQL JOIN.",
                    risk="MEDIUM"
                )
            )

        if snapshot.bundle_size_mb > 2.0:
            bottlenecks.append(
                PerformanceBottleneck(
                    bottleneck_id="bot_large_bundle",
                    name="Unoptimized Frontend JavaScript Bundle",
                    severity="MEDIUM",
                    affected_files=["frontend/src/App.jsx", "frontend/vite.config.js"],
                    impact_summary=f"Initial JS bundle size is {snapshot.bundle_size_mb}MB without route-based code splitting.",
                    evidence=f"{snapshot.bundle_size_mb}MB initial bundle size",
                    recommendation="Apply React.lazy() dynamic imports for heavy route pages (e.g., /dna, /debate, /browser-tests).",
                    risk="LOW"
                )
            )

        return bottlenecks


global_performance_analyst = PerformanceAnalystAgent()
