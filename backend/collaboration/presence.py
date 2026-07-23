"""
AIForge Real-time User Presence Tracker
=======================================
Tracks active developers, current file focus, and active cursor locations in shared workspaces.
"""

import time
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.collaboration")


class PresenceTracker:
    """
    Tracks user presence and active file cursors.
    """

    def __init__(self) -> None:
        self.presence_map: Dict[str, Dict[str, Any]] = {}

    def update_presence(self, user_id: str, file_path: str, line_number: int = 1) -> Dict[str, Any]:
        info = {
            "user_id": user_id,
            "active_file": file_path,
            "line_number": line_number,
            "last_active": time.time()
        }
        self.presence_map[user_id] = info
        return info

    def get_active_presence(self) -> List[Dict[str, Any]]:
        return list(self.presence_map.values())
