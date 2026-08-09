"""
AIForge Enterprise Package
==========================
Organization Management, Workspace System, Team Members, RBAC Permissions, Team Collaboration Hub, Real-time Activity Feed, and Notification Service.
"""

from backend.enterprise.organization import OrganizationManager, global_organization_manager
from backend.enterprise.workspace import WorkspaceSystem, global_workspace_system
from backend.enterprise.members import TeamMembersManager, global_team_members_manager
from backend.enterprise.permissions import RBACPermissionsEngine, Role, global_rbac_permissions_engine
from backend.enterprise.collaboration import TeamCollaborationHub, global_team_collaboration_hub
from backend.enterprise.activity import ActivityTracker, global_activity_tracker
from backend.enterprise.notifications import NotificationService, global_notification_service

__all__ = [
    "OrganizationManager", "global_organization_manager",
    "WorkspaceSystem", "global_workspace_system",
    "TeamMembersManager", "global_team_members_manager",
    "RBACPermissionsEngine", "Role", "global_rbac_permissions_engine",
    "TeamCollaborationHub", "global_team_collaboration_hub",
    "ActivityTracker", "global_activity_tracker",
    "NotificationService", "global_notification_service"
]
