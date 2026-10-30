"""
AIForge Day 93 Performance Analytics & Metrics Telemetry
=========================================================
Tracks and calculates platform telemetry:
Generation Time, Tokens, Retries, Errors, Success Rate %, Average Test Score, Average Review Score, Learning Score.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning.metrics")


class PerformanceAnalyticsCollector:
    """
    Performance analytics and metrics telemetry collector.
    """

    def __init__(self, memory_path: Optional[str] = None) -> None:
        if memory_path is None:
            kn_dir = Path(__file__).resolve().parent.parent / "knowledge"
            kn_dir.mkdir(parents=True, exist_ok=True)
            memory_path = str(kn_dir / "project_memory.json")
        self.memory_file = Path(memory_path)

    def _load_projects(self) -> List[Dict[str, Any]]:
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """Averages over the values the project memory actually recorded; None where nothing was recorded."""
        projects = self._load_projects()

        def avg(key: str, ndigits: int = 1) -> Optional[float]:
            vals = [p[key] for p in projects if isinstance(p.get(key), (int, float)) and not isinstance(p.get(key), bool)]
            return round(sum(vals) / len(vals), ndigits) if vals else None

        def total(key: str) -> Optional[int]:
            vals = [p[key] for p in projects if isinstance(p.get(key), int) and not isinstance(p.get(key), bool)]
            return sum(vals) if vals else None
        outcomes = [p.get("success") for p in projects if isinstance(p.get("success"), bool)]
        success_rate = round(100.0 * sum(outcomes) / len(outcomes), 1) if outcomes else None
        tokens = avg("tokens_used", 0)
        metrics = {
            "projects_generated": len(projects),
            "generation_time_sec": avg("generation_time_sec"),
            "tokens_used": int(tokens) if tokens is not None else None,
            "retries_count": total("retries"),
            "errors_count": total("errors"),
            "success_rate_pct": success_rate,
            "average_test_score": avg("tests_passed"),
            "average_review_score": avg("review_score"),
            "average_learning_score": avg("learning_score"),
        }

        def show(v, suffix=""):
            return "not recorded" if v is None else f"{v}{suffix}"
        metrics["dashboard_summary"] = {
            "Projects": metrics["projects_generated"],
            "Generation Time": show(metrics["generation_time_sec"], "s"),
            "Tokens": show(metrics["tokens_used"]),
            "Retries": show(metrics["retries_count"]),
            "Errors": show(metrics["errors_count"]),
            "Success Rate": show(metrics["success_rate_pct"], "%"),
            "Average Test Score": show(metrics["average_test_score"], "%"),
            "Average Review Score": show(metrics["average_review_score"], "%"),
        }
        return metrics


global_analytics_collector = PerformanceAnalyticsCollector()
