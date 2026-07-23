"""
Day 88 & 89 - Autonomous AI Company: Self-Evolution, Continuous Learning & AI OS Verification Suite
======================================================================================================
Validates AIForge Autonomous Learning & Evolution System across all 9 testing checklist items:
- Test 1: Reusable Component Recommendation (Suggests pre-built UI & backend components saving ~70% time)
- Test 2: Knowledge Base Project Storage (Stores completed projects with stacks, performance scores & reuse scores)
- Test 3: Error Memory & Fix Retrieval (Remembers error-fix pairs and recommends previous fix when duplicate errors occur)
- Test 4: Semantic Embedding Project Search (Uses embeddings to match 'Food Delivery App' to 'Restaurant App')
- Test 5: Comprehensive Code Ranking (Scores projects across 10 metrics: Perf, Sec, Maint, Read, Complex, Arch, Test, Doc, Deploy, Scale)
- Test 6: Engineering Standards Enforcement (Generates company standards and applies them automatically to generated code)
- Test 7: Knowledge Graph Relationships (Builds graph linking JWT -> Auth -> FastAPI -> React -> MongoDB -> Project)
- Test 8: Evolution Engine Memory Updates (Updates memories, templates, and recommendations after each build)
- Test 9: Learning Dashboard Telemetry (Displays project history, reuse rate %, quality trends, and error patterns)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.learning.learner import global_project_learner
from backend.learning.ranking import global_code_ranking_engine
from backend.learning.recommender import global_component_recommender
from backend.learning.embeddings import global_embedding_engine
from backend.learning.feedback import global_error_feedback_engine
from backend.learning.similarity import global_similarity_engine
from backend.learning.evolution import global_evolution_engine
from backend.learning.analytics import global_learning_analytics
from backend.memory.project_memory import global_project_memory
from backend.memory.vector_memory import global_vector_memory

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


async def run_day88_89_tests():
    print("======================================================================")
    print(" AIForge Day 88-89 - Autonomous AI Company & Self-Evolution Verification")
    print("======================================================================\n")

    # ------------------------------------------------------------------
    section("Test 1 – Reusable Component Recommendation (Day 88)")
    # ------------------------------------------------------------------
    recs = global_component_recommender.recommend_reusable_components("Build a SaaS Customer Dashboard")
    
    check("Recommended pre-built reusable UI & API components", recs["reusable_components_found"] >= 4)
    check("Estimated development time savings (~70% savings)", "70%" in recs["estimated_development_time_savings"])

    # ------------------------------------------------------------------
    section("Test 2 – Knowledge Base Project Storage (Day 88)")
    # ------------------------------------------------------------------
    learn_res = global_project_learner.record_completed_project(
        project_name="AI Medical Imaging Portal",
        tech_stack=["FastAPI", "React", "PostgreSQL", "Docker"],
        performance_score=9.7,
        reuse_score_pct=96.0
    )

    check("Stored completed project in project memory database", learn_res["status"] == "success")
    check("Project record contains stack, performance, and reuse score", 
          global_project_memory.get_all_projects()[-1]["reuse_score_pct"] == 96.0)

    # ------------------------------------------------------------------
    section("Test 3 – Error Memory & Automated Fix Recommendation (Day 89)")
    # ------------------------------------------------------------------
    global_error_feedback_engine.record_error_and_fix(
        error_type="ImportError",
        cause="Wrong relative import path in router",
        recommended_fix="Use absolute package import 'from backend.routes import auth'"
    )
    fix_retrieved = global_error_feedback_engine.get_recommended_fix("ImportError: cannot import name auth")

    check("Recorded error-fix pair in persistent error memory", fix_retrieved is not None)
    check("Recommended previous fix when duplicate error occurred", "absolute package import" in fix_retrieved["recommended_fix"])

    # ------------------------------------------------------------------
    section("Test 4 – Semantic Embedding Project Search (Day 88)")
    # ------------------------------------------------------------------
    similar_projects = global_similarity_engine.find_similar_projects("Food Delivery App", top_k=2)

    check("Generated vector embeddings for similarity search", len(similar_projects) > 0)
    check("Retrieved similar past projects via embedding cosine similarity", similar_projects[0]["similarity_score_numeric"] > 0)

    # ------------------------------------------------------------------
    section("Test 5 – Comprehensive 10-Metric Code Ranking Engine (Day 89)")
    # ------------------------------------------------------------------
    rank_res = global_code_ranking_engine.rank_project_quality("AI Medical Imaging Portal")
    categories = rank_res["category_scores"]

    check("Scored project across 10 quality metrics (Perf, Sec, Maint, Read, Complex, Arch, Test, Doc, Deploy, Scale)", len(categories) == 10)
    check("Assigned overall ranking score & tier (Overall >= 95.0% - Enterprise Premier)", rank_res["overall_ranking_score"] >= 95.0)

    # ------------------------------------------------------------------
    section("Test 6 – Engineering Standards Generation & Auto Enforcement (Day 89)")
    # ------------------------------------------------------------------
    standards = global_learning_analytics.generate_engineering_standards()
    raw_code = "def process_data(): pass"
    standardized_code = global_learning_analytics.apply_standards_to_code(raw_code)

    check("Generated corporate engineering standards (naming, folder structure, testing, logging)", "naming_conventions" in standards)
    check("Automatically applied engineering standards to generated code", "import logging" in standardized_code)

    # ------------------------------------------------------------------
    section("Test 7 & 8 – Knowledge Graph & Evolution Engine (Day 89)")
    # ------------------------------------------------------------------
    evo_res = global_evolution_engine.evolve_system("AI Medical Imaging Portal", ["FastAPI", "React", "PostgreSQL", "Docker"])
    graph = global_evolution_engine.get_knowledge_graph()

    check("Evolution Engine updated system memory & knowledge base", evo_res["status"] == "success")
    check("Knowledge Graph linked technologies, patterns, and projects", len(graph["nodes"]) >= 6 and len(graph["edges"]) >= 6)

    # ------------------------------------------------------------------
    section("Test 9 – Learning Dashboard Telemetry (Day 89)")
    # ------------------------------------------------------------------
    dash = global_learning_analytics.get_dashboard_analytics()

    check("Dashboard displays code reuse rate % (Reuse >= 70%)", dash["overall_code_reuse_rate_pct"] >= 70.0)
    check("Dashboard displays weekly quality trends & common error patterns", len(dash["quality_trend_progression"]) >= 4)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 88-89 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day88_89_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
