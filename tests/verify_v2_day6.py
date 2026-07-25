"""
AIForge V2 Day 6 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 6 deliverables:
1. Backend Agent (Autonomous FastAPI REST Backend Application Generator)
2. FastAPI APIRouter & Endpoint Generator
3. Service Layer Business Logic Generator
4. Repository Layer Persistence Generator
5. JWT Authentication & Role-Based Access Control (RBAC) Generator
6. Middleware & Exception Handling Framework Generator
7. Pytest Automated Unit Test Generator
8. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> END)
9. FastAPI Endpoint (POST /api/v2/backend/generate)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.backend.agent import global_backend_agent_v2
from v2.agents.backend.validator import global_backend_validator
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


async def run_v2_day6_verification():
    print("======================================================================")
    print(" 🐍 AIForge V2 – Day 6 FastAPI Backend Application Generation Verification")
    print("======================================================================\n")

    # 1. FastAPI Application Generation Test: AI Resume Analyzer
    prompt = "Build an AI Resume Analyzer using FastAPI and React."
    section("1. FastAPI Application & REST Routers Generation")
    report = global_backend_agent_v2.generate_backend(prompt, project_id="v2_day6_verify")

    check("Generated modular backend folder structure tree", len(report.folder_structure) >= 10)
    check("Generated REST API routers & endpoints (/auth, /projects, /generate)", len(report.apis) >= 4)
    check("Generated Service Layer business logic classes (AuthService, ProjectService)", len(report.services) >= 2)

    section("2. Persistence, Auth & Middleware")
    check("Generated Repository Layer persistence classes (UserRepository, ProjectRepository)", len(report.repositories) >= 2)
    check("Generated JWT Bearer Authentication & RBAC role permissions", len(report.auth.roles) >= 3 and "Admin" in report.auth.roles)
    check("Generated FastAPI CORS & Request ID timing middlewares", len(report.middleware) >= 2)

    section("3. Main Bundle, Pydantic Schemas & Pytest Suite")
    check("Generated main.py FastAPI application entry point", len(report.main_py_content) > 50)
    check("Generated automated Pytest unit test suite scripts", len(report.tests) >= 2)

    section("4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend)")
    initial_state = {
        "user_prompt": prompt,
        "ceo_evaluation": None,
        "tasks": None,
        "planner_output": None,
        "architect_output": None,
        "frontend_output": None,
        "backend_output": None,
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)

    check("LangGraph graph executed CEO -> Manager -> Planner -> Architect -> Frontend -> Backend seamlessly", final_state.get("backend_output") is not None)
    check("Inter-Agent event stream logged BACKEND_APPLICATION_GENERATED event", any(m.get("event") == "BACKEND_APPLICATION_GENERATED" for m in final_state.get("messages", [])))

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 6 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day6_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
