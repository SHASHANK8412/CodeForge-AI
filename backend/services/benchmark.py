"""
AIForge Benchmark Tracker Service (Day 43)
=========================================
Tracks model response times, token usage, success/error rates, win percentages, and quality scores, storing metrics persistently in backend/data/model_metrics.json.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.services.benchmark")


class BenchmarkTracker:
    """
    Service responsible for benchmarking multi-model execution and maintaining model performance metrics.
    """

    def __init__(self, metrics_file: Optional[Path] = None):
        _root = Path(__file__).resolve().parent.parent.parent
        self.metrics_file = metrics_file or (_root / "backend" / "data" / "model_metrics.json")
        self._ensure_metrics_file()

    def _ensure_metrics_file(self):
        try:
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.metrics_file.exists():
                default_data = {
                    "qwen2.5-coder": {"model": "qwen2.5-coder", "avg_latency": 2.1, "wins": 150, "quality": 95.0, "errors": 2, "total_tokens": 120000, "total_runs": 155},
                    "deepseek-coder": {"model": "deepseek-coder", "avg_latency": 2.4, "wins": 140, "quality": 94.5, "errors": 3, "total_tokens": 135000, "total_runs": 150},
                    "codellama": {"model": "codellama", "avg_latency": 2.8, "wins": 95, "quality": 91.0, "errors": 4, "total_tokens": 110000, "total_runs": 115}
                }
                self.metrics_file.write_text(json.dumps(default_data, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.error(f"BenchmarkTracker: Failed to initialize metrics file: {e}")

    def load_metrics(self) -> Dict[str, Dict[str, Any]]:
        try:
            if self.metrics_file.exists():
                content = self.metrics_file.read_text(encoding="utf-8")
                return json.loads(content) if content.strip() else {}
        except Exception as e:
            _logger.error(f"BenchmarkTracker: Error reading metrics file: {e}")
        return {}

    def save_metrics(self, data: Dict[str, Dict[str, Any]]) -> None:
        try:
            self.metrics_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.error(f"BenchmarkTracker: Error saving metrics file: {e}")

    def record_run(
        self,
        model_name: str,
        latency: float,
        tokens_used: int,
        quality_score: float,
        is_winner: bool = False,
        is_error: bool = False
    ) -> Dict[str, Any]:
        """
        Updates benchmark statistics after a model execution attempt.
        """
        metrics = self.load_metrics()

        if model_name not in metrics:
            metrics[model_name] = {
                "model": model_name,
                "avg_latency": round(latency, 2),
                "wins": 0,
                "quality": round(quality_score, 1),
                "errors": 0,
                "total_tokens": 0,
                "total_runs": 0
            }

        rec = metrics[model_name]
        rec["total_runs"] += 1
        rec["total_tokens"] += tokens_used

        # Running average latency
        prev_latency = rec["avg_latency"]
        rec["avg_latency"] = round(((prev_latency * (rec["total_runs"] - 1)) + latency) / rec["total_runs"], 2)

        # Running average quality
        prev_quality = rec["quality"]
        rec["quality"] = round(((prev_quality * (rec["total_runs"] - 1)) + quality_score) / rec["total_runs"], 1)

        if is_winner:
            rec["wins"] += 1

        if is_error:
            rec["errors"] += 1

        self.save_metrics(metrics)
        return rec

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Generates benchmark summary statistics for the UI dashboard.
        """
        metrics = self.load_metrics()

        total_runs = sum(m.get("total_runs", 0) for m in metrics.values())
        total_wins = sum(m.get("wins", 0) for m in metrics.values())
        total_tokens = sum(m.get("total_tokens", 0) for m in metrics.values())
        total_errors = sum(m.get("errors", 0) for m in metrics.values())

        model_stats = []
        for name, m in metrics.items():
            win_pct = round((m.get("wins", 0) / max(1, total_wins)) * 100, 1)
            err_pct = round((m.get("errors", 0) / max(1, m.get("total_runs", 1))) * 100, 1)
            model_stats.append({
                "model": name,
                "avg_latency": m.get("avg_latency", 2.0),
                "wins": m.get("wins", 0),
                "win_percentage": win_pct,
                "quality_score": m.get("quality", 90.0),
                "errors": m.get("errors", 0),
                "error_rate": err_pct,
                "total_tokens": m.get("total_tokens", 0)
            })

        return {
            "total_runs": total_runs,
            "total_tokens_consumed": total_tokens,
            "overall_success_rate": round(100.0 - ((total_errors / max(1, total_runs)) * 100), 1),
            "model_statistics": model_stats
        }


global_benchmark_tracker = BenchmarkTracker()
