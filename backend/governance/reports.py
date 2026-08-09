"""
AIForge Governance Dashboard & Reports
======================================
Compiles governance dashboards, audit timelines, compliance metrics, approval statistics, and enterprise reports.
"""

import time
from typing import Dict, Any, List
from backend.governance.approvals import global_approval_engine
from backend.governance.audit import global_audit_logger
from backend.governance.roles import global_rbac_manager
from backend.governance.history import global_change_history
from backend.governance.reviewers import global_reviewer_manager


class GovernanceReports:
    """
    Generates summary reports and governance dashboard views.
    """

    def get_governance_dashboard(self) -> Dict[str, Any]:
        pending_approvals = global_approval_engine.get_pending_approvals()
        all_requests = global_approval_engine.get_all_requests()
        audit_logs = global_audit_logger.get_logs(limit=20)
        reviewers = global_reviewer_manager.get_all_reviewers()

        total_reqs = len(all_requests)
        approved_count = len([r for r in all_requests if r["status"] == "Approved"])
        rejected_count = len([r for r in all_requests if r["status"] == "Rejected"])
        pending_count = len(pending_approvals)

        compliance_score = round((approved_count / max(1, total_reqs)) * 100, 1)

        return {
            "timestamp": time.time(),
            "compliance_score_percentage": compliance_score,
            "approval_statistics": {
                "total_requests": total_reqs,
                "approved": approved_count,
                "rejected": rejected_count,
                "pending": pending_count
            },
            "pending_approvals": pending_approvals,
            "active_reviewers": reviewers,
            "audit_timeline": audit_logs,
            "recent_changes": global_change_history.get_project_history("proj_hospital")[:5],
            "rbac_roles": global_rbac_manager.get_all_roles()
        }


global_governance_reports = GovernanceReports()
