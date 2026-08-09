"""
AIForge Real-Time Activity Feed Tracker
=======================================
Tracks organization and workspace audit logs and chronological real-time activity events.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.enterprise.activity")


class ActivityTracker:
    """
    Maintains real-time activity feed logs for organizations and projects.
    """

    def __init__(self) -> None:
        self.activities: List[Dict[str, Any]] = [
            {"id": "act_1", "timestamp": time.time() - 3600, "time_str": "09:15", "event": "Project Created", "actor": "Alice Smith"},
            {"id": "act_2", "timestamp": time.time() - 3300, "time_str": "09:20", "event": "Planner Completed", "actor": "Planner Agent"},
            {"id": "act_3", "timestamp": time.time() - 3000, "time_str": "09:25", "event": "Architecture Approved", "actor": "Bob Jones"},
            {"id": "act_4", "timestamp": time.time() - 2100, "time_str": "09:40", "event": "Backend Code Generation Started", "actor": "Backend Agent"},
            {"id": "act_5", "timestamp": time.time() - 300, "time_str": "10:10", "event": "Deployment Completed", "actor": "DevOps Agent"}
        ]

    def record_activity(self, event: str, actor: str = "User / AI Agent") -> Dict[str, Any]:
        entry = {
            "id": f"act_{int(time.time() * 1000)}",
            "timestamp": time.time(),
            "time_str": time.strftime("%H:%M"),
            "event": event,
            "actor": actor
        }
        self.activities.insert(0, entry)
        _logger.info(f"ActivityTracker: [{entry['time_str']}] {actor} - {event}")
        return entry

    def get_activity_feed(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.activities[:limit]


global_activity_tracker = ActivityTracker()
