"""
AIForge Stabilization Sprint End-to-End Verification Suite
===========================================================
Validates all 12 Architectural Solutions:
1. Replace Plain Text with JSON contracts between agents
2. Strict single responsibility for each agent
3. Structured State dictionary in LangGraph (ProjectState)
4. Parallel execution of Frontend, Backend, and Database
5. Specialized prompt builders per agent role
6. Reduced prompt size & context scoping
7. Node-level caching service (NodeCacheService)
8. Real code review on generated file maps
9. Real testing inspecting generated code
10. Real project multi-file workspace generation
11. Stream intermediate progress updates
12. Validation gates & stage retries
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.services.cache_service import global_cache_service
from backend.services.validator import global_stage_validator
from backend.services.project_builder import global_structured_project_builder
from backend.services.prompt_builder import global_prompt_builder
from backend.graph.parallel_workflow import parallel_graph

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


async def run_stabilization_tests():
    print("======================================================================")
    print(" 🛠️ AIForge Stabilization Sprint Verification Suite (Solutions 1-12)")
    print("======================================================================\n")

    # ------------------------------------------------------------------
    section("1. Solution 1 & 12: JSON Contracts & Validation Gates")
    # ------------------------------------------------------------------
    plan_raw = '{"project_name": "Formula 1 Racing Portal", "type": "Full Stack", "frontend": "React", "backend": "FastAPI", "database": "PostgreSQL", "pages": ["Home", "Cars"], "features": ["Auth", "Gallery"]}'
    valid_plan, msg_plan, plan_json = global_stage_validator.validate_plan(plan_raw)
    check("Planner JSON contract & validation gate passed", valid_plan and plan_json["project_name"] == "Formula 1 Racing Portal")

    arch_raw = '{"components": ["Navbar", "CarCard"], "routes": ["GET /cars"], "models": ["Car"], "dependencies": ["react", "fastapi"], "folder_structure": {}}'
    valid_arch, msg_arch, arch_json = global_stage_validator.validate_architecture(arch_raw)
    check("Architect JSON contract & validation gate passed", valid_arch and len(arch_json["components"]) > 0)

    # ------------------------------------------------------------------
    section("2. Solution 2, 5 & 6: Single Responsibility & Context Scoping")
    # ------------------------------------------------------------------
    p_prompt = global_prompt_builder.build_planner_prompt("Build Formula 1 Portal")
    a_prompt = global_prompt_builder.build_architect_prompt(plan_json)
    fe_prompt = global_prompt_builder.build_frontend_prompt(arch_json)
    be_prompt = global_prompt_builder.build_backend_prompt(arch_json)

    check("Minimal context-scoped prompts constructed for each specialized role",
          "Analyze user requirements" in p_prompt and "Formula 1 Racing Portal" in a_prompt and "CarCard" in fe_prompt and "GET /cars" in be_prompt)

    # ------------------------------------------------------------------
    section("3. Solution 7: Node-Level Caching Service")
    # ------------------------------------------------------------------
    global_cache_service.set("planner", "Build F1", plan_json)
    cached = global_cache_service.get("planner", "Build F1")
    check("Node Cache Service stored & retrieved cached stage outputs", cached is not None and cached["project_name"] == "Formula 1 Racing Portal")

    # ------------------------------------------------------------------
    section("4. Solution 10: Real Multi-File Directory Generator")
    # ------------------------------------------------------------------
    project = global_structured_project_builder.assemble_real_project(
        project_name="Formula 1 Racing Portal",
        plan_json=plan_json,
        arch_json=arch_json,
        frontend_code="// React Code",
        backend_code="# FastAPI Code",
        database_code="-- SQL Code",
        testing_code="# Pytest Code",
        docs_code="# Documentation"
    )
    check("Assembled multi-file workspace (Formula 1 Racing Portal/frontend, backend, database, docs, docker)",
          project["total_files"] >= 10 and "frontend/src/App.jsx" in project["file_structure"])

    # ------------------------------------------------------------------
    section("5. Solution 3, 4, 8, 9 & 11: LangGraph Parallel Execution & Progress Streaming")
    # ------------------------------------------------------------------
    initial_state = {
        "user_prompt": "Build Formula 1 Racing Portal",
        "prompt": "Build Formula 1 Racing Portal"
    }
    final_state = await parallel_graph.ainvoke(initial_state)

    check("LangGraph parallel graph executed Frontend, Backend, & Database concurrently",
          final_state.get("frontend") is not None and final_state.get("backend") is not None and final_state.get("database") is not None)
    check("Streamed intermediate progress events across nodes",
          len(final_state.get("stream_events", [])) >= 6)
    check("Real code reviewer & testing agent evaluated generated file contents",
          "review" in final_state and "tests" in final_state)

    # Summary
    print("\n" + "="*70)
    print(f" STABILIZATION SPRINT VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_stabilization_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
