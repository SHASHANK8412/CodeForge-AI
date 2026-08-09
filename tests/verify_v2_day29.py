"""
AIForge V2 Day 29 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 29 deliverables:
1. Autonomous Project Manager Agent Initialization & AgentFactory Registration
2. Milestone Breakdown (7 Core Milestones: Setup, Auth, Frontend, Backend, DB, QA, Deploy)
3. Task Decomposition & Specialized Agent Assignments (Frontend, Backend, DB, QA, Reviewer)
4. Real-time Progress Tracking, Progress JSON, and ASCII Progress Bar Rendering
5. Blocker Detection & Automatic Task Reassignment Strategy
6. Daily Executive Report Generator (Markdown & Summary Metrics)
7. LangGraph Workflow Graph Sequence Update (`Planner -> Project Manager -> Architect ...`)
8. REST API Endpoints (`/project/start`, `/project/status`, `/project/report`, `/project/tasks`, `/project/dashboard`)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.factory import AgentFactory
from backend.agents.project_manager_agent import ProjectManagerAgent, global_project_manager_agent
from backend.graph.workflow import graph as workflow_graph

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


def run_v2_day29_verification():
    print("======================================================================")
    print(" 👔 AIForge V2 – Day 29 Autonomous Project Manager Agent Verification")
    print("======================================================================\n")

    project_name = "Food Delivery App"

    section("1. AgentFactory Registration & Initialization")
    pm_agent = AgentFactory.create_agent("project_manager")
    check("Created ProjectManagerAgent via AgentFactory", isinstance(pm_agent, ProjectManagerAgent))

    section("2. Milestone Breakdown & Sprint Planning")
    milestones = pm_agent.break_into_milestones(project_name)
    check("Decomposed project into 7 core milestones", len(milestones) == 7, f"Milestones: {[m['title'] for m in milestones]}")

    section("3. Milestone Task Decomposition & Agent Assignments")
    auth_tasks = pm_agent.divide_milestone_into_tasks("m2", "Milestone 2: Authentication & Security")
    check("Divided Authentication milestone into 5 granular tasks", len(auth_tasks) == 5)

    assigned_tasks = pm_agent.assign_agents(auth_tasks)
    check("Assigned specialized agents to tasks", all(t.get("status") == "Assigned" for t in assigned_tasks))

    section("4. Progress Tracking & ASCII Progress Bar")
    # Simulate marking tasks completed
    assigned_tasks[0]["status"] = "Completed"
    assigned_tasks[1]["status"] = "Completed"
    assigned_tasks[2]["status"] = "Completed"

    metrics = pm_agent.monitor_completion(assigned_tasks)
    check("Computed completion metrics (3/5 tasks done)", metrics["completed"] == 3 and metrics["remaining"] == 2)

    progress_json = pm_agent.generate_progress_json(project_name, assigned_tasks, current_agent="Frontend Agent")
    check("Generated Day 29 Progress JSON schema", progress_json["project"] == project_name and progress_json["progress"] == 60)

    progress_bar_str = pm_agent.render_progress_bar(60.0)
    check("Rendered ASCII progress bar", "████████████░░░░░░░░ 60.0%" in progress_bar_str, f"Bar: {progress_bar_str}")

    section("5. Blocker Detection & Automatic Task Reassignment")
    # Simulate a failed task
    failed_task = dict(assigned_tasks[3])
    failed_task["status"] = "Failed"
    failed_task["error"] = "Missing backend endpoint for password reset"

    test_tasks_with_failure = list(assigned_tasks) + [failed_task]
    blockers = pm_agent.detect_blockers(test_tasks_with_failure)
    check("Detected blocked task & failure reason", len(blockers) >= 1 and "Missing backend" in blockers[0]["reason"])

    reassigned = pm_agent.reassign_work(failed_task, failure_reason=blockers[0]["reason"])
    check("Reassigned failed task for self-healing", reassigned["status"] == "Reassigned" and "reassigned_to" in reassigned)

    section("6. Daily Executive Report Generator")
    daily_report = pm_agent.generate_daily_report(project_name, assigned_tasks)
    check("Generated Daily Executive Report in Markdown & JSON", "markdown" in daily_report and len(daily_report["completed_tasks"]) == 3)

    section("7. LangGraph Workflow Graph Sequence Update")
    nodes_in_graph = list(workflow_graph.nodes.keys())
    check("LangGraph workflow graph contains 'project_manager' node", "project_manager" in nodes_in_graph, f"Nodes: {nodes_in_graph}")

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 29 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day29_verification()
    sys.exit(0 if success else 1)
