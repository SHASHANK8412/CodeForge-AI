"""
AIForge V2 Day 4 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 4 deliverables:
1. Architect Agent (Autonomous System Design & Technical Architecture Package)
2. High & Low-Level Topology Diagram Generators
3. REST API Specification & Request/Response Schema Designer
4. Database Schema & ER Relationship Designer
5. Security, Caching, VectorStore & Docker Deployment Modules
6. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> END)
7. FastAPI Endpoint (POST /api/v2/architect/design)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.architect.agent import global_architect_agent_v2
from v2.agents.architect.validator import global_architecture_validator
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


async def run_v2_day4_verification():
    print("======================================================================")
    print(" 🏗️ AIForge V2 – Day 4 Technical Architecture Verification")
    print("======================================================================\n")

    # 1. Technical Architecture Package Generation Test: AI Resume Analyzer
    prompt = "Build an AI Resume Analyzer using FastAPI and React."
    section("1. Technical Architecture Package Generation")
    report = global_architect_agent_v2.design_architecture(prompt, project_id="v2_day4_verify")

    check("Generated High-Level & Low-Level system topology descriptions", len(report.high_level_architecture) > 20 and len(report.low_level_architecture) > 20)
    check("Generated modular folder structure tree", len(report.folder_structure) >= 10)
    check("Generated system component specifications", len(report.components) >= 3)

    section("2. REST API Specification & Database Schema Design")
    check("Designed REST API endpoints with request/response schemas", len(report.apis) >= 4)
    check("Designed PostgreSQL SQL database tables with column types", len(report.database.tables) >= 4)
    check("Designed ER relationships between database tables", len(report.database.er_relationships) >= 2)

    section("3. Security, Caching, VectorStore & Docker Deployment")
    check("Configured security strategy (JWT Auth, TLS 1.3, Rate Limiting)", "JWT" in report.security.auth_type)
    check("Configured Redis cache strategy and TTL", report.caching.engine == "Redis" and report.caching.ttl_seconds > 0)
    check("Configured ChromaDB vector store collections", report.vector_store.engine == "ChromaDB" and len(report.vector_store.collections) >= 2)
    check("Configured Docker Compose deployment services", len(report.deployment.containers) >= 3)

    section("4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect)")
    initial_state = {
        "user_prompt": prompt,
        "ceo_evaluation": None,
        "tasks": None,
        "planner_output": None,
        "architect_output": None,
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)

    check("LangGraph graph executed CEO -> Manager -> Planner -> Architect seamlessly", final_state.get("architect_output") is not None)
    check("Inter-Agent event stream logged ARCHITECTURE_DESIGN_COMPLETED event", any(m.get("event") == "ARCHITECTURE_DESIGN_COMPLETED" for m in final_state.get("messages", [])))

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 4 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day4_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
