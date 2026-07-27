"""
AIForge V2 Day 28 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 28 deliverables:
1. Human-in-the-Loop Approval Workflows (Checkpoints: Requirements, Architecture, Generated Code, Deployment)
2. Role-Based Access Control (RBAC Matrix & Permission Enforcement)
3. Immutable Audit Logging (Action Tracking, Decisions, File Diffs)
4. Version History Tracking, Diff Generation & Rollback Support
5. Code Review Comments & Discussion Threads
6. Governance Dashboard, SLA Metrics & Compliance Reporting
7. Healthcare Management System Workflow Approval Simulation
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.governance.approvals import global_approval_engine
from backend.governance.roles import global_rbac_manager
from backend.governance.audit import global_audit_logger
from backend.governance.history import global_change_history
from backend.governance.comments import global_review_comments
from backend.governance.reviewers import global_reviewer_manager
from backend.governance.reports import global_governance_reports

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


def run_v2_day28_verification():
    print("======================================================================")
    print(" 🛡️ AIForge V2 – Day 28 Governance & Human-in-the-Loop Verification")
    print("======================================================================\n")

    project_id = "proj_healthcare_e2e"
    project_name = "Healthcare Management System"

    section("1. Role-Based Access Control (RBAC)")
    roles = global_rbac_manager.get_all_roles()
    check("Loaded RBAC roles matrix", len(roles) >= 6)

    admin_can_approve = global_rbac_manager.check_permission("Administrator", "approve_deployment")
    viewer_cannot_approve = not global_rbac_manager.check_permission("Viewer", "approve_deployment")
    check("Verified RBAC permissions (Admin can approve, Viewer blocked)", admin_can_approve and viewer_cannot_approve)

    assigned = global_rbac_manager.assign_user_role("dr_smith", "Reviewer")
    check("Assigned custom user role in RBAC system", assigned["role"] == "Reviewer")

    section("2. Architecture Approval Checkpoint")
    arch_req = global_approval_engine.request_approval(
        project_id=project_id,
        project_name=project_name,
        checkpoint="Architecture",
        title="Microservices Architecture Blueprint",
        description="Review system blueprint for HIPAA patient data privacy and DB schemas."
    )
    check("Triggered Architecture approval request checkpoint", arch_req["status"] == "Pending")

    pending_list = global_approval_engine.get_pending_approvals(project_id)
    check("Retrieved pending approval requests for Healthcare System", len(pending_list) >= 1)

    # Approve architecture
    arch_res = global_approval_engine.respond_to_approval(
        request_id=arch_req["request_id"],
        decision="Approved",
        reviewer="Dr. Sarah Connor (Lead Architect)",
        comments="Architecture meets HIPAA security requirements."
    )
    check("Human reviewer approved Architecture checkpoint", arch_res["status"] == "Approved")
    check("Verified Architecture checkpoint is approved", global_approval_engine.is_checkpoint_approved(project_id, "Architecture"))

    section("3. Development & Audit Logging")
    global_audit_logger.log_event(
        user_or_agent="Backend Agent",
        role="Developer",
        action="Generated Healthcare Patient Management API",
        target_entity="src/api/patient_service.py",
        project_id=project_id,
        version="v1.0.0",
        files_changed=["src/api/patient_service.py", "src/models/patient.py"],
        decision="Completed"
    )

    audit_logs = global_audit_logger.get_logs(project_id=project_id)
    check("Recorded development action in immutable Audit Log", len(audit_logs) >= 1)

    section("4. Change History & Rollback Support")
    v1 = global_change_history.record_version(
        project_id=project_id,
        version_id="v1.0.0",
        author="Backend Agent",
        summary="Initial Healthcare API & Patient Models",
        files_affected=["src/api/patient_service.py"],
        diff="+ def get_patient(id): return patient_db.find(id)"
    )
    check("Recorded version history with code diff", v1["version_id"] == "v1.0.0")

    history = global_change_history.get_project_history(project_id)
    check("Retrieved project change history", len(history) >= 1)

    rollback_res = global_change_history.rollback_to_version(project_id, "v1.0.0")
    check("Executed version rollback to v1.0.0", rollback_res["status"] == "success")

    section("5. Review Comments & Code Feedback")
    comment = global_review_comments.add_comment(
        project_id=project_id,
        author="Alex Mercer",
        author_role="Security Lead",
        text="Enforce AES-256 field level encryption for Patient SSN.",
        file_path="src/models/patient.py",
        line_number=24,
        comment_type="Security Review"
    )
    check("Added inline review comment to file", comment["status"] == "open")

    resolved = global_review_comments.resolve_comment(comment["comment_id"], resolver="Lead Developer")
    check("Resolved inline review comment thread", resolved["status"] == "resolved")

    section("6. Deployment Checkpoint & Governance Dashboard")
    deploy_req = global_approval_engine.request_approval(
        project_id=project_id,
        project_name=project_name,
        checkpoint="Deployment",
        title="Production Deployment Release v1.0",
        description="Deploy Healthcare Management System to AWS EKS Cluster."
    )
    check("Triggered Production Deployment approval request", deploy_req["status"] == "Pending")
    check("Deployment blocked until final human approval", not global_approval_engine.is_checkpoint_approved(project_id, "Deployment"))

    gov_dashboard = global_governance_reports.get_governance_dashboard()
    check("Compiled Governance Dashboard with compliance score", "compliance_score_percentage" in gov_dashboard)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 28 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day28_verification()
    sys.exit(0 if success else 1)
