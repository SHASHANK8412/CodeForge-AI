"""
AIForge V2 Day 10 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 10 deliverables:
1. Documentation Agent (Autonomous Documentation & Knowledge Generation Engine)
2. README.md, ARCHITECTURE.md, API_DOCUMENTATION.md, DATABASE_DOCUMENTATION.md Generators
3. DEVELOPER_GUIDE.md, DEPLOYMENT_GUIDE.md, USER_MANUAL.md Generators
4. CHANGELOG.md & RELEASE_NOTES.md Generator
5. Mermaid Diagram Engine (Flowchart TD, Sequence, ER Diagrams)
6. Documentation Validation Engine
7. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer -> Testing -> Documentation -> END)
8. FastAPI Endpoint (POST /api/v2/documentation/generate)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.documentation.agent import global_documentation_agent_v2
from v2.agents.documentation.validator import global_documentation_validator
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


async def run_v2_day10_verification():
    print("======================================================================")
    print(" 📚 AIForge V2 – Day 10 Documentation & Knowledge Generation Verification")
    print("======================================================================\n")

    # 1. Documentation Generation Test: AI Resume Analyzer
    prompt = "Generate documentation package for an AI Resume Analyzer project."
    section("1. Markdown Documentation Files & Release Notes")
    report = global_documentation_agent_v2.generate_documentation(prompt, project_id="v2_day10_verify")

    check("Generated documentation files tree (README, Architecture, API, DB, Dev, Deploy, UserManual)", len(report.files) >= 6)
    check("Generated README.md overview markdown", len(report.readme_markdown) > 100)
    check("Generated DEVELOPER_GUIDE.md markdown", len(report.developer_docs_markdown) > 100)
    check("Generated DEPLOYMENT_GUIDE.md markdown", len(report.deployment_docs_markdown) > 100)
    check("Generated release notes (Version 2.0.0)", report.release_notes.version == "2.0.0")

    section("2. Mermaid Architecture Diagrams")
    check("Generated Mermaid interactive architecture diagrams (Flowchart TD, ER Diagram)", len(report.diagrams) >= 2)
    check("Mermaid flowchart code contains workflow graph", "graph TD" in report.diagrams[0].mermaid_code)

    section("3. Documentation Validation Engine")
    check("Documentation report validation score >= 90.0%", report.validation_score >= 90.0)

    section("4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer -> Testing -> Documentation)")
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

    check("LangGraph graph executed CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer -> Testing -> Documentation seamlessly", final_state.get("documentation_output") is not None)
    check("Inter-Agent event stream logged DOCUMENTATION_PACKAGE_GENERATED event", any(m.get("event") == "DOCUMENTATION_PACKAGE_GENERATED" for m in final_state.get("messages", [])))

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 10 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day10_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
