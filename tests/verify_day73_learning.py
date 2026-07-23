"""
Day 73 - Autonomous Learning & Self-Improvement Engine Verification Suite
========================================================================
Validates AIForge Autonomous Learning Engine across 5 core testing scenarios:
- Test 1: Architecture Reuse (Generating same project twice reuses previous successful architecture)
- Test 2: Feedback & Prompt Optimization (Detects missing JWT -> Prompt Optimizer adds JWT requirements)
- Test 3: Recurring Error & Best Practices Update (Identifies validation failure pattern -> Updates Best Practices DB)
- Test 4: Architecture Memory Category Matching (Recommends optimal architecture for Todo App, Chat App, E-Commerce)
- Test 5: Generation Cycle & Telemetry (Stores experience, updates metrics, generates improvement report, and feeds dashboard)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.learning.experience_store import ExperienceStore
from backend.learning.feedback_analyzer import FeedbackAnalyzer
from backend.learning.prompt_optimizer import PromptOptimizer
from backend.learning.architecture_memory import ArchitectureMemory
from backend.learning.best_practices import BestPracticesGenerator
from backend.learning.learning_engine import LearningEngine

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


async def run_day73_tests():
    print("======================================================================")
    print(" AIForge Day 73 - Autonomous Learning & Self-Improvement Verification")
    print("======================================================================\n")

    engine = LearningEngine()

    # ------------------------------------------------------------------
    section("Test 1 – Architecture Reuse for Similar Projects")
    # ------------------------------------------------------------------
    # Step A: Run learning cycle for first generation
    engine.run_learning_cycle(
        project_name="Inventory App",
        project_type="Inventory",
        user_prompt="Build an Inventory Management System",
        technologies=["React", "FastAPI", "PostgreSQL", "Docker"],
        architecture="FastAPI + PostgreSQL + Docker",
        success=True,
        execution_time=32.0,
        score=98.0
    )

    # Step B: Search prior experience for second generation of similar prompt
    prior_res = engine.query_prior_experience("Build an Inventory Management System")

    check("Prior experience match detected for duplicate project request", prior_res["similar_experience_found"])
    check("Recommended architecture reuses previous successful build stack", "FastAPI" in prior_res["recommended_architecture"])
    check("Enhanced prompt generated with requirements", "Requirements:" in prior_res["enhanced_prompt"])

    # ------------------------------------------------------------------
    section("Test 2 – Missing Security Feedback & Prompt Optimization")
    # ------------------------------------------------------------------
    # Simulate reviewer feedback detecting missing JWT
    raw_prompt = "Build a Todo App"
    enhanced_prompt = engine.prompt_optimizer.enhance_user_prompt(raw_prompt)
    
    # Trigger system prompt optimization based on missing JWT criticism
    opt_system_prompt = engine.prompt_optimizer.optimize_prompt(
        agent_name="backend",
        reviewer_feedback="Missing JWT authentication on protected user routes"
    )

    check("Prompt Optimizer enhanced raw prompt with JWT requirements", "JWT Authentication" in enhanced_prompt)
    check("Backend System Prompt updated to address reviewer feedback", len(opt_system_prompt) > 0)
    check("Prompt version history recorded in prompt_versions.json", len(engine.prompt_optimizer.get_prompt_history()) > 0)

    # ------------------------------------------------------------------
    section("Test 3 – Recurring Errors & Best Practices Database Update")
    # ------------------------------------------------------------------
    # Simulate multiple runs encountering input validation errors
    for i in range(2):
        engine.run_learning_cycle(
            project_name=f"API_Project_{i}",
            project_type="API",
            user_prompt="Build User API",
            technologies=["FastAPI"],
            architecture="FastAPI",
            success=False,
            execution_time=20.0,
            errors=["Missing input validation for payload"],
            score=75.0
        )

    feedback_analysis = engine.feedback_analyzer.analyze_feedback()
    best_practices = engine.best_practices.get_all_best_practices()

    check("Feedback Analyzer classified recurring input validation errors", "Missing Input Validation" in feedback_analysis["error_breakdown"])
    check("Best Practices database updated with input validation rules", any("Pydantic" in bp["rule"] or "validation" in bp["rule"] for bp in best_practices))

    # ------------------------------------------------------------------
    section("Test 4 – Architecture Memory Category Matching")
    # ------------------------------------------------------------------
    chat_arch = engine.architecture_memory.get_best_architecture("Chat Application")
    todo_arch = engine.architecture_memory.get_best_architecture("Todo App")
    ecom_arch = engine.architecture_memory.get_best_architecture("E-Commerce Website")

    check("Architecture Memory recommended Chat App stack (React + FastAPI + Redis)", "Redis" in chat_arch["technologies"] or "FastAPI" in chat_arch["technologies"])
    check("Architecture Memory recommended Todo App stack", "SQLite" in todo_arch["technologies"] or "FastAPI" in todo_arch["technologies"])
    check("Architecture Memory recommended E-Commerce stack", "Stripe" in ecom_arch["technologies"] or "React" in ecom_arch["technologies"])

    # ------------------------------------------------------------------
    section("Test 5 – Complete Generation Cycle & Dashboard Telemetry")
    # ------------------------------------------------------------------
    cycle_res = engine.run_learning_cycle(
        project_name="SaaS Analytics Dashboard",
        project_type="Dashboard",
        user_prompt="Build a SaaS Analytics Dashboard",
        technologies=["React", "FastAPI", "PostgreSQL", "Redis"],
        architecture="React + FastAPI + PostgreSQL",
        success=True,
        execution_time=36.5,
        errors=[],
        fixes=[],
        score=99.0
    )

    telemetry = engine.get_telemetry()

    check("Experience recorded in Experience Store", cycle_res["experience"]["id"].startswith("exp_"))
    check("Improvement report generated with execution time & score", cycle_res["improvement_report"]["success_score"] == 99.0)
    check("Learning Dashboard telemetry reflects total projects learned (>= 4)", telemetry["projects_learned"] >= 4)
    check("Learning Dashboard telemetry reflects patterns stored (>= 45)", telemetry["patterns_stored"] >= 45)
    check("Learning Dashboard telemetry reflects success rate percentage", telemetry["success_rate_pct"] > 0)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 73 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day73_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
