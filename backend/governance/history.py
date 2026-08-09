"""
AIForge Change History & Rollback Manager
=========================================
Tracks file version history, AI change summaries, code diffs, and rollback execution across project repositories.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.governance.history")


class ChangeHistoryManager:
    """
    Manages project version history, diff generation, AI summaries, and rollbacks.
    """

    def __init__(self) -> None:
        self.version_history: Dict[str, List[Dict[str, Any]]] = {
            "proj_hospital": [
                {
                    "version_id": "v1.0.0",
                    "project_id": "proj_hospital",
                    "author": "Architect Agent",
                    "summary": "Initial microservices setup & database models",
                    "timestamp": time.time() - 86400,
                    "files_affected": ["src/main.py", "src/models/patient.py"],
                    "diff": "+ class Patient(Base):\n+    id: int\n+    name: str"
                },
                {
                    "version_id": "v1.1.0",
                    "project_id": "proj_hospital",
                    "author": "Backend Agent",
                    "summary": "Added JWT authentication and RBAC patient endpoints",
                    "timestamp": time.time() - 43200,
                    "files_affected": ["src/auth/jwt_handler.py", "src/api/patients.py"],
                    "diff": "+ @router.post('/patients')\n+ def create_patient(data: PatientSchema):\n+     return save_patient(data)"
                }
            ]
        }

    def record_version(
        self,
        project_id: str,
        version_id: str,
        author: str,
        summary: str,
        files_affected: List[str],
        diff: str = ""
    ) -> Dict[str, Any]:
        entry = {
            "version_id": version_id,
            "project_id": project_id,
            "author": author,
            "summary": summary,
            "timestamp": time.time(),
            "files_affected": files_affected,
            "diff": diff
        }
        if project_id not in self.version_history:
            self.version_history[project_id] = []
        self.version_history[project_id].insert(0, entry)
        _logger.info(f"ChangeHistoryManager: Recorded version '{version_id}' for project '{project_id}'")
        return entry

    def get_project_history(self, project_id: str) -> List[Dict[str, Any]]:
        return self.version_history.get(project_id, [])

    def rollback_to_version(self, project_id: str, version_id: str) -> Dict[str, Any]:
        history = self.get_project_history(project_id)
        target = None
        for v in history:
            if v["version_id"] == version_id:
                target = v
                break

        if not target:
            raise ValueError(f"Version '{version_id}' not found in project '{project_id}' history.")

        # Create rollback record
        rollback_v_id = f"v_rollback_{int(time.time())}"
        rollback_entry = self.record_version(
            project_id=project_id,
            version_id=rollback_v_id,
            author="Human Administrator (Rollback)",
            summary=f"Rolled back workspace state to version '{version_id}'",
            files_affected=target["files_affected"],
            diff=f"Reverted to state at {target['version_id']}"
        )

        _logger.info(f"ChangeHistoryManager: Rolled back project '{project_id}' to version '{version_id}'")
        return {
            "status": "success",
            "rolled_back_to": version_id,
            "new_rollback_version": rollback_v_id,
            "rollback_entry": rollback_entry
        }


global_change_history = ChangeHistoryManager()
