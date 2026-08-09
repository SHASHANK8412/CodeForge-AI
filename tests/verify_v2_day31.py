"""
AIForge V2 Day 31 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 31 deliverables:
1. Human Review Agent & Action Risk Evaluation (10 High-Risk Action Types)
2. Approval Workflows & Workflow State Pausing/Resumption (Pending -> Approved/Rejected)
3. Human Feedback Conversion into Actionable Engineering Tasks
4. Ambiguity Clarification Engine & Q&A Dialog Generation
5. Immutable Approval Audit Trail
6. Approval Dashboard Metrics & REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.human_review_agent import global_human_review_agent
from backend.approvals.approval_manager import global_approval_manager
from backend.approvals.approval_store import global_approval_store

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


def run_v2_day31_verification():
    print("======================================================================")
    print(" 🛡️ AIForge V2 – Day 31 Human-in-the-Loop (HITL) Verification")
    print("======================================================================\n")

    section("1. Action Risk Evaluation & Approval Triggers")
    risk_eval = global_human_review_agent.evaluate_action_risk(
        action_title="Execute Database Migration & Drop Column",
        affected_files=["backend/models/user.py", "migrations/002.sql"],
        description="Refactoring user database schema."
    )
    check("Evaluated action risk as High & flagged approval required", risk_eval["risk"] == "High" and risk_eval["approval_required"])

    section("2. Approval Request Creation & Workflow Pausing")
    appr_req = global_approval_manager.create_approval_request(
        title="Deploy Backend to Production",
        reason="Release v1.5 build passing unit tests",
        affected_files=["backend/main.py", "Dockerfile"],
        risk="High",
        estimated_time="4 min"
    )
    check("Created approval request & paused workflow execution", appr_req["status"] == "Pending" and appr_req["workflow_state"] == "PAUSED")

    pending = global_approval_store.get_all_approvals("Pending")
    check("Retrieved pending approval requests", len(pending) >= 1)

    section("3. Approval Responding & Workflow Resumption")
    appr_res = global_approval_manager.respond_to_request(
        approval_id=appr_req["id"],
        decision="Approve",
        reviewer_note="Approved production release v1.5"
    )
    check("Approved request & resumed workflow execution", appr_res["status"] == "Approved" and appr_res["workflow_state"] == "RESUMED")

    section("4. Human Feedback System & Task Conversion")
    feedback_text = "Improve UI colors to dark mode\nUse PostgreSQL database\nAdd JWT refresh tokens"
    feedback_result = global_approval_manager.submit_user_feedback(feedback_text, project_name="Food Delivery")
    check("Converted human feedback into 3 engineering tasks", feedback_result["created_tasks_count"] == 3)

    all_feedback = global_approval_store.get_all_feedback()
    check("Stored human feedback in ApprovalStore", len(all_feedback) >= 1)

    section("5. Ambiguity Clarification Engine")
    clarif_item = global_approval_manager.check_ambiguity_and_clarify("Create an ecommerce app")
    check("Generated clarification questions for ambiguous prompt", clarif_item["status"] == "Awaiting User Input" and len(clarif_item["questions"]) >= 2)

    ans = global_approval_store.answer_clarification(clarif_item["id"], {"Question 1": "Stripe", "Question 2": "PostgreSQL"})
    check("Answered clarification questions", ans["status"] == "Answered")

    section("6. Approval Dashboard & Audit Trail")
    dashboard = global_approval_manager.get_approval_dashboard()
    check("Compiled Approval Dashboard data", dashboard["summary"]["total_requests"] >= 1 and len(dashboard["audit_trail"]) >= 2)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 31 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day31_verification()
    sys.exit(0 if success else 1)
