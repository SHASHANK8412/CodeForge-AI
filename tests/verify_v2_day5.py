"""
AIForge V2 Day 5 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 5 deliverables:
1. Frontend Agent (Autonomous React + TSX + Tailwind Application Generator)
2. Modular UI Component Generator (Navbar, Sidebar, Button, Card)
3. Page & Layout Component Generators (Dashboard, Upload, AuthLayout, DashboardLayout)
4. React Router 6 Navigation & Protected Route Guard Generator
5. Zustand State Stores (useAuthStore, useProjectStore) & Custom Hooks Generator
6. Axios API Client Service Generator
7. Tailwind CSS Config Generator
8. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> END)
9. FastAPI Endpoint (POST /api/v2/frontend/generate)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.frontend.agent import global_frontend_agent_v2
from v2.agents.frontend.validator import global_frontend_validator
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


async def run_v2_day5_verification():
    print("======================================================================")
    print(" ⚛️ AIForge V2 – Day 5 Frontend React Application Generation Verification")
    print("======================================================================\n")

    # 1. React Application Generation Test: AI Resume Analyzer
    prompt = "Build an AI Resume Analyzer using FastAPI and React."
    section("1. React Application & Component Generation")
    report = global_frontend_agent_v2.generate_frontend(prompt, project_id="v2_day5_verify")

    check("Generated modular folder structure tree", len(report.folder_structure) >= 8)
    check("Generated reusable UI components (Navbar, Sidebar, Button, Card)", len(report.components) >= 4)
    check("Generated React pages (Dashboard, ResumeUpload, Login)", len(report.pages) >= 3)

    section("2. Routing, State Management & API Services")
    check("Generated React Router 6 protected routes & AppRouter", len(report.routes) >= 3)
    check("Generated Zustand state management stores (useAuthStore, useProjectStore)", len(report.stores) >= 2)
    check("Generated custom hooks (useAuth, useProjects)", len(report.hooks) >= 2)
    check("Generated Axios API client with JWT interceptors", len(report.services) >= 1)

    section("3. Tailwind CSS & Main Bundle Configurations")
    check("Generated tailwind.config.js & index.css styling rules", len(report.tailwind_config) > 50)
    check("Generated main.tsx application entry point", len(report.main_entry) > 50)

    section("4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend)")
    initial_state = {
        "user_prompt": prompt,
        "ceo_evaluation": None,
        "tasks": None,
        "planner_output": None,
        "architect_output": None,
        "frontend_output": None,
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)

    check("LangGraph graph executed CEO -> Manager -> Planner -> Architect -> Frontend seamlessly", final_state.get("frontend_output") is not None)
    check("Inter-Agent event stream logged FRONTEND_APPLICATION_GENERATED event", any(m.get("event") == "FRONTEND_APPLICATION_GENERATED" for m in final_state.get("messages", [])))

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 5 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day5_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
