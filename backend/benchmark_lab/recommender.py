"""
AIForge Benchmark Lab — Evidence-Based Recommendation Engine
============================================================
Translates historical benchmark evaluation runs into actionable, evidence-backed
engineering workflow and model recommendations with explicit trade-off explanations.
"""

from typing import Dict, Any, List
from backend.benchmark_lab.models import BenchmarkRun


class BenchmarkRecommender:
    """
    Synthesizes historical benchmark evidence to recommend optimal models and workflows.
    """

    def generate_recommendations(self, historical_runs: List[BenchmarkRun]) -> List[Dict[str, Any]]:
        """
        Analyzes completed historical runs and produces scenario-specific recommendations.
        """
        if not historical_runs:
            return [{
                "title": "Baseline Initial Recommendation",
                "recommended_configuration": "Qwen 2.5 Coder (Planner → Coder → Reviewer)",
                "target_scenario": "General Python & Full-Stack Development",
                "sample_size": 0,
                "confidence": "Low (No prior benchmark data)",
                "evidence": "Recommended baseline for local coding evaluations pending benchmark execution.",
                "trade_offs": "Balance between generation speed and error detection.",
                "cited_runs": [],
                "approval_required": True
            }]

        completed_runs = [r for r in historical_runs if r.status == "COMPLETED" and r.results]
        if not completed_runs:
            return [{
                "title": "Incomplete Benchmark Data",
                "recommended_configuration": "Qwen 2.5 Coder (Planner → Coder)",
                "target_scenario": "Software Engineering Workflows",
                "sample_size": len(historical_runs),
                "confidence": "Low (Runs incomplete or failed)",
                "evidence": "Runs are pending completion. Rerun benchmark suite to establish statistical evidence.",
                "trade_offs": "Awaiting deterministic validation results.",
                "cited_runs": [r.id for r in historical_runs[:3]],
                "approval_required": True
            }]

        # Aggregate task results across all completed runs
        config_stats: Dict[str, Dict[str, Any]] = {}
        cited_run_ids = [r.id for r in completed_runs]

        for run in completed_runs:
            for res in run.results:
                cid = res.config_id
                if cid not in config_stats:
                    config_stats[cid] = {
                        "count": 0,
                        "tests_passed": 0,
                        "tests_total": 0,
                        "durations": [],
                        "correctness": [],
                        "repairs": 0
                    }
                s = config_stats[cid]
                s["count"] += 1
                s["tests_passed"] += res.metrics.tests_passed
                s["tests_total"] += res.metrics.tests_total
                s["durations"].append(res.metrics.duration_seconds)
                s["correctness"].append(res.metrics.functional_correctness)
                s["repairs"] += res.metrics.repair_attempts

        recommendations: List[Dict[str, Any]] = []

        # Find best for Correctness and best for Speed
        best_correctness_cid = None
        highest_correctness = -1.0

        fastest_cid = None
        lowest_duration = 999999.0

        for cid, stats in config_stats.items():
            if stats["count"] == 0:
                continue
            avg_corr = sum(stats["correctness"]) / stats["count"]
            avg_dur = sum(stats["durations"]) / stats["count"]

            if avg_corr > highest_correctness:
                highest_correctness = avg_corr
                best_correctness_cid = cid

            if avg_dur < lowest_duration:
                lowest_duration = avg_dur
                fastest_cid = cid

        if best_correctness_cid:
            b_stats = config_stats[best_correctness_cid]
            b_samples = b_stats["count"]
            avg_dur = round(sum(b_stats["durations"]) / b_samples, 1)
            pass_rate = round(
                (b_stats["tests_passed"] / b_stats["tests_total"] * 100.0)
                if b_stats["tests_total"] > 0 else highest_correctness,
                1
            )

            recommendations.append({
                "title": "Optimal Configuration for Mission-Critical Engineering",
                "recommended_configuration": best_correctness_cid,
                "target_scenario": "Complex API Generation & Production Architecture",
                "sample_size": b_samples,
                "confidence": "High" if b_samples >= 5 else "Moderate",
                "evidence": (
                    f"Observed functional test pass rate of {pass_rate}% with an average correctness score of {round(highest_correctness, 1)}% across {b_samples} evaluated task runs."
                ),
                "trade_offs": (
                    f"Requires average execution duration of {avg_dur}s per task. "
                    f"Prioritizes correctness and verification over minimum latency."
                ),
                "cited_runs": cited_run_ids[:5],
                "approval_required": True
            })

        if fastest_cid and fastest_cid != best_correctness_cid:
            f_stats = config_stats[fastest_cid]
            f_samples = f_stats["count"]
            avg_dur = round(lowest_duration, 1)
            avg_corr = round(sum(f_stats["correctness"]) / f_samples, 1)

            recommendations.append({
                "title": "Optimal Configuration for Rapid Prototyping & Iteration",
                "recommended_configuration": fastest_cid,
                "target_scenario": "Fast Iteration & Interactive Developer Assistance",
                "sample_size": f_samples,
                "confidence": "High" if f_samples >= 5 else "Moderate",
                "evidence": (
                    f"Delivers fastest observed execution duration averaging {avg_dur}s with {avg_corr}% baseline correctness."
                ),
                "trade_offs": (
                    f"Faster execution by omitting multi-agent review stages. May require follow-up repair for intricate edge cases."
                ),
                "cited_runs": cited_run_ids[:5],
                "approval_required": True
            })

        return recommendations


global_benchmark_recommender = BenchmarkRecommender()
