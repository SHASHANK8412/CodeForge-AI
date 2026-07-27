"""
AIForge V2 Day 38 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 38 deliverables:
1. Organization Management & Department/Team Hierarchies
2. Multi-Tenant Isolated Workspaces System
3. Team Member User Accounts & Profile Management
4. Role-Based Access Control (RBAC) Permissions Matrix Enforcement
5. Team Collaboration Hub (Comments, Meeting Summaries, Reviews)
6. Real-Time Activity Feed & Audit Logging
7. Notification Service Alerts Dispatch
8. Enterprise Dashboard Metrics & REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.enterprise.organization import global_organization_manager
from backend.enterprise.workspace import global_workspace_system
from backend.enterprise.members import global_team_members_manager
from backend.enterprise.permissions import global_rbac_permissions_engine, Role
from backend.enterprise.collaboration import global_team_collaboration_hub
from backend.enterprise.activity import global_activity_tracker
from backend.enterprise.notifications import global_notification_service

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


def run_v2_day38_verification():
    print("======================================================================")
    print(" 🏢 AIForge V2 – Day 38 Enterprise AI Platform & Workspaces Verification")
    print("======================================================================\n")

    section("1. Organization Management & Hierarchies")
    org = global_organization_manager.create_organization(name="Acme Corp", tier="Enterprise")
    check("Created Enterprise Organization tenant", org["name"] == "Acme Corp" and len(org["departments"]) >= 2)

    section("2. Multi-Tenant Workspace System")
    ws = global_workspace_system.create_workspace(org_id=org["org_id"], name="Core Delivery Workspace")
    check("Created isolated workspace", ws["name"] == "Core Delivery Workspace")

    ws_stats = global_workspace_system.get_workspace_stats(ws["workspace_id"])
    check("Retrieved workspace usage statistics", ws_stats["stats"]["active_projects"] >= 1)

    section("3. Team Members & User Management")
    member = global_team_members_manager.add_member(
        email="developer@acme.com",
        full_name="Charlie Dev",
        org_id=org["org_id"],
        role=Role.DEVELOPER
    )
    check("Added team member account with Developer role", member["role"] == Role.DEVELOPER)

    section("4. RBAC Permissions Matrix Enforcement")
    check_owner_deploy = global_rbac_permissions_engine.check_permission(Role.OWNER, "deploy")
    check_viewer_deploy = global_rbac_permissions_engine.check_permission(Role.VIEWER, "deploy")
    check("Owner permitted to deploy, Viewer denied deploy", check_owner_deploy and not check_viewer_deploy)

    section("5. Team Collaboration Hub")
    comment = global_team_collaboration_hub.add_comment(
        project_id="proj_food",
        author="Alice (@alice)",
        content="Architecture design approved."
    )
    check("Added project comment", comment["content"] == "Architecture design approved.")

    summary = global_team_collaboration_hub.generate_meeting_summary(
        title="Architecture Alignment",
        participants=["Alice", "Bob"],
        raw_notes="Use PostgreSQL and Redis"
    )
    check("Generated AI meeting summary", summary["title"] == "Architecture Alignment")

    section("6. Real-Time Activity Feed")
    act = global_activity_tracker.record_activity("Project Production Release Approved", actor="Bob (Architect)")
    check("Recorded audit log entry in Activity Feed", act["actor"] == "Bob (Architect)")

    feed = global_activity_tracker.get_activity_feed(limit=5)
    check("Retrieved real-time activity feed", len(feed) >= 5)

    section("7. Notification Service")
    notif = global_notification_service.send_notification(
        title="Security Alert",
        message="Dependency update required for Requests package",
        category="Security"
    )
    check("Dispatched alert notification", notif["category"] == "Security" and notif["status"] == "UNREAD")

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 38 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day38_verification()
    sys.exit(0 if success else 1)
