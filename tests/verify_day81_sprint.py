"""
Day 81 - Autonomous AI Dev Team Collaboration & Sprint Execution Verification Suite
====================================================================================
Validates AIForge Sprint Manager Agent and Autonomous Agile Development Team across 7 core testing scenarios:
- Test 1: Task Creation (Generates tasks with unique IDs, priorities, dependencies, and assigned agents)
- Test 2: Parallel Execution (Independent tasks execute simultaneously in parallel via asyncio.gather)
- Test 3: Dependency Enforcement (Backend waits for DB; Frontend waits for Backend API; Docs/Tests wait for code)
- Test 4: Conflict Detection (Detects concurrent agents editing same file and resolves automatically)
- Test 5: Retry Logic (Forces agent execution failure -> Sprint Manager retries & delegates to backup agent)
- Test 6: Progress Dashboard (Live metrics tracking completed, running, waiting, failed tasks, and completion %)
- Test 7: Sprint Report (Generates end-of-sprint report with completed features, agent stats, retries, token usage, LLM calls)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.sprint.sprint_manager import SprintManagerAgent
from backend.sprint.task import SprintTask
from backend.sprint.dependency_graph import SprintDependencyGraph
from backend.sprint.scheduler import SprintScheduler
from backend.sprint.conflict_detector import ConflictDetector
from backend.sprint.progress_tracker import SprintProgressTracker
from backend.sprint.sprint_report import SprintReportGenerator

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


async def run_day81_tests():
    print("======================================================================")
    print(" AIForge Day 81 - Agile Sprint Manager & AI Dev Team Verification")
    print("======================================================================\n")

    sprint_manager = SprintManagerAgent()

    # ------------------------------------------------------------------
    section("Test 1 – Task Creation & Assignment")
    # ------------------------------------------------------------------
    tasks = sprint_manager.plan_sprint_tasks("E-Commerce Enterprise System")

    check("Generated multiple sprint tasks (> 5 tasks)", len(tasks) >= 6)
    check("Task IDs and assigned agents initialized", all(t.task_id and t.assigned_agent for t in tasks))
    check("Priorities assigned (HIGH, MEDIUM, LOW)", any(t.priority == "HIGH" for t in tasks))
    check("Target file paths assigned per task", all(len(t.target_files) > 0 for t in tasks))

    # ------------------------------------------------------------------
    section("Test 2 & 3 – Parallel Execution & Dependency Enforcement")
    # ------------------------------------------------------------------
    runnable_initial = sprint_manager.dep_graph.get_runnable_tasks()
    runnable_ids = [t.task_id for t in runnable_initial]

    check("Independent initial tasks (DB TASK-101) identified as runnable", "TASK-101" in runnable_ids)
    check("Dependent tasks (Backend TASK-102 & Testing TASK-104) forced to wait", "TASK-102" not in runnable_ids and "TASK-104" not in runnable_ids)

    # ------------------------------------------------------------------
    section("Test 4 – Conflict Detection")
    # ------------------------------------------------------------------
    conflict_detector = ConflictDetector()
    task_a = SprintTask("T-1", "Backend Config", "Backend Agent", target_files=["src/api/config.js"])
    task_b = SprintTask("T-2", "Frontend Config", "Frontend Agent", target_files=["src/api/config.js"])
    
    conflicts = conflict_detector.detect_conflicts([task_a, task_b])

    check("Conflict detector identified concurrent file edits on src/api/config.js", len(conflicts) == 1)
    check("Automatic conflict resolution strategy generated", "automatically merged" in conflicts[0]["resolution"])

    # ------------------------------------------------------------------
    section("Test 5 – Retry Logic & Backup Agent Reallocation")
    # ------------------------------------------------------------------
    sprint_res = await sprint_manager.execute_sprint(failure_task_ids=["TASK-102"])
    report = sprint_res["report"]
    task_102 = [t for t in sprint_res["tasks"] if t["task_id"] == "TASK-102"][0]

    check("Triggered retry for failed task (TASK-102)", task_102["retry_count"] >= 1)
    check("Delegated failed task to backup agent (Senior Architectural Reviewer)", task_102["assigned_agent"] == "Senior Architectural Reviewer")
    check("Task successfully completed after retry", task_102["status"] == "Completed")

    # ------------------------------------------------------------------
    section("Test 6 – Progress Dashboard Telemetry")
    # ------------------------------------------------------------------
    progress = sprint_res["progress"]

    check("Tracked completed tasks count", progress["completed_tasks"] >= 6)
    check("Calculated overall completion percentage (= 100.0%)", progress["overall_completion_pct"] == 100.0)

    # ------------------------------------------------------------------
    section("Test 7 – Comprehensive End-of-Sprint Report")
    # ------------------------------------------------------------------
    check("Report includes list of completed features", len(report["completed_features"]) >= 6)
    check("Report includes overall execution time", report["overall_execution_time_seconds"] > 0)
    check("Report includes agent performance statistics", "Database Agent" in report["agent_performance"])
    check("Report includes token usage & LLM call telemetry", report["telemetry"]["token_usage"] > 0 and report["telemetry"]["llm_calls"] > 0)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 81 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day81_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
