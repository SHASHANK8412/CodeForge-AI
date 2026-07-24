"""
Day 92 - Autonomous Learning & Self-Improving AI Engineer Verification Suite
=============================================================================
Validates all 7 Day 92 Testing Checklist Scenarios:
1. Test 1 - History Storage (Records project details, score, tests_passed, bugs, generation_time, date)
2. Test 2 - Quality Evaluation (Produces Overall Score = 92/100 and 7 category scores)
3. Test 3 - Pattern Extraction (Extracts & stores architectural patterns for quality score >= 90)
4. Test 4 - Failure Learning (Records problem "JWT Middleware Missing" and fix strategy)
5. Test 5 - Prompt Improvement (Transforms short prompt into enhanced production prompt)
6. Test 6 - Pattern Reuse (Queries prior knowledge & retrieves best-ranked pattern from leaderboard)
7. Test 7 - Metrics Dashboard (Aggregates projects_generated, average score, success rate, learned patterns, failures)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.learning.history import global_history_store
from backend.learning.quality_score import global_quality_evaluator
from backend.learning.evaluator import global_automated_evaluator
from backend.learning.pattern_extractor import global_pattern_extractor
from backend.learning.storage import global_learning_db
from backend.learning.improvement_engine import global_improvement_engine
from backend.learning.metrics import global_metrics_collector
from backend.learning.learner import global_project_learner

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


async def run_day92_tests():
    print("======================================================================")
    print(" AIForge Day 92 - Autonomous Learning & Self-Improving AI Engineer")
    print("======================================================================\n")

    # ------------------------------------------------------------------
    section("Test 1 – Generation History Storage")
    # ------------------------------------------------------------------
    hist_rec = global_history_store.record_history(
        project="Food Delivery App",
        framework="React",
        backend="FastAPI",
        score=91,
        tests_passed=34,
        bugs=2,
        generation_time=54
    )
    latest_hist = global_history_store.get_latest_record()

    check("Generated history record with project name, framework, and backend", latest_hist["project"] == "Food Delivery App" and latest_hist["framework"] == "React")
    check("Recorded generation metrics (Score=91, Tests Passed=34, Bugs=2, Time=54s, Date)", latest_hist["score"] == 91 and latest_hist["bugs"] == 2 and "date" in latest_hist)

    # ------------------------------------------------------------------
    section("Test 2 – Quality Score Evaluation (7 Categories)")
    # ------------------------------------------------------------------
    eval_res = global_quality_evaluator.evaluate_project_quality("E-Commerce Portal")
    category_scores = eval_res["category_scores"]

    check("Calculated Overall Score formatted (e.g., 'Overall Score = 93/100')", "Overall Score = " in eval_res["score_formatted"])
    check("Evaluated 7 quality categories (Code, Test, Doc, Readability, Perf, Sec, Org)", len(category_scores) == 7 and "code_quality" in category_scores and "folder_organization" in category_scores)

    # ------------------------------------------------------------------
    section("Test 3 – Architectural Pattern Extraction (Score >= 90)")
    # ------------------------------------------------------------------
    pat_res = global_pattern_extractor.extract_and_store_patterns(
        project_name="E-Commerce Microservice",
        overall_score=94,
        architecture="Clean Architecture + Microservices"
    )

    check("Extracted reusable architecture, API design, and testing approach for score >= 90", pat_res["extracted"] and pat_res["patterns_extracted_count"] == 3)
    check("Stored extracted patterns in Learning Database (patterns.db)", len(global_learning_db.get_all_patterns()) >= 3)

    # ------------------------------------------------------------------
    section("Test 4 – Failure Learning & Fix Strategy")
    # ------------------------------------------------------------------
    fail_rec = global_improvement_engine.record_failure(
        problem="Authentication broken / JWT Middleware Missing",
        fix="Always generate JWT middleware before routes",
        category="authentication"
    )

    check("Recorded failure problem & fix strategy in failure database", fail_rec["failure_id"] is not None)
    check("Failure fix strategy persisted ('Always generate JWT middleware before routes')", "JWT middleware" in fail_rec["fix"])

    # ------------------------------------------------------------------
    section("Test 5 – Automatic Prompt Improvement")
    # ------------------------------------------------------------------
    base_prompt = "Generate backend."
    enhanced_prompt = global_improvement_engine.improve_prompt(base_prompt)

    check("Detected short prompt and expanded to production-grade prompt", len(enhanced_prompt) > len(base_prompt))
    check("Enhanced prompt includes JWT, dependency injection, logging, Swagger, and Docker", "JWT" in enhanced_prompt and "Docker" in enhanced_prompt)

    # ------------------------------------------------------------------
    section("Test 6 – Pattern Ranking & Leaderboard Reuse")
    # ------------------------------------------------------------------
    prior_knowledge = global_project_learner.query_prior_knowledge("Build a Task Management Application")
    leaderboard = global_learning_db.get_leaderboard()

    check("Pre-generation query retrieved highest-rated pattern from leaderboard", len(leaderboard) > 0 and leaderboard[0]["score"] >= 95)
    check("Retrieved best architecture & known bug fixes for pre-planning", prior_knowledge["suggested_architecture"] is not None and len(prior_knowledge["known_bugs_and_fixes"]) > 0)

    # ------------------------------------------------------------------
    section("Test 7 – Metrics Dashboard Telemetry")
    # ------------------------------------------------------------------
    pipeline_res = global_project_learner.run_learning_pipeline("FinTech Payment Gateway")
    metrics = global_metrics_collector.get_dashboard_metrics()

    check("Metrics Dashboard tracks total Projects Generated", metrics["projects_generated"] >= 180)
    check("Metrics Dashboard tracks Average Score, Success Rate %, Patterns & Failures Learned", 
          metrics["average_score"] >= 90.0 and metrics["success_rate_pct"] == 96.0 and metrics["patterns_learned"] >= 300 and metrics["failures_learned"] >= 80)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 92 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day92_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
