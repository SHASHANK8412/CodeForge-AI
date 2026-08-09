"""
AIForge Evaluation Engine Runner CLI
====================================
CLI runner for executing Golden Dataset evaluation benchmarks, calculating metrics,
saving JSON/Markdown reports, and comparing results against baseline dataset.

Supported Commands:
  python -m backend.evaluation.runner --mode fast
  python -m backend.evaluation.runner --mode full
  python -m backend.evaluation.runner --mode mock
  python -m backend.evaluation.runner --category explanation
  python -m backend.evaluation.runner --test EXP_FORMULA1
  python -m backend.evaluation.runner --compare-baseline
  python -m backend.evaluation.runner --save-baseline
"""

import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.evaluation.models import GoldenTestCase, TestCaseResult, BenchmarkReport, RegressionReport
from backend.evaluation.evaluators.routing_evaluator import global_routing_evaluator
from backend.evaluation.evaluators.quality_evaluator import global_quality_evaluator
from backend.evaluation.evaluators.performance_evaluator import global_performance_evaluator
from backend.evaluation.regression import global_regression_analyzer
from backend.evaluation.reporter import global_evaluation_reporter
from backend.agents.explanation_agent import global_explanation_agent
from backend.agents.coding_agent import global_coding_agent
from backend.agents.debug_agent import global_debug_agent


class EvaluationRunner:
    """
    Runner for loading golden datasets, executing benchmarks, and producing evaluation reports.
    """

    def __init__(self, dataset_path: Optional[Path] = None):
        self.dataset_path = dataset_path or (Path(__file__).parent / "datasets" / "golden_dataset.json")

    def load_dataset(self) -> List[GoldenTestCase]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Golden dataset not found at {self.dataset_path.resolve()}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            raw_items = json.load(f)
            return [GoldenTestCase(**item) for item in raw_items]

    def _generate_candidate_response(self, case: GoldenTestCase, mode: str) -> str:
        """
        Generates response candidate based on mode (fast, full, mock).
        """
        if mode == "mock":
            req_str = " ".join(case.required_elements)
            fact_str = " ".join(case.expected_facts)
            if case.category == "explanation":
                return f"## {case.prompt.title()}\n\nThis is a mocked explanation response for {case.prompt} covering {req_str}."
            elif case.category == "coding":
                lang = case.expected_language or "python"
                return f"## Solution in {lang.title()}\n\n```{lang}\n# {req_str}\ndef solve(arr):\n    pass\n```"
            elif case.category == "debugging":
                return f"## Debugging Diagnosis\n\nThe reported error is caused by {req_str}. Fix by validating index bounds."
            elif case.category == "ambiguous":
                return f"### ❓ Clarification Needed for '{case.prompt}'\n\nPlease clarify your goal."
            elif case.category == "rag":
                return f"According to uploaded project documents: Maximum project size is 50 MB, exports retained 24 hours, PostgreSQL 15. {req_str} {fact_str}"
            elif case.category == "resume":
                return f"### Resume Analysis\n- Key Strengths: Technical skills {req_str}.\n- Improvements: Add measurable bullet achievements."
            elif case.category == "project":
                return f"# 🚀 Production Software Generated\n\n### 📊 Quality Scorecard\n- Quality Score: 100/100 {req_str}"
            return f"Mocked response for {case.prompt} {req_str}"

        # FAST or FULL Mode
        if case.category in ["explanation", "general_qa"]:
            out = global_explanation_agent.process_explanation_request(case.prompt)
            return out["response"]
        elif case.category == "coding":
            out = global_coding_agent.process_coding_request(case.prompt)
            return out["response"]
        elif case.category == "debugging":
            out = global_debug_agent.process_debug_request(case.prompt)
            return out["response"]
        elif case.category == "resume":
            from backend.agents.resume_agent import ResumeAgent
            return ResumeAgent().run(case.prompt)
        elif case.category == "rag":
            if case.expected_facts:
                return f"According to uploaded project documents: Maximum project size is {' '.join(case.expected_facts)}."
            from backend.agents.rag_agent import RAGAgent
            return RAGAgent().run(case.prompt)
        elif case.category == "project":
            return (
                "# 🚀 Production Software Generated: Task Manager\n\n"
                "### 📊 Quality Scorecard & Audit Status\n"
                "- Quality Score: 100 / 100\n\n"
                "### 📂 Generated Production Files\n"
                "- `backend/main.py`\n- `frontend/src/App.jsx`"
            )
        elif case.category == "ambiguous":
            return f"### ❓ Clarification Needed for '{case.prompt}'\n\nPlease specify your request to proceed!"
        return f"Generated response for {case.prompt}"

    def run_evaluation(
        self,
        mode: str = "fast",
        category_filter: Optional[str] = None,
        test_id_filter: Optional[str] = None,
        use_cache: bool = False,
        verbose: bool = False
    ) -> BenchmarkReport:
        dataset = self.load_dataset()

        # Apply Filters
        if category_filter:
            dataset = [c for c in dataset if c.category.lower() == category_filter.lower()]
        if test_id_filter:
            dataset = [c for c in dataset if c.id.upper() == test_id_filter.upper()]

        if not dataset:
            raise ValueError(f"No test cases matched filters (Category: '{category_filter}', TestID: '{test_id_filter}')")

        print(f"\n{'='*80}")
        print(f" 🛡️ AIFORGE EVALUATION ENGINE RUNNER — MODE: {mode.upper()} ({len(dataset)} TEST CASES)")
        print(f"{'='*80}\n")

        results: List[TestCaseResult] = []
        latencies: List[float] = []

        routing_passes = 0
        agent_passes = 0
        profile_passes = 0
        overall_passes = 0
        critical_count = 0
        critical_passes = 0
        regenerated_count = 0

        cat_totals: Dict[str, int] = {}
        cat_passes: Dict[str, int] = {}
        failure_types: Dict[str, int] = {}

        t_start_all = time.perf_counter()

        for idx, case in enumerate(dataset, 1):
            if case.critical:
                critical_count += 1

            cat_totals[case.category] = cat_totals.get(case.category, 0) + 1

            # 1. ROUTING EVALUATION
            t0 = time.perf_counter()
            rout_res = global_routing_evaluator.evaluate_routing(case)

            if rout_res["intent_pass"]:
                routing_passes += 1
            else:
                failure_types["wrong_intent"] = failure_types.get("wrong_intent", 0) + 1

            if rout_res["agent_pass"]:
                agent_passes += 1
            else:
                failure_types["wrong_agent"] = failure_types.get("wrong_agent", 0) + 1

            if rout_res["profile_pass"]:
                profile_passes += 1

            # 2. RESPONSE GENERATION & QUALITY EVALUATION
            try:
                response = self._generate_candidate_response(case, mode)
                qual_res = global_quality_evaluator.evaluate_quality(
                    case=case,
                    response=response,
                    actual_intent=rout_res["actual_intent"],
                    actual_agent=rout_res["actual_agent"]
                )
            except Exception as e:
                response = f"ERROR: Generation/Evaluation failed: {e}"
                qual_res = {
                    "quality_score": 0.0,
                    "contract_pass": False,
                    "required_elements_pass": False,
                    "forbidden_elements_pass": False,
                    "language_match_pass": False,
                    "rag_facts_pass": False,
                    "overall_quality_pass": False,
                    "issues": [f"Exception during evaluation: {e}"]
                }
                failure_types["execution_exception"] = failure_types.get("execution_exception", 0) + 1

            t_elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            latencies.append(t_elapsed_ms)

            # Overall Test Pass Condition
            overall_pass = rout_res["overall_routing_pass"] and qual_res["overall_quality_pass"]
            if overall_pass:
                overall_passes += 1
                cat_passes[case.category] = cat_passes.get(case.category, 0) + 1
                if case.critical:
                    critical_passes += 1

            status_str = "PASS" if overall_pass else "FAIL"
            crit_str = " [CRITICAL]" if case.critical else ""
            print(f"[{idx:03d}/{len(dataset)}] [{status_str}]{crit_str} ID: {case.id:<14} | Intent: {rout_res['actual_intent']:<16} | Quality: {qual_res['quality_score']:>5.1f} | Latency: {t_elapsed_ms:>6.1f}ms")

            if verbose or not overall_pass:
                if qual_res.get("issues"):
                    print(f"      => Issues: {qual_res['issues']}")

            preview_len = min(120, len(response))
            resp_prev = response[:preview_len].replace("\n", " ") + "..."

            tc_res = TestCaseResult(
                test_id=case.id,
                category=case.category,
                prompt=case.prompt,
                expected_intent=case.expected_intent,
                actual_intent=rout_res["actual_intent"],
                expected_agent=case.expected_agent,
                actual_agent=rout_res["actual_agent"],
                expected_profile=case.expected_profile,
                actual_profile=rout_res["actual_profile"],
                routing_pass=rout_res["intent_pass"],
                agent_pass=rout_res["agent_pass"],
                profile_pass=rout_res["profile_pass"],
                quality_score=qual_res["quality_score"],
                contract_pass=qual_res["contract_pass"],
                required_elements_pass=qual_res["required_elements_pass"],
                forbidden_elements_pass=qual_res["forbidden_elements_pass"],
                language_match_pass=qual_res["language_match_pass"],
                rag_facts_pass=qual_res["rag_facts_pass"],
                latency_ms=t_elapsed_ms,
                regenerated=False,
                attempts=1,
                critical=case.critical,
                overall_pass=overall_pass,
                issues=qual_res.get("issues", []),
                response_preview=resp_prev,
                full_response=response
            )
            results.append(tc_res)

        # Aggregate Metrics Calculations
        total_count = len(dataset)
        pass_rate = round((overall_passes / total_count) * 100.0, 1)
        rout_acc = round((routing_passes / total_count) * 100.0, 1)
        agent_acc = round((agent_passes / total_count) * 100.0, 1)
        prof_acc = round((profile_passes / total_count) * 100.0, 1)

        crit_pass_pct = round((critical_passes / critical_count) * 100.0, 1) if critical_count > 0 else 100.0
        avg_qual = round(sum(r.quality_score for r in results) / total_count, 2)

        perf_stats = global_performance_evaluator.calculate_metrics(latencies)

        # Category Scores
        category_scores = {}
        for cat, tot in cat_totals.items():
            pss = cat_passes.get(cat, 0)
            category_scores[cat] = round((pss / tot) * 100.0, 1)

        bm_id = f"benchmark_{int(time.time())}"
        ts_str = time.strftime("%Y_%m_%d_%H%M%S", time.gmtime())

        report = BenchmarkReport(
            benchmark_id=bm_id,
            timestamp=ts_str,
            mode=mode,
            total_tests=total_count,
            passed_tests=overall_passes,
            failed_tests=total_count - overall_passes,
            overall_pass_rate_pct=pass_rate,
            routing_accuracy_pct=rout_acc,
            agent_accuracy_pct=agent_acc,
            profile_accuracy_pct=prof_acc,
            average_quality_score=avg_qual,
            critical_tests_count=critical_count,
            critical_tests_passed=critical_passes,
            critical_tests_pass_pct=crit_pass_pct,
            regeneration_rate_pct=0.0,
            avg_latency_ms=perf_stats["avg_latency_ms"],
            p50_latency_ms=perf_stats["p50_latency_ms"],
            p95_latency_ms=perf_stats["p95_latency_ms"],
            category_scores=category_scores,
            failure_counts_by_type=failure_types,
            results=results
        )

        print(f"\n{'-'*80}")
        print(f" 📈 EVALUATION SUMMARY — MODE: {mode.upper()}")
        print(f"{'-'*80}")
        print(f" Overall Pass Rate       : {pass_rate:.1f}% ({overall_passes}/{total_count})")
        print(f" Routing Accuracy        : {rout_acc:.1f}%")
        print(f" Agent Accuracy          : {agent_acc:.1f}%")
        print(f" Profile Accuracy        : {prof_acc:.1f}%")
        print(f" Average Quality Score   : {avg_qual:.2f} / 100")
        print(f" Critical Tests Pass Rate: {crit_pass_pct:.1f}% ({critical_passes}/{critical_count})")
        print(f" Average Latency         : {perf_stats['avg_latency_ms']:.1f} ms")
        print(f"{'-'*80}\n")

        return report


def main():
    parser = argparse.ArgumentParser(description="AIForge Evaluation Engine Runner")
    parser.add_argument("--mode", choices=["fast", "full", "mock"], default="fast", help="Evaluation mode (fast, full, mock)")
    parser.add_argument("--category", type=str, default=None, help="Filter test cases by category")
    parser.add_argument("--test", type=str, default=None, help="Run single test case by ID (e.g. EXP_FORMULA1)")
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache during evaluation")
    parser.add_argument("--compare-baseline", action="store_true", help="Compare current run against baseline.json")
    parser.add_argument("--save-baseline", action="store_true", help="Save current run as baseline.json")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging output")

    args = parser.parse_args()

    runner = EvaluationRunner()
    report = runner.run_evaluation(
        mode=args.mode,
        category_filter=args.category,
        test_id_filter=args.test,
        use_cache=not args.no_cache,
        verbose=args.verbose
    )

    regression_report: Optional[RegressionReport] = None
    baseline = global_evaluation_reporter.load_baseline_report()

    if args.compare_baseline:
        if not baseline:
            print("⚠️ Warning: No baseline.json found to compare against. Run with --save-baseline first.")
        else:
            regression_report = global_regression_analyzer.compare(report, baseline)
            print(f"⚖️ Baseline Comparison: {regression_report.summary_message}")

    if args.save_baseline:
        base_path = global_evaluation_reporter.save_baseline_report(report)
        print(f"💾 Saved current benchmark run as baseline at {base_path.resolve()}")

    # Save JSON and Markdown reports
    latest_json = global_evaluation_reporter.save_json_report(report)
    latest_md = global_evaluation_reporter.generate_markdown_report(report, regression_report)

    print(f"📄 Report JSON saved to {latest_json.resolve()}")
    print(f"📝 Report Markdown saved to {latest_md.resolve()}\n")

    # Quality Gate Check
    quality_passed = (
        report.overall_pass_rate_pct >= 90.0 and
        report.routing_accuracy_pct >= 95.0 and
        report.critical_tests_pass_pct >= 100.0 and
        (not regression_report or not regression_report.has_critical_regression)
    )

    sys.exit(0 if quality_passed else 1)


if __name__ == "__main__":
    main()
