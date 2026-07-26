import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aiforge.memory.versioning")


class VersionControlManager:
    """
    VersionControlManager tracks version snapshots (v1, v2, v3) for projects,
    recording architecture updates, file additions/deletions, and commit descriptions.
    """

    def __init__(self):
        self.versions: Dict[str, List[Dict[str, Any]]] = {}

    def create_version(
        self,
        project_id: str,
        commit_message: str,
        files: Dict[str, str],
        architecture: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Creates and stores a new project version snapshot."""
        history = self.versions.setdefault(project_id, [])
        version_number = f"v{len(history) + 1}"

        snapshot = {
            "version": version_number,
            "project_id": project_id,
            "commit_message": commit_message,
            "file_count": len(files),
            "files": dict(files),
            "architecture": architecture or {},
            "timestamp": time.time()
        }

        history.append(snapshot)
        logger.info(f"VersionControlManager created '{version_number}' for project '{project_id}'")
        return snapshot

    def list_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """Returns all version history records for a project."""
        return self.versions.get(project_id, [])

    def get_version(self, project_id: str, version_tag: str) -> Optional[Dict[str, Any]]:
        """Returns a specific version snapshot by tag (e.g. 'v1', 'v2')."""
        history = self.versions.get(project_id, [])
        for v in history:
            if v["version"] == version_tag:
                return v
        return None


# Global VersionControlManager instance
global_version_manager = VersionControlManager()
