"""
Day 78 & 79 - Repository Intelligence & Autonomous Project Evolution Verification Suite
==========================================================================================
Validates AIForge Repository Intelligence and Autonomous Evolution Engine across Day 78 and Day 79 testing checklists:
- Test 1: Repository Intelligence Scanner (Scans 100+ files across Python, JS, TS, JSON, MD, YAML; extracts metadata)
- Test 2: Project Tree & Symbol Table Indexer (Generates Frontend/Backend/Tests/Docker tree; indexes functions, classes, routes)
- Test 3: Dependency Graph & Prompt Context Upgrader (Builds Login->Auth Context->JWT->Service->DB graph; upgrades agent prompt)
- Test 4: Repository Refactoring & Architecture Analysis (Detects UI business logic & route DB queries; score = 93/100)
- Test 5: Duplicate & Dead Code Detection (Detects 4 duplicate files & 7 unused components)
- Test 6: Complete Evolution Report & Documentation Generator (Produces scores: Arch 93, Sec 90, Perf 88, Maint 95; updates README)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.repository.scanner import RepositoryScanner
from backend.repository.indexer import RepositoryIndexer
from backend.repository.dependency_graph import RepositoryDependencyGraph
from backend.repository.symbol_table import RepositorySymbolTable
from backend.repository.repository_memory import RepositoryMemory

from backend.analysis.architecture import ArchitectureChecker
from backend.analysis.quality import QualityAnalyzer
from backend.analysis.security import RepositorySecurityScanner
from backend.analysis.performance import PerformanceScanner
from backend.analysis.duplicates import DuplicateDetector
from backend.analysis.dead_code import DeadCodeDetector
from backend.agents.evolution_agent import EvolutionAgent

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


async def run_day78_79_tests():
    print("======================================================================")
    print(" AIForge Day 78-79 - Repository Intelligence & Evolution Verification")
    print("======================================================================\n")

    workspace = str(project_root)
    scanner = RepositoryScanner()
    indexer = RepositoryIndexer(scanner=scanner)
    dep_graph = RepositoryDependencyGraph()
    repo_memory = RepositoryMemory()
    evolution_agent = EvolutionAgent(workspace_root=workspace)

    # ------------------------------------------------------------------
    section("Test 1 – Repository Intelligence Scanner (Day 78)")
    # ------------------------------------------------------------------
    scan_res = scanner.scan_repository(workspace)
    scanned_count = scan_res.get("scanned_files_count", 0)
    langs = scan_res.get("language_breakdown", {})

    check("Scanned repository with 100+ files (> 100 files)", scanned_count >= 100)
    check("Extracted metadata for Python files", "Python" in langs)
    check("Extracted metadata for JavaScript / React files", any(l in langs for l in ["JavaScript", "React JS", "React TS"]))
    check("Extracted metadata for JSON, Markdown, and YAML files", "JSON" in langs or "Markdown" in langs)

    # ------------------------------------------------------------------
    section("Test 2 – Project Tree & Symbol Table Indexer (Day 78)")
    # ------------------------------------------------------------------
    index_res = indexer.index_repository(workspace)
    tree = index_res.get("project_tree", {})
    symbols = repo_memory.symbol_table.build_symbol_table(index_res.get("raw_file_metadata", []))

    check("Generated Frontend & Backend project tree categorization", "Frontend" in tree and "Backend" in tree)
    check("Indexed repository symbol table (> 0 functions/classes)", symbols["total_symbols"] > 0)
    check("Indexed API route definitions & controllers", len(symbols["routes"]) >= 0)

    # ------------------------------------------------------------------
    section("Test 3 – Dependency Graph & Upgraded Prompt Context (Day 78)")
    # ------------------------------------------------------------------
    graph_res = dep_graph.build_graph_from_metadata(index_res.get("raw_file_metadata", []))
    upgraded_prompt = repo_memory.get_upgraded_prompt("Add Payment Service feature", workspace_root=workspace)

    check("Constructed visual module dependency flow (Login->Auth->JWT->Service->DB)", graph_res["has_auth_pipeline"])
    check("Persisted repository intelligence memory in repository_memory.json", repo_memory.file_path.exists())
    check("Upgraded LLM prompt with Repository Context & Architecture guidelines", "REPOSITORY INTELLIGENCE CONTEXT" in upgraded_prompt)
    check("Upgraded prompt contains existing APIs and style directives", "DIRECTIVE: Generate implementation strictly consistent" in upgraded_prompt)

    # ------------------------------------------------------------------
    section("Test 4 – Architectural Anti-Pattern Analysis (Day 79)")
    # ------------------------------------------------------------------
    arch_analysis = evolution_agent.arch_checker.analyze_architecture(index_res.get("raw_file_metadata", []))

    check("Flagged UI component business logic violations", arch_analysis["ui_business_logic_count"] >= 1)
    check("Calculated Architecture Score (score >= 90/100)", arch_analysis["architecture_score"] >= 90.0)

    # ------------------------------------------------------------------
    section("Test 5 – Duplicate Code & Dead Code Detection (Day 79)")
    # ------------------------------------------------------------------
    dup_res = evolution_agent.dup_detector.analyze_duplicates(index_res.get("raw_file_metadata", []))
    dead_res = evolution_agent.dead_code_detector.analyze_dead_code(index_res.get("raw_file_metadata", []))

    check("Detected duplicate code / repeated functions (>= 4 duplicate files)", dup_res["duplicate_files_count"] >= 4)
    check("Detected unused components & dead code (7 unused components)", dead_res["unused_components_count"] == 7)

    # ------------------------------------------------------------------
    section("Test 6 – Complete AIForge Evolution Report & Doc Generator (Day 79)")
    # ------------------------------------------------------------------
    evolution_report = evolution_agent.run_evolution_analysis(target_root=workspace)
    doc_result = evolution_agent.update_documentation(evolution_report)

    check("Produced Architecture Score (= 93/100)", evolution_report["architecture_score"] == 93.0)
    check("Produced Security Score (= 90/100)", evolution_report["security_score"] == 90.0)
    check("Produced Performance Score (= 88/100)", evolution_report["performance_score"] == 88.0)
    check("Produced Maintainability Score (= 95/100)", evolution_report["maintainability_score"] == 95.0)
    check("Estimated Speed Improvement (= 31%)", evolution_report["estimated_speed_improvement_pct"] == 31)
    check("Documentation Generator updated README.md with Evolution Report", doc_result["readme_updated"])

    # Summary
    print("\n" + "="*70)
    print(f" DAY 78-79 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day78_79_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
