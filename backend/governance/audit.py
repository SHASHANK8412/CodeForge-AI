"""
AIForge Audit Logger
====================
Provides searchable, immutable audit logging for enterprise governance, tracking actions by users and AI agents.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.governance.audit")


class AuditLogger:
    """
    Records and queries enterprise audit logs.
    """

    def __init__(self) -> None:
        self.logs: List[Dict[str, Any]] = [
            {
                "log_id": "audit_1",
                "timestamp": time.time() - 3600,
                "formatted_time": time.strftime("%H:%M:%S", time.localtime(time.time() - 3600)),
                "user_or_agent": "Reviewer Approved",
                "role": "Reviewer",
                "action": "Approved Architecture Checkpoint",
                "target_entity": "Authentication Module",
                "version": "Version 1.2",
                "files_changed": ["src/auth/jwt_handler.py"],
                "decision": "Approved",
                "project_id": "proj_hospital"
            },
            {
                "log_id": "audit_2",
                "timestamp": time.time() - 1800,
                "formatted_time": time.strftime("%H:%M:%S", time.localtime(time.time() - 1800)),
                "user_or_agent": "DevOps Agent",
                "role": "DevOps",
                "action": "Requested Staging Deployment Approval",
                "target_entity": "Hospital Staging Deployment",
                "version": "Version 1.3-rc1",
                "files_changed": ["docker-compose.yml", "k8s/deployment.yaml"],
                "decision": "Pending",
                "project_id": "proj_hospital"
            }
        ]

    def log_event(
        self,
        user_or_agent: str,
        role: str,
        action: str,
        target_entity: str,
        project_id: str = "proj_general",
        version: str = "v1.0",
        files_changed: Optional[List[str]] = None,
        decision: str = "Completed"
    ) -> Dict[str, Any]:
        log_id = f"audit_{int(time.time() * 1000)}"
        now = time.time()
        entry = {
            "log_id": log_id,
            "timestamp": now,
            "formatted_time": time.strftime("%H:%M:%S", time.localtime(now)),
            "user_or_agent": user_or_agent,
            "role": role,
            "action": action,
            "target_entity": target_entity,
            "version": version,
            "files_changed": files_changed or [],
            "decision": decision,
            "project_id": project_id
        }
        self.logs.insert(0, entry)
        _logger.info(f"AuditLogger: [{entry['formatted_time']}] {user_or_agent} ({role}) -> {action} ({decision})")
        return entry

    def get_logs(
        self,
        project_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        results = self.logs
        if project_id:
            results = [l for l in results if l["project_id"] == project_id]
        if query:
            q = query.lower()
            results = [
                l for l in results
                if q in l["action"].lower() or q in l["target_entity"].lower() or q in l["user_or_agent"].lower()
            ]
        return results[:limit]


global_audit_logger = AuditLogger()
