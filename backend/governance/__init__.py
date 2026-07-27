"""
AIForge Governance Package
==========================
Enterprise governance, human-in-the-loop approvals, RBAC, audit logging, file history, inline comments, and reviewer management.
"""

from backend.governance.approvals import global_approval_engine, ApprovalEngine
from backend.governance.roles import global_rbac_manager, RBACManager
from backend.governance.audit import global_audit_logger, AuditLogger
from backend.governance.history import global_change_history, ChangeHistoryManager
from backend.governance.comments import global_review_comments, ReviewCommentsManager
from backend.governance.reviewers import global_reviewer_manager, ReviewerManager
from backend.governance.reports import global_governance_reports, GovernanceReports

__all__ = [
    "global_approval_engine", "ApprovalEngine",
    "global_rbac_manager", "RBACManager",
    "global_audit_logger", "AuditLogger",
    "global_change_history", "ChangeHistoryManager",
    "global_review_comments", "ReviewCommentsManager",
    "global_reviewer_manager", "ReviewerManager",
    "global_governance_reports", "GovernanceReports"
]
