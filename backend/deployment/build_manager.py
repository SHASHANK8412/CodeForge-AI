"""
AIForge Build Manager
=====================
Tracks build history, artifact metadata, status (SUCCESS, FAILED), commit hashes, and build durations.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.deployment.build_manager")


class BuildManager:
    """
    Manages build history and artifact tracking.
    """

    def __init__(self) -> None:
        self.builds: Dict[str, Dict[str, Any]] = {
            "build_101": {
                "build_id": "build_101",
                "branch": "main",
                "status": "SUCCESS",
                "duration": "3m 45s",
                "artifacts": ["frontend-image:v1.0.0", "backend-image:v1.0.0"],
                "commit_hash": "a1b2c3d",
                "timestamp": time.time() - 7200
            },
            "build_102": {
                "build_id": "build_102",
                "branch": "main",
                "status": "SUCCESS",
                "duration": "4m 10s",
                "artifacts": ["frontend-image:v1.1.0", "backend-image:v1.1.0", "db-migration:v1.1.0"],
                "commit_hash": "f4e5d6c",
                "timestamp": time.time() - 3600
            }
        }

    def record_build(
        self,
        branch: str = "main",
        status: str = "SUCCESS",
        duration: str = "4m 22s",
        artifacts: Optional[List[str]] = None,
        commit_hash: str = "a1b2c3d"
    ) -> Dict[str, Any]:
        build_id = f"build_{int(time.time() * 1000)}"
        build_entry = {
            "build_id": build_id,
            "branch": branch,
            "status": status,
            "duration": duration,
            "artifacts": artifacts or ["frontend-image", "backend-image", "database-image"],
            "commit_hash": commit_hash,
            "timestamp": time.time()
        }
        self.builds[build_id] = build_entry
        _logger.info(f"BuildManager: Recorded build '{build_id}' (Status: {status})")
        return build_entry

    def get_all_builds(self) -> List[Dict[str, Any]]:
        return sorted(list(self.builds.values()), key=lambda b: b["timestamp"], reverse=True)

    def get_build(self, build_id: str) -> Optional[Dict[str, Any]]:
        return self.builds.get(build_id)


global_build_manager = BuildManager()
