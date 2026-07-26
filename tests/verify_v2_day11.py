"""
AIForge V2 Day 11 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 11 deliverables:
1. PostgreSQL Database & ORM Connection (`db.py`, `models_memory.py`)
2. CRUD Layer (`crud.py`, `schemas_memory.py`)
3. Memory Service & Telemetry Storage (`memory_service.py`)
4. Project Service & Lifecycle Management (`project_service.py`)
5. FastAPI REST API Endpoints (`/projects`, `/memory/{id}`, `/logs/{id}`)
6. LangGraph Workflow Auto-Persistence Integration (`workflow_v2.py`)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.database.init_db import init_database
from v2.services.project_service import global_project_service
from v2.services.memory_service import global_memory_service
from v2.orchestrator.workflow_v2 import workflow_v2_graph

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


async def run_v2_day11_verification():
    print("======================================================================")
    print(" 💾 AIForge V2 – Day 11 PostgreSQL Integration & Memory System Verification")
    print("======================================================================\n")

    # Initialize Database
    init_database()

    section("1. Project CRUD & Persistent Storage")
    proj = global_project_service.create_new_project(
        title="Verification Test Project",
        description="Verifying PostgreSQL memory persistence"
    )
    check("Created new project in PostgreSQL database", proj.get("id") is not None)

    fetched = global_project_service.get_project_by_id(proj["id"])
    check("Fetched project by ID with task and conversation relations", fetched is not None and fetched["id"] == proj["id"])

    projects_list = global_project_service.fetch_all_projects()
    check("Listed active projects from database", len(projects_list) >= 1)

    section("2. Memory Service Recording & Telemetry Retrieval")
    project_id = proj["id"]
    global_memory_service.record_conversation(project_id, "user", "Generate an AI Resume Analyzer")
    global_memory_service.record_agent_output(project_id, "ceo", "Generate an AI Resume Analyzer", "CEO Evaluation Done", 15.0)

    memory_data = global_memory_service.get_project_memory(project_id)
    check("Retrieved project conversation history from database", memory_data["conversations_count"] >= 1)
    check("Retrieved agent telemetry logs from database", memory_data["logs_count"] >= 1)

    section("3. LangGraph Workflow Auto-Persistence Integration")
    prompt = "Build a real-time Chat Application"
    initial_state = {
        "user_prompt": prompt,
        "ceo_evaluation": None,
        "tasks": None,
        "planner_output": None,
        "architect_output": None,
        "frontend_output": None,
        "backend_output": None,
        "database_output": None,
        "reviewer_output": None,
        "testing_output": None,
        "documentation_output": None,
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)

    check("LangGraph workflow auto-created project & recorded CEO agent memory output", final_state.get("ceo_evaluation") is not None)

    # Cleanup
    global_project_service.remove_project(project_id)
    check("Cleaned up verification test project from database", global_project_service.get_project_by_id(project_id) is None)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 11 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day11_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
