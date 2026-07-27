"""
AIForge Team Members Manager
============================
Manages organization user accounts, team memberships, and profile assignments.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.enterprise.members")


class TeamMembersManager:
    """
    Manages enterprise users and team assignments.
    """

    def __init__(self) -> None:
        self.members: Dict[str, Dict[str, Any]] = {
            "user_alice": {
                "user_id": "user_alice",
                "email": "alice@acme.com",
                "full_name": "Alice Smith",
                "org_id": "org_acme",
                "role": "Owner",
                "joined_at": time.time() - 86400 * 30
            },
            "user_bob": {
                "user_id": "user_bob",
                "email": "bob@acme.com",
                "full_name": "Bob Jones",
                "org_id": "org_acme",
                "role": "Architect",
                "joined_at": time.time() - 86400 * 15
            }
        }

    def add_member(self, email: str, full_name: str, org_id: str, role: str = "Developer") -> Dict[str, Any]:
        u_id = f"user_{int(time.time() * 1000)}"
        member = {
            "user_id": u_id,
            "email": email,
            "full_name": full_name,
            "org_id": org_id,
            "role": role,
            "joined_at": time.time()
        }
        self.members[u_id] = member
        _logger.info(f"TeamMembersManager: Added member '{email}' as '{role}' in org '{org_id}'")
        return member

    def list_members(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.members.values())
        if org_id:
            results = [m for m in results if m["org_id"] == org_id]
        return results


global_team_members_manager = TeamMembersManager()
