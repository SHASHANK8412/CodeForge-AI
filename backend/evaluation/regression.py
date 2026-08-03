"""
AIForge Regression & Improvement Analyzer
=========================================
Compares current evaluation benchmark results against saved baseline data to detect:
1. Routing, Agent, or Profile Regressions
2. Quality Score Regressions
3. Critical Test Failures (e.g. Formula 1, Ambiguous Java, etc.)
4. Performance / Latency Degradation (>25%)
5. Quality Improvements across prompts and categories
"""

from typing import Dict, Any, Optional
from backend.evaluation.models import BenchmarkReport, RegressionReport


class RegressionAnalyzer:
    """
    Analyzes current vs baseline benchmark reports to detect regressions and improvements.
    """

    def compare(self, current: BenchmarkReport, baseline: BenchmarkReport) -> RegressionReport:
        quality_delta = round(current.average_quality_score - baseline.average_quality_score, 2)
        routing_delta = round(current.routing_accuracy_pct - baseline.routing_accuracy_pct, 2)
        pass_rate_delta = round(current.overall_pass_rate_pct - baseline.overall_pass_rate_pct, 2)
        latency_delta = round(current.avg_latency_ms - baseline.avg_latency_ms, 2)

        regressions = []
        improvements = []
        has_critical = False

        # 1. Critical Tests Check
        if current.critical_tests_passed < baseline.critical_tests_passed:
            has_critical = True
            regressions.append({
                "type": "CRITICAL_TEST_FAILURE",
                "message": f"Critical tests passed dropped from {baseline.critical_tests_passed} to {current.critical_tests_passed}"
            })

        # Check individual test regressions
        baseline_results_map = {r.test_id: r for r in baseline.results}
        for curr_r in current.results:
            base_r = baseline_results_map.get(curr_r.test_id)
            if base_r:
                if base_r.overall_pass and not curr_r.overall_pass:
                    reg_item = {
                        "test_id": curr_r.test_id,
                        "prompt": curr_r.prompt,
                        "baseline_score": base_r.quality_score,
                        "current_score": curr_r.quality_score,
                        "issues": curr_r.issues,
                        "critical": curr_r.critical
                    }
                    regressions.append(reg_item)
                    if curr_r.critical:
                        has_critical = True

                elif curr_r.quality_score < (base_r.quality_score - 10.0):
                    regressions.append({
                        "test_id": curr_r.test_id,
                        "prompt": curr_r.prompt,
                        "baseline_score": base_r.quality_score,
                        "current_score": curr_r.quality_score,
                        "delta": round(curr_r.quality_score - base_r.quality_score, 2)
                    })

                elif curr_r.quality_score > (base_r.quality_score + 5.0):
                    improvements.append({
                        "test_id": curr_r.test_id,
                        "prompt": curr_r.prompt,
                        "baseline_score": base_r.quality_score,
                        "current_score": curr_r.quality_score,
                        "delta": round(curr_r.quality_score - base_r.quality_score, 2)
                    })

        # Aggregate regressions
        if quality_delta < -3.0:
            regressions.append({
                "type": "GLOBAL_QUALITY_REGRESSION",
                "message": f"Average quality score decreased by {abs(quality_delta):.2f} points"
            })
        if routing_delta < -1.0:
            regressions.append({
                "type": "ROUTING_ACCURACY_REGRESSION",
                "message": f"Routing accuracy decreased by {abs(routing_delta):.2f}%"
            })
        if baseline.avg_latency_ms > 0 and latency_delta > (baseline.avg_latency_ms * 0.25):
            regressions.append({
                "type": "LATENCY_PERFORMANCE_REGRESSION",
                "message": f"Average latency increased by {latency_delta:.1f}ms (>25% slowdown)"
            })

        has_regression = len(regressions) > 0 or has_critical

        if has_critical:
            summary = "❌ CRITICAL REGRESSION DETECTED: One or more critical golden tests failed!"
        elif has_regression:
            summary = f"⚠️ REGRESSION DETECTED: {len(regressions)} regression items found."
        else:
            summary = "✅ NO REGRESSION DETECTED: Quality and routing metrics match or exceed baseline."

        return RegressionReport(
            has_regression=has_regression,
            has_critical_regression=has_critical,
            quality_delta=quality_delta,
            routing_accuracy_delta=routing_delta,
            pass_rate_delta=pass_rate_delta,
            latency_delta_ms=latency_delta,
            regressions_list=regressions,
            improvements_list=improvements,
            summary_message=summary
        )


global_regression_analyzer = RegressionAnalyzer()
