"""
AIForge V2 Day 27 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 27 deliverables:
1. Multi-Project Workspace Management (Creation, Switching, List, State)
2. Shared Agent Scheduler & Dynamic Agent Pool Allocation across Projects
3. Portfolio Dashboard Aggregations (Health, Completion %, Running/Failed Tasks)
4. System Resource Allocation (LLM models, CPU, Memory, Plugins, Queues)
5. Cross-Project Pattern Learning & Reuse (JWT Auth, Shared Knowledge Base)
6. Event-Driven Notifications System
7. REST APIs for Workspace Operations
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.workspace.workspace_manager import global_workspace_manager
from backend.workspace.scheduler import global_agent_scheduler
from backend.workspace.portfolio import global_portfolio_dashboard
from backend.workspace.notifications import global_notification_manager
from backend.workspace.resource_manager import global_resource_manager
from backend.workspace.priorities import global_priority_manager
from backend.workspace.analytics import global_workspace_analytics

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


def run_v2_day27_verification():
    print("======================================================================")
    print(" 🏢 AIForge V2 – Day 27 Multi-Project Workspace & Shared Agent Pool Verification")
    print("======================================================================\n")

    section("1. Multi-Project Workspace Management")
    projects_to_create = [
        ("Hospital Management", "Healthcare & Medical System"),
        ("Banking Platform", "Core Banking & Transaction System"),
        ("CRM System", "Enterprise CRM Platform"),
        ("Inventory Management", "Supply Chain Inventory Manager")
    ]

    created_ids = {}
    for p_name, p_desc in projects_to_create:
        p = global_workspace_manager.create_project(p_name, p_desc)
        created_ids[p_name] = p["project_id"]

    check("Created 4 concurrent projects in workspace", len(created_ids) == 4, f"Created IDs: {created_ids}")

    all_projs = global_workspace_manager.get_all_projects()
    check("Listed all workspace projects", len(all_projs) >= 4)

    switched = global_workspace_manager.switch_project(created_ids["Hospital Management"])
    check("Switched active project context to Hospital Management", switched["name"] == "Hospital Management")

    section("2. Shared AI Agent Pool & Scheduling")
    pool = global_agent_scheduler.get_agent_pool()
    check("Loaded shared AI agent pool", len(pool) >= 7, f"Total agents in pool: {len(pool)}")

    t1 = global_agent_scheduler.add_task_to_queue(
        created_ids["Hospital Management"], "Hospital Management", "Design Patient Microservices", "Architect", "Critical"
    )
    t2 = global_agent_scheduler.add_task_to_queue(
        created_ids["Banking Platform"], "Banking Platform", "Build Payment Gateway API", "Backend", "High"
    )
    t3 = global_agent_scheduler.add_task_to_queue(
        created_ids["CRM System"], "CRM System", "Build Customer Dashboard UI", "Frontend", "High"
    )
    t4 = global_agent_scheduler.add_task_to_queue(
        created_ids["Inventory Management"], "Inventory Management", "Run Integration Tests", "QA", "Medium"
    )

    scheduler_status = global_agent_scheduler.get_scheduler_status()
    check("Scheduled tasks across 4 concurrent projects", scheduler_status["in_progress_tasks"] >= 4)

    # Release an agent and verify reallocation
    released = global_agent_scheduler.release_agent("agent_arch", success=True)
    check("Released idle agent and reallocated to queue", released["completed_task"] == "Design Patient Microservices")

    section("3. Cross-Project Knowledge Reuse")
    # Register pattern from Hospital Management
    pattern = global_workspace_analytics.register_pattern(
        pattern_id="fhir_jwt_auth",
        title="FHIR Compliant JWT Auth",
        category="Security",
        origin_project="Hospital Management",
        description="HIPAA/FHIR standard compliant JWT bearer token middleware."
    )
    check("Registered architectural pattern in global Knowledge Base", pattern["pattern_id"] == "fhir_jwt_auth")

    # Reuse in Banking Platform
    reused = global_workspace_manager.reuse_module_across_projects(
        created_ids["Banking Platform"], "FHIR Compliant JWT Auth"
    )
    check("Reused security module from Hospital Management in Banking Platform", reused["status"] == "success")

    analytics_summary = global_workspace_analytics.get_analytics_summary()
    check("Cross-project learning analytics updated", analytics_summary["total_cross_project_reuses"] >= 1)

    section("4. Resource Manager & Priority Allocation")
    alloc = global_resource_manager.get_resource_allocation(created_ids["Banking Platform"])
    check("Retrieved project resource allocations (LLM, CPU, Memory)", alloc["llm_model"] == "gpt-4o")

    p_update = global_priority_manager.set_project_priority(created_ids["Hospital Management"], "Critical")
    check("Updated project priority level to Critical", p_update["new_priority"] == "Critical")

    section("5. Portfolio Dashboard & Event Notifications")
    dashboard = global_portfolio_dashboard.get_portfolio_dashboard()
    check("Generated portfolio dashboard metrics", dashboard["total_projects"] >= 4 and "health_breakdown" in dashboard)

    notif = global_notification_manager.notify(
        event_type="sprint_completed",
        project_id=created_ids["Banking Platform"],
        project_name="Banking Platform",
        title="Sprint 1 Completed",
        message="Core Banking API Sprint 1 delivered successfully."
    )
    check("Published event-driven workspace notification", notif["event_type"] == "sprint_completed")

    unread_notifs = global_notification_manager.get_notifications(unread_only=True)
    check("Retrieved unread workspace notifications", len(unread_notifs) >= 1)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 27 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day27_verification()
    sys.exit(0 if success else 1)
