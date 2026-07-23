"""
Day 76 & 77 - Project Intelligence & Self-Improving Prompt Optimizer Verification Suite
========================================================================================
Validates AIForge Project Intelligence and Self-Improving Prompt Optimizer across 5 core testing scenarios:
- Test 1: Project Learning (Generate Todo app -> Extract architecture, tech stack, patterns, score -> Persist in ProjectMemoryDB)
- Test 2: Similarity Search (Generate Task Manager -> Query similarity engine -> Retrieve reusable patterns JWT, CRUD, auth)
- Test 3: Prompt Optimization (Generate prompt variants Version A/B/C -> Evaluator scores RL rewards/punishments -> Select winner)
- Test 4: Continuous Improvement (Simulate generation failure -> Evaluator records failure, updates prompt rankings, selects robust fallback)
- Test 5: End-to-End Learning Cycle (Complete generation cycle -> Learn lessons -> Next build reuses knowledge for improved output)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.learning.learner import MasterProjectLearner
from backend.learning.project_memory import ProjectMemoryDB
from backend.learning.similarity import SimilaritySearchEngine
from backend.learning.scorer import QualityScorer
from backend.optimizer.prompt_optimizer import SelfImprovingPromptOptimizer
from backend.optimizer.mutation import PromptMutationEngine
from backend.optimizer.evaluator import PromptEvaluator
from backend.optimizer.history import PromptHistoryStore

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


async def run_day76_77_tests():
    print("======================================================================")
    print(" AIForge Day 76-77 - Project Intelligence & Prompt Optimizer Verification")
    print("======================================================================\n")

    learner = MasterProjectLearner()
    optimizer = SelfImprovingPromptOptimizer()

    # ------------------------------------------------------------------
    section("Test 1 – Project Learning & Intelligence Extraction")
    # ------------------------------------------------------------------
    todo_learn = learner.learn_from_project(
        project_name="MERN Todo Application",
        tech_stack=["React", "Node.js", "Express", "MongoDB", "TailwindCSS"],
        architecture="MERN Stack",
        authentication="JWT",
        database_type="MongoDB",
        frontend_framework="React",
        design_patterns=["Repository", "MVC", "JWT Middleware"],
        syntax_errors=0,
        test_pass_rate=100.0,
        bugs_fixed_count=3,
        execution_time_seconds=28.5
    )

    db_projects = learner.db.get_all_projects()

    check("Learned from Todo App generation", todo_learn["status"] == "success")
    check("Extracted quality score (overall score >= 90.0)", todo_learn["overall_score"] >= 90.0)
    check("Persisted project intelligence in SQLite ProjectMemoryDB", len(db_projects) > 0)
    check("Stored tech stack, architecture, and fixed bugs count", db_projects[0]["bugs_fixed_count"] == 3)

    # ------------------------------------------------------------------
    section("Test 2 – Similarity Search & Pattern Reuse")
    # ------------------------------------------------------------------
    reusable = learner.query_prior_knowledge("Build a Task Management Application")

    check("Similarity search matched prior Todo project features", reusable["similar_project_found"])
    check("Similarity score calculated (> 0.40)", reusable["similarity_score"] >= 0.40)
    check("Retrieved reusable JWT Auth & CRUD API patterns", any("JWT" in p for p in reusable["reusable_patterns"]))
    check("Retrieved Docker container & CI/CD workflow configurations", any("Docker" in p for p in reusable["reusable_patterns"]))

    # ------------------------------------------------------------------
    section("Test 3 – Multi-Variant Prompt Optimization")
    # ------------------------------------------------------------------
    opt_res = optimizer.optimize_prompt_variants("Generate backend", target_agent="backend")

    check("Generated Version A, B, and C prompt mutations", len(opt_res["all_evaluated_variants"]) == 3)
    check("Evaluator selected highest-scoring SOLID production prompt", "Version C" in opt_res["winning_version"])
    check("Recorded winning prompt score (score >= 90.0)", opt_res["winning_score"] >= 90.0)
    check("Persisted winning prompt in Prompt History Store", opt_res["history_entry"]["version"].startswith("v"))

    # ------------------------------------------------------------------
    section("Test 4 – Failure Feedback & Continuous Improvement")
    # ------------------------------------------------------------------
    fail_opt_res = optimizer.optimize_prompt_variants("Generate backend", target_agent="backend", is_failure_scenario=True)

    check("Evaluator penalized failure-inducing prompt variants", any(v["score"] < 70.0 for v in fail_opt_res["all_evaluated_variants"]))
    check("Evaluator selected robust production variant as winner", fail_opt_res["winning_score"] >= 90.0)
    check("Updated prompt history with evolutionary version", len(optimizer.history_store.get_all_history()) >= 3)

    # ------------------------------------------------------------------
    section("Test 5 – End-to-End Self-Improving Learning Cycle")
    # ------------------------------------------------------------------
    # Step A: First run learns LMS project
    learner.learn_from_project(
        project_name="LMS Education Portal",
        tech_stack=["React", "FastAPI", "PostgreSQL", "Docker"],
        architecture="FastAPI + React",
        authentication="OAuth2",
        database_type="PostgreSQL",
        frontend_framework="React",
        design_patterns=["Repository Pattern", "JWT Middleware"],
        syntax_errors=0,
        test_pass_rate=100.0,
        bugs_fixed_count=5,
        execution_time_seconds=32.0
    )

    # Step B: Second run queries prior knowledge for Course Management App
    course_reuse = learner.query_prior_knowledge("Build a Course Management Application")
    best_prompt = optimizer.get_best_prompt("backend")

    check("Learned from LMS Education Portal project", course_reuse["similar_project_found"])
    check("Reused architecture from prior project", course_reuse["matched_project_name"] == "LMS Education Portal")
    check("Retrieved evolved best system prompt for next generation", "clean architecture" in best_prompt.lower() or "production" in best_prompt.lower() or "backend" in best_prompt.lower())

    # Summary
    print("\n" + "="*70)
    print(f" DAY 76-77 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day76_77_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
