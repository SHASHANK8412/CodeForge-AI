"""
AIForge Notification Service
============================
Dispatches in-app and webhook alerts for critical workspace triggers (Project Complete, Deployment Failed, Approval Required, Security Alerts).
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.enterprise.notifications")


class NotificationService:
    """
    Manages user notifications and workspace alert triggers.
    """

    def __init__(self) -> None:
        self.notifications: List[Dict[str, Any]] = [
            {
                "notification_id": "notif_101",
                "title": "Approval Required",
                "message": "Production deployment of Food Delivery API requires human review.",
                "category": "Approval",
                "status": "UNREAD",
                "timestamp": time.time() - 1800
            },
            {
                "notification_id": "notif_102",
                "title": "Deployment Completed",
                "message": "Release v2.1.0 deployed successfully to Production environment.",
                "category": "Deployment",
                "status": "READ",
                "timestamp": time.time() - 3600
            }
        ]

    def send_notification(self, title: str, message: str, category: str = "General") -> Dict[str, Any]:
        entry = {
            "notification_id": f"notif_{int(time.time() * 1000)}",
            "title": title,
            "message": message,
            "category": category,
            "status": "UNREAD",
            "timestamp": time.time()
        }
        self.notifications.insert(0, entry)
        _logger.info(f"NotificationService: Dispatched notification '{title}' ({category})")
        return entry

    def get_notifications(self, unread_only: bool = False) -> List[Dict[str, Any]]:
        if unread_only:
            return [n for n in self.notifications if n["status"] == "UNREAD"]
        return list(self.notifications)


global_notification_service = NotificationService()
