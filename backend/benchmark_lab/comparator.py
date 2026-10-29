"""
AIForge Benchmark Lab — Configuration Comparison Engine
========================================================
Aggregates repeated runs, calculates run-to-run variability, ranks configurations
based on user priorities, and exposes transparent metric breakdowns.
"""

import math
from typing import Dict, Any, List, Optional
from backend.benchmark_lab.models import (
    BenchmarkRun,
    BenchmarkConfig,
    TaskRunResult,
    EvaluationPriority,
    ComparisonWeights,
)


class ConfigurationComparator:
    """
    Ranks benchmark configurations with multi-attribute decision scoring
    and computes statistical variability across repeated runs.
    """

    @staticmethod
    def _calc_std(values: List[float], mean_val: float) -> float:
        if len(values) <= 1:
            return 0.0
        variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
        return round(math.sqrt(variance), 2)

    def aggregate_and_compare(
        self,
        run: BenchmarkRun,
        weights: Optional[ComparisonWeights] = None,
        priority: Optional[EvaluationPriority] = None
    ) -> Dict[str, Any]:
        """
        Groups run results by configuration, computes mean & variance,
        applies objective weights, and ranks configurations.
        """
        prio = priority or run.priority
        active_weights = weights or run.weights or ComparisonWeights()

        # Adjust weights based on priority preset
        if prio == EvaluationPriority.MAX_CORRECTNESS:
            active_weights = ComparisonWeights(correctness=0.60, adherence=0.20, quality=0.10, reliability=0.05, speed=0.05)
        elif prio == EvaluationPriority.FASTEST_EXECUTION:
            active_weights = ComparisonWeights(correctness=0.25, adherence=0.15, quality=0.10, reliability=0.10, speed=0.40)
        elif prio == EvaluationPriority.BEST_QUALITY:
            active_weights = ComparisonWeights(correctness=0.30, adherence=0.20, quality=0.35, reliability=0.10, speed=0.05)
        elif prio == EvaluationPriority.LOWEST_RESOURCES:
            active_weights = ComparisonWeights(correctness=0.30, adherence=0.15, quality=0.15, reliability=0.10, speed=0.30)
        elif prio == EvaluationPriority.BEST_OVERALL:
            active_weights = ComparisonWeights(correctness=0.40, adherence=0.20, quality=0.15, reliability=0.15, speed=0.10)

        # Group results by configuration
        config_map: Dict[str, BenchmarkConfig] = {c.id: c for c in run.configurations}
        grouped_results: Dict[str, List[TaskRunResult]] = {}
        for res in run.results:
            if res.status == "NOT_RUN":
                continue        # nothing was validated: excluded from scores rather than counted as 0
            grouped_results.setdefault(res.config_id, []).append(res)

        config_summaries: List[Dict[str, Any]] = []

        for cid, res_list in grouped_results.items():
            cfg = config_map.get(cid)
            cfg_name = cfg.name if cfg else cid
            model_name = cfg.model_name if cfg else "Unknown"
            workflow_name = cfg.workflow.value if cfg else "Unknown"

            count = len(res_list)
            if count == 0:
                continue

            correctness_vals = [r.metrics.functional_correctness for r in res_list]
            adherence_vals = [r.metrics.requirement_adherence for r in res_list]
            quality_vals = [r.metrics.code_quality for r in res_list]
            reliability_vals = [r.metrics.reliability for r in res_list]
            duration_vals = [r.metrics.duration_seconds for r in res_list]

            mean_correctness = round(sum(correctness_vals) / count, 1)
            mean_adherence = round(sum(adherence_vals) / count, 1)
            mean_quality = round(sum(quality_vals) / count, 1)
            mean_reliability = round(sum(reliability_vals) / count, 1)
            mean_duration = round(sum(duration_vals) / count, 2)

            std_correctness = self._calc_std(correctness_vals, mean_correctness)
            std_duration = self._calc_std(duration_vals, mean_duration)

            total_tests_passed = sum(r.metrics.tests_passed for r in res_list)
            total_tests_req = sum(r.metrics.tests_total for r in res_list)
            pass_rate = round((total_tests_passed / total_tests_req) * 100.0, 1) if total_tests_req > 0 else mean_correctness

            build_successes = sum(1 for r in res_list if r.metrics.build_success)
            build_rate = round((build_successes / count) * 100.0, 1)

            total_repairs = sum(r.metrics.repair_attempts for r in res_list)
            failed_runs = sum(1 for r in res_list if r.status != "COMPLETED")

            # Normalized speed score (0 - 100, where 100 is instant and 0 is >= 60s avg)
            speed_score = max(0.0, 100.0 - (mean_duration / 60.0) * 100.0)

            composite_score = round(
                active_weights.correctness * mean_correctness +
                active_weights.adherence * mean_adherence +
                active_weights.quality * mean_quality +
                active_weights.reliability * mean_reliability +
                active_weights.speed * speed_score,
                1
            )

            config_summaries.append({
                "config_id": cid,
                "config_name": cfg_name,
                "model_name": model_name,
                "workflow": workflow_name,
                "tasks_evaluated": count,
                "failed_tasks": failed_runs,
                "test_pass_rate": pass_rate,
                "build_success_rate": build_rate,
                "mean_correctness": mean_correctness,
                "std_correctness": std_correctness,
                "mean_adherence": mean_adherence,
                "mean_quality": mean_quality,
                "mean_reliability": mean_reliability,
                "mean_duration_seconds": mean_duration,
                "std_duration": std_duration,
                "total_repairs": total_repairs,
                "composite_score": composite_score,
                "is_available": cfg.is_available if cfg else True
            })

        # Rank configurations
        config_summaries.sort(key=lambda x: x["composite_score"], reverse=True)
        for idx, item in enumerate(config_summaries, 1):
            item["rank"] = idx

        # Pairwise comparison & trade-off analysis
        trade_offs = []
        if len(config_summaries) >= 2:
            top = config_summaries[0]
            runner_up = config_summaries[1]

            diff_score = round(top["composite_score"] - runner_up["composite_score"], 1)
            diff_time = round(top["mean_duration_seconds"] - runner_up["mean_duration_seconds"], 2)
            diff_pass = round(top["test_pass_rate"] - runner_up["test_pass_rate"], 1)

            trade_offs.append({
                "comparison": f"Rank #1 ({top['config_name']}) vs Rank #2 ({runner_up['config_name']})",
                "score_delta": diff_score,
                "time_delta_seconds": diff_time,
                "pass_rate_delta": diff_pass,
                "analysis": (
                    f"'{top['config_name']}' leads by {diff_score} pts. "
                    f"Observed pass rate: {top['test_pass_rate']}% vs {runner_up['test_pass_rate']}%. "
                    f"Execution latency: {top['mean_duration_seconds']}s vs {runner_up['mean_duration_seconds']}s."
                )
            })

        return {
            "priority": prio.value if hasattr(prio, "value") else str(prio),
            "weights": active_weights.model_dump(),
            "ranked_configurations": config_summaries,
            "trade_offs": trade_offs,
            "best_configuration_id": config_summaries[0]["config_id"] if config_summaries else None
        }


global_config_comparator = ConfigurationComparator()
