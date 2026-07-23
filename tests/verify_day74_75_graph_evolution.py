"""
Day 74 & 75 - Project Knowledge Graph + Autonomous Code Evolution Verification Suite
======================================================================================
Validates AIForge Knowledge Graph and Code Evolution Engine across 6 core testing scenarios:
- Test 1: Build Project Graph (Scans codebase, counts files, functions, classes, APIs, DB models, saves project_graph.json)
- Test 2: Query Dependencies (Query "Which files depend on auth.py?" returns frontend, routes, middleware)
- Test 3: Impact Analysis (Query "Rename User model to Account" calculates affected files count=12, risk level, migrations)
- Test 4: Selective Testing (Modify auth.py -> Runs 8 related tests, skips 124 unaffected tests)
- Test 5: Documentation Update (Modify API -> Updates README, Swagger, Architecture Mermaid Diagram, Dependency Graph)
- Test 6: Complete Code Evolution (Prompt "Replace JWT authentication with OAuth2" generates impact, migration plan, rollback plan, updates 18 files, runs tests, updates docs)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.graph.builder import GraphBuilder
from backend.graph.query_engine import GraphQueryEngine
from backend.graph.analyzer import GraphAnalyzer
from backend.graph.visualizer import GraphVisualizer
from backend.evolution.impact import ImpactAnalyzer
from backend.evolution.planner import EvolutionPlanner
from backend.evolution.patch_generator import EvolutionPatchGenerator
from backend.evolution.rollback import RollbackEngine
from backend.evolution.selective_runner import SelectiveTestRunner
from backend.evolution.doc_updater import DocumentationUpdater
from backend.evolution.migration import CodeEvolutionEngine

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


async def run_day74_75_tests():
    print("======================================================================")
    print(" AIForge Day 74-75 - Knowledge Graph & Code Evolution Verification")
    print("======================================================================\n")

    builder = GraphBuilder()
    query_engine = GraphQueryEngine()
    impact_analyzer = ImpactAnalyzer()
    selective_runner = SelectiveTestRunner()
    doc_updater = DocumentationUpdater()
    evolution_engine = CodeEvolutionEngine()

    # ------------------------------------------------------------------
    section("Test 1 – Build Project Knowledge Graph")
    # ------------------------------------------------------------------
    G, summary = builder.build_graph()

    check("Scanned codebase files (> 0 files)", summary["total_files"] > 0)
    check("Extracted functions (> 0 functions)", summary["total_functions"] > 0)
    check("Extracted classes (> 0 classes)", summary["total_classes"] > 0)
    check("Extracted APIs (> 0 APIs)", summary["total_apis"] > 0)
    check("Saved NetworkX graph to project_graph.json", Path(builder.memory.file_path).exists())

    # ------------------------------------------------------------------
    section("Test 2 – Query Dependencies")
    # ------------------------------------------------------------------
    dep_query = query_engine.query("Which files depend on auth.py?")
    dep_files = dep_query.get("dependent_files", [])

    check("Dependency query processed successfully", dep_query["query_type"] == "dependencies")
    check("Located dependent frontend/login files", any("login" in f.lower() for f in dep_files))
    check("Located dependent routes & middleware files", any("auth" in f.lower() or "jwt" in f.lower() for f in dep_files))

    # ------------------------------------------------------------------
    section("Test 3 – Impact Analysis for Schema Refactoring")
    # ------------------------------------------------------------------
    impact = impact_analyzer.evaluate_impact("Rename User model to Account", target_symbol="User")

    check("Calculated affected files count (= 12 files)", impact["affected_files_count"] == 12)
    check("Estimated risk level (= Medium)", impact["risk_level"] == "Medium")
    check("Identified required API & DB migrations", impact["requires_api_update"] and impact["requires_db_migration"])
    check("Identified required Frontend updates", impact["requires_frontend_update"])

    # ------------------------------------------------------------------
    section("Test 4 – Selective Test Runner")
    # ------------------------------------------------------------------
    test_run = selective_runner.run_selective_tests(["backend/routes/auth.py"])

    check("Ran related test cases (= 8 related tests)", test_run["related_tests_run"] == 8)
    check("Skipped unaffected test cases (= 124 skipped tests)", test_run["unaffected_tests_skipped"] == 124)
    check("All selective impacted tests passed cleanly", test_run["all_passed"])

    # ------------------------------------------------------------------
    section("Test 5 – Automated Documentation Synchronization")
    # ------------------------------------------------------------------
    doc_res = doc_updater.update_documentation({
        "proposed_change": "Update Auth API",
        "files_updated": ["backend/routes/auth.py"]
    })

    check("README.md updated with evolution changelog", doc_res["readme_updated"])
    check("Swagger / OpenAPI specification updated", doc_res["swagger_updated"])
    check("Architecture Mermaid diagram exported", doc_res["architecture_updated"])
    check("Dependency Graph documentation updated", doc_res["dependency_graph_updated"])

    # ------------------------------------------------------------------
    section("Test 6 – Complete Autonomous Code Evolution")
    # ------------------------------------------------------------------
    evolve_res = evolution_engine.evolve_codebase("Replace JWT authentication with OAuth2")

    check("Impact analysis calculated 18 affected files", evolve_res["impact_analysis"]["affected_files_count"] == 18)
    check("Migration plan generated with step-by-step procedure", len(evolve_res["migration_plan"]["steps"]) >= 5)
    check("Rollback plan generated with recovery steps", len(evolve_res["rollback_plan"]["rollback_steps"]) >= 4)
    check("Targeted evolution patches created (+ additions, - deletions)", evolve_res["patch_report"]["total_files_updated"] == 18)
    check("Selective test runner executed impacted tests", evolve_res["selective_test_results"]["all_passed"])
    check("Documentation updated automatically", evolve_res["documentation_updates"]["architecture_updated"])

    # Summary
    print("\n" + "="*70)
    print(f" DAY 74-75 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day74_75_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
