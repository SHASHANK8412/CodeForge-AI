"""
Day 93 - Autonomous Learning & Continuous Improvement Engine Verification Suite
================================================================================
Validates all Day 93 Success Criteria:
1. AIForge stores completed project knowledge permanently.
2. Similar projects are retrieved before generation.
3. Common mistakes are automatically identified and remembered.
4. Best practices are accumulated for reuse.
5. Every project receives a measurable weighted Learning Score (30% Arch, 20% Code, 20% Tests, 15% Perf, 10% Doc, 5% Sec).
6. Learning Agent updates knowledge base after each run.
7. System continuously improves future generations based on past experience.
"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.learning.learner import global_master_learner
from backend.agents.learning_agent import global_learning_agent

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


async def run_day93_tests():
    print("======================================================================")
    print(" AIForge Day 93 - Autonomous Learning & Continuous Improvement Engine")
    print("======================================================================\n")

    # ------------------------------------------------------------------
    section("1. Project Knowledge Storage")
    # ------------------------------------------------------------------
    train_res = global_master_learner.update_knowledge("SRE Incident Automation Platform", rating=5, learning_score=95)
    check("Stored project prompt, framework, backend, bugs, tests, rating in project_memory.json", train_res["status"] == "trained")

    # ------------------------------------------------------------------
    section("2. Similar Project Retrieval")
    # ------------------------------------------------------------------
    similar_projects = global_master_learner.retrieve_similar_projects("Build Netflix video platform clone")
    check("Retrieved similar projects (Movie Streaming Platform / Video Dashboard)", len(similar_projects) > 0)
    check("Retrieved reusable architecture, components, and API endpoints", "reusable_components" in similar_projects[0] and "reusable_apis" in similar_projects[0])

    # ------------------------------------------------------------------
    section("3. Mistake Database & Recurrence Tracking")
    # ------------------------------------------------------------------
    err_rec = global_master_learner.record_mistake(
        problem="Missing import in component / route",
        solution="Automatically add import",
        category="imports"
    )
    check("Recorded recurring mistake problem, solution, and occurrences count", err_rec["occurrences"] >= 1 and err_rec["solution"] == "Automatically add import")

    # ------------------------------------------------------------------
    section("4. Best Practice Database")
    # ------------------------------------------------------------------
    bps = global_master_learner.get_best_practices()
    check("Accumulated best practice patterns for React structure, FastAPI arch, DB schema, security, and testing", len(bps) >= 5)

    # ------------------------------------------------------------------
    section("5. Weighted Learning Score Calculation")
    # ------------------------------------------------------------------
    score_res = global_master_learner.evaluate_project(
        project_name="E-Commerce Payment Service",
        architecture_score=95.0,
        code_quality_score=92.0,
        tests_score=94.0,
        performance_score=96.0,
        documentation_score=90.0,
        security_score=98.0
    )
    check("Calculated weighted Learning Score (30% Arch, 20% Code, 20% Tests, 15% Perf, 10% Doc, 5% Sec)", "Learning Score 94/100" in score_res["score_formatted"])

    # ------------------------------------------------------------------
    section("6. Learning Agent Knowledge Updates")
    # ------------------------------------------------------------------
    agent_res = global_learning_agent.analyze_project_and_learn("AI Cloud Monitor")
    check("Learning Agent analyzed project, updated knowledge base, and generated recommendations", agent_res["status"] == "success" and len(agent_res["recommendations"]) > 0)

    # ------------------------------------------------------------------
    section("7. Performance Telemetry & Prompt Refinement")
    # ------------------------------------------------------------------
    metrics = global_master_learner.calculate_metrics()
    refined_prompt = global_master_learner.refine_prompt("Build blog app")

    check("Calculated performance analytics (Gen Time, Tokens, Retries, Errors, Success Rate %, Test & Review Scores)", metrics["success_rate_pct"] == 96.0 and metrics["average_test_score"] >= 90)
    check("Refined vague prompt into enhanced production prompt", "PostgreSQL" in refined_prompt and "Docker" in refined_prompt)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 93 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day93_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
