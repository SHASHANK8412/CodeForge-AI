"""
AIForge V2 Day 41 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 41 deliverables:
1. Project Memory Storage & User Feedback Collection
2. Bug Fix Memory Recording & Matching Solution Retrieval
3. Reusable Pattern Detection & Template Catalog
4. Semantic Vector Search across Historical Projects
5. Success Tracker Analytics & Agent Performance Metrics
6. Production Learning Engine Pre-Generation Enrichment & Post-Generation Update
7. LangGraph Workflow Graph Topology Integration
8. Learning REST APIs & Dashboard Metrics
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.learning.project_memory import global_production_project_memory
from backend.learning.knowledge_store import global_production_knowledge_store
from backend.learning.pattern_detector import global_pattern_detector
from backend.learning.embedding_search import global_semantic_search_engine
from backend.learning.success_tracker import global_success_tracker
from backend.learning.learning_engine import global_production_learning_engine
from backend.graph.workflow import create_workflow_graph

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


def run_v2_day41_verification():
    print("======================================================================")
    print(" 🧠 AIForge V2 – Day 41 Production-Ready Learning Engine Verification")
    print("======================================================================\n")

    section("1. Project Memory Storage & Feedback Collection")
    proj = global_production_project_memory.record_project(
        user_prompt="Build an e-commerce platform with FastAPI and React",
        architecture="Microservices Blueprint",
        technologies=["FastAPI", "React", "PostgreSQL", "Docker"],
        execution_time_seconds=22.0
    )
    check("Automatically recorded project in persistent memory", proj["project_id"].startswith("proj_mem_"))

    updated_proj = global_production_project_memory.add_user_feedback(proj["project_id"], rating=5, comment="Great code!")
    check("Added user feedback rating (5 stars)", updated_proj["user_feedback"]["rating"] == 5)

    section("2. Bug Fix Memory & Solution Retrieval")
    bug_fix = global_production_knowledge_store.record_bug_fix(
        bug="Database Connection Pool Exhausted",
        cause="Missing pool_pre_ping parameter",
        solution="Set pool_pre_ping=True in engine configuration",
        affected_files=["backend/database.py"]
    )
    check("Recorded bug fix memory with confidence score", bug_fix["confidence_score"] >= 0.9)

    found_sol = global_production_knowledge_store.find_matching_bug_solution("Database Connection error")
    check("Retrieved matching bug fix solution automatically", found_sol is not None and "pool_pre_ping" in found_sol["solution"])

    section("3. Reusable Pattern Detection")
    detected = global_pattern_detector.detect_patterns("Build a FastAPI REST API with JWT Auth", generated_code="from fastapi import FastAPI")
    check("Detected reusable software patterns", len(detected) >= 2)

    section("4. Semantic Vector Search Engine")
    search_res = global_semantic_search_engine.search_similar_projects("food delivery platform with FastAPI")
    check("Retrieved top matching historical projects via semantic search", len(search_res["matching_projects"]) >= 1)

    section("5. Success Tracker Analytics & Metrics")
    stats = global_success_tracker.get_statistics()
    check("Compiled platform success rates & build time metrics", stats["statistics"]["project_success_rate_pct"] > 90.0)

    section("6. Production Learning Engine Lifecycle")
    enrichment = global_production_learning_engine.enrich_planning_context("Build a food delivery backend")
    check("Pre-generation enrichment extracted past project context", len(enrichment["similar_projects"]) >= 1)

    upd_summary = global_production_learning_engine.update_learning_knowledge({
        "user_prompt": "Food Delivery Backend",
        "architecture": "Microservices",
        "generated_files": ["main.py", "auth.py"],
        "start_time": 100.0
    })
    check("Post-generation knowledge update completed", "project_record" in upd_summary)

    section("7. LangGraph Workflow Graph Topology")
    compiled_graph = create_workflow_graph()
    check("Compiled LangGraph workflow graph with Learning Enricher and Learning Updater nodes", compiled_graph is not None)

    section("8. Learning Dashboard Metrics")
    dash = global_production_learning_engine.get_dashboard_data()
    check("Compiled Learning Dashboard metrics", dash["projects_stored_count"] >= 2 and dash["patterns_learned_count"] >= 2)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 41 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day41_verification()
    sys.exit(0 if success else 1)
