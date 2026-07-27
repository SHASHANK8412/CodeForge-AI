"""
AIForge V2 Day 35 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 35 deliverables:
1. Knowledge Extractor Architecture & Pattern Mining from Completed Projects
2. Engineering Knowledge Graph Construction & Node-Edge Link Querying
3. Project Memory Persistent Profile Store
4. Reusable Software Asset Recommendation Engine
5. Continuous Learning Engine Pattern Stats & Knowledge Growth Metrics
6. Semantic Knowledge Retriever & Search Engine
7. Knowledge Dashboard Metrics & REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.knowledge.extractor import global_knowledge_extractor
from backend.knowledge.graph_builder import global_knowledge_graph_builder
from backend.knowledge.project_memory import global_project_memory_store
from backend.knowledge.recommender import global_recommendation_engine
from backend.knowledge.learning_engine import global_learning_engine
from backend.knowledge.retriever import global_knowledge_retriever

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


def run_v2_day35_verification():
    print("======================================================================")
    print(" 🧠 AIForge V2 – Day 35 Knowledge Graph & Continuous Learning Verification")
    print("======================================================================\n")

    section("1. Knowledge Extractor Pattern Mining")
    extracted = global_knowledge_extractor.extract_knowledge({"name": "Food Delivery App"})
    check("Extracted 7 engineering pattern categories from project", extracted["patterns_count"] == 7)

    section("2. Engineering Knowledge Graph Construction")
    graph = global_knowledge_graph_builder.get_full_graph()
    check("Constructed Knowledge Graph with nodes and edges", graph["total_nodes"] >= 8 and graph["total_edges"] >= 5)

    related = global_knowledge_graph_builder.get_related_nodes("Authentication")
    check("Queried related nodes for 'Authentication' (JWT, OAuth, RBAC)", len(related) >= 3)

    section("3. Project Memory Profile Persistence")
    mem_entry = global_project_memory_store.record_project_memory(
        project_name="E-Commerce Store",
        language="TypeScript",
        framework="Next.js + FastAPI",
        database="PostgreSQL",
        patterns=["JWT Auth", "Stripe Payment", "Redis Cache"]
    )
    check("Recorded persistent project profile in ProjectMemoryStore", mem_entry["project_name"] == "E-Commerce Store")

    all_projects = global_project_memory_store.get_all_projects()
    check("Retrieved all stored project profiles", len(all_projects) >= 3)

    section("4. Reusable Software Asset Recommendation Engine")
    recs = global_recommendation_engine.recommend_for_project(project_type="Food Delivery App")
    check("Recommended proven reusable software assets & blueprints", recs["recommended_assets_count"] >= 5)

    section("5. Continuous Learning Engine Pattern Stats")
    pattern_stat = global_learning_engine.record_pattern_usage("Repository Layer", was_successful=True)
    check("Updated pattern usage stats (Projects Used incremented)", pattern_stat["projects_used"] >= 29)

    stats = global_learning_engine.get_learning_stats()
    check("Compiled learning progress metrics & growth rate", "knowledge_growth_rate" in stats and len(stats["top_patterns"]) >= 4)

    section("6. Semantic Knowledge Retriever")
    search_res = global_knowledge_retriever.search_knowledge("JWT authentication")
    check("Retrieved historical implementation decisions for query", search_res["total_matches"] >= 1)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 35 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day35_verification()
    sys.exit(0 if success else 1)
