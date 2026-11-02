"""
AIForge Notification Manager
============================
Event-driven notification engine alerting users and team members on critical milestone events across projects.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.workspace.notifications")


class NotificationManager:
    """
    Manages cross-project notification queue and user alerts.
    """

    def __init__(self) -> None:
        self.notifications: List[Dict[str, Any]] = [
            {
                "id": "notif_1",
                "event_type": "sprint_completed",
                "project_id": "proj_ecommerce",
                "project_name": "Ecommerce Platform",
                "title": "Sprint 3 Completed",
                "message": "Sprint 3 successfully completed. 14 user stories verified.",
                "timestamp": time.time() - 3600,
                "read": True
            },
            {
                "id": "notif_2",
                "event_type": "deployment_finished",
                "project_id": "proj_airesume",
                "project_name": "AI Resume Analyzer",
                "title": "Production Deployment Successful",
                "message": "Version 1.2 deployed to Production. All smoke tests passing.",
                "timestamp": time.time() - 1800,
                "read": False
            }
        ]

    def notify(
        self,
        event_type: str,
        project_id: str,
        project_name: str,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Types: sprint_completed, deployment_finished, debugging_failed, documentation_generated, human_approval_required
        """
        notif_id = f"notif_{int(time.time() * 1000)}"
        notification = {
            "id": notif_id,
            "event_type": event_type,
            "project_id": project_id,
            "project_name": project_name,
            "title": title,
            "message": message,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "read": False
        }
        self.notifications.insert(0, notification)
        _logger.info(f"NotificationManager: [{event_type.upper()}] Project: '{project_name}' - {title}")
        return notification

    def get_notifications(self, project_id: Optional[str] = None, unread_only: bool = False) -> List[Dict[str, Any]]:
        result = self.notifications
        if project_id:
            result = [n for n in result if n["project_id"] == project_id]
        if unread_only:
            result = [n for n in result if not n["read"]]
        return result

    def mark_as_read(self, notification_id: str) -> bool:
        for n in self.notifications:
            if n["id"] == notification_id:
                n["read"] = True
                return True
        return False


global_notification_manager = NotificationManager()
