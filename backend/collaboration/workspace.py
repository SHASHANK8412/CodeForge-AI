"""
AIForge Shared Cloud Workspace
==============================
Enables multi-user real-time collaboration across developers and AI agents.
Synchronizes project architecture, active tasks, requirements, generated code, and decisions.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.collaboration")


class SharedAIWorkspace:
    """
    Shared multi-user collaboration workspace container.
    """

    def __init__(self, workspace_id: str = "shared_cloud_ws") -> None:
        self.workspace_id = workspace_id
        self.connected_users: Dict[str, Dict[str, Any]] = {}
        self.shared_memory: Dict[str, Any] = {
            "architecture": "FastAPI + React Clean Architecture",
            "decisions": ["Used JWT authentication", "Selected PostgreSQL database"],
            "requirements": ["Multi-tenant SaaS support", "Stripe payment integration"],
            "generated_code_files": ["backend/main.py", "frontend/src/App.jsx"]
        }

    def connect_user(self, user_id: str, name: str, role: str = "Developer") -> Dict[str, Any]:
        user_info = {
            "user_id": user_id,
            "name": name,
            "role": role,
            "connected_at": time.time(),
            "active_file": "backend/main.py"
        }
        self.connected_users[user_id] = user_info
        _logger.info(f"SharedAIWorkspace: User '{name}' ({role}) connected to workspace '{self.workspace_id}'.")
        return user_info

    def get_shared_memory(self) -> Dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "connected_users_count": len(self.connected_users),
            "users": list(self.connected_users.values()),
            "shared_memory": self.shared_memory
        }


global_shared_workspace = SharedAIWorkspace()
