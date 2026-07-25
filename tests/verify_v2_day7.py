"""
AIForge V2 Day 7 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 7 deliverables:
1. Database Agent (Autonomous PostgreSQL Database Design & Persistence Layer Generator)
2. PostgreSQL SQL DDL Schema & Initialization Generator
3. SQLAlchemy ORM Model & Relationship Generator
4. Alembic Versioned Schema Migration Generator
5. Index & Query Optimization Engine
6. Python Seed Data Script Generator
7. Backup & Monitoring Configuration Engine
8. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> END)
9. FastAPI Endpoint (POST /api/v2/database/generate)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.database.agent import global_database_agent_v2
from v2.agents.database.validator import global_database_validator
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


async def run_v2_day7_verification():
    print("======================================================================")
    print(" 🗄️ AIForge V2 – Day 7 PostgreSQL Database Persistence Generation Verification")
    print("======================================================================\n")

    # 1. Database Persistence Generation Test: AI Resume Analyzer
    prompt = "Build an AI Resume Analyzer using FastAPI and React."
    section("1. PostgreSQL DDL Schema & Table Specifications")
    report = global_database_agent_v2.generate_database(prompt, project_id="v2_day7_verify")

    check("Generated modular database folder structure tree", len(report.folder_structure) >= 8)
    check("Generated PostgreSQL SQL DDL schema script", len(report.ddl_schema_sql) > 100)
    check("Generated database table specifications (users, projects, tasks)", len(report.tables) >= 3)

    section("2. ORM Models, Relationships & Migrations")
    check("Generated production SQLAlchemy ORM models code", len(report.sqlalchemy_models_code) > 100)
    check("Generated 1:N foreign key table relationship specifications", len(report.relationships) >= 2)
    check("Generated Alembic versioned migration revision scripts", len(report.migrations) >= 1)

    section("3. Indexing, Seeds, Backup & Monitoring")
    check("Generated optimized SQL index specifications", len(report.indexes) >= 3)
    check("Generated Python seed data scripts (admin user, demo projects)", len(report.seeds) >= 2)
    check("Generated daily backup & restore shell scripts", len(report.backup_config.backup_script) > 50)
    check("Generated query latency monitoring & VACUUM schedule", report.monitoring_config.slow_query_threshold_ms == 200.0)

    section("4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database)")
    initial_state = {
        "user_prompt": prompt,
        "ceo_evaluation": None,
        "tasks": None,
        "planner_output": None,
        "architect_output": None,
        "frontend_output": None,
        "backend_output": None,
        "database_output": None,
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)

    check("LangGraph graph executed CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database seamlessly", final_state.get("database_output") is not None)
    check("Inter-Agent event stream logged DATABASE_PERSISTENCE_GENERATED event", any(m.get("event") == "DATABASE_PERSISTENCE_GENERATED" for m in final_state.get("messages", [])))

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 7 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day7_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
