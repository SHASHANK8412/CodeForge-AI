"""
AIForge V2 — Day 14 Version Management, Snapshots & Rollback Engine
=====================================================================
Manages project generation version history, snapshots, regression detection,
repeated failure detection, and safe rollback to known-good versions.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.quality.version_manager")


class ProjectVersion(BaseModel):
    version_id: str
    project_id: str
    parent_version: Optional[str] = None
    files_snapshot: Dict[str, str] = Field(default_factory=dict)
    changed_files: List[str] = Field(default_factory=list)
    repair_reason: str = ""
    change_source: str = "USER"
    created_at: float = Field(default_factory=time.time)
    test_result: Dict[str, Any] = Field(default_factory=dict)
    quality_score: float = 100.0


class VersionManager:
    """
    Manages snapshots, version lineage, regression checks, and rollbacks for project generations.
    """

    def __init__(self):
        self._history: Dict[str, List[ProjectVersion]] = {}  # project_id -> [versions]

    def create_snapshot(
        self,
        project_id: str,
        files_map: Dict[str, str],
        repair_reason: str = "Initial Generation",
        changed_files: Optional[List[str]] = None,
        test_result: Optional[Dict[str, Any]] = None,
        quality_score: float = 100.0,
        change_source: str = "USER"
    ) -> ProjectVersion:
        """
        Creates and stores a immutable snapshot version of project files.
        """
        versions = self._history.setdefault(project_id, [])
        version_num = len(versions) + 1
        version_id = f"v{version_num}"
        parent_id = versions[-1].version_id if versions else None

        ver = ProjectVersion(
            version_id=version_id,
            project_id=project_id,
            parent_version=parent_id,
            files_snapshot=dict(files_map),
            changed_files=changed_files or list(files_map.keys()),
            repair_reason=repair_reason,
            change_source=change_source,
            created_at=time.time(),
            test_result=test_result or {},
            quality_score=quality_score
        )
        versions.append(ver)
        _logger.info(f"VersionManager: Created snapshot '{version_id}' for project '{project_id}' ({len(ver.files_snapshot)} file(s))")
        return ver

    def get_latest_version(self, project_id: str) -> Optional[ProjectVersion]:
        versions = self._history.get(project_id, [])
        return versions[-1] if versions else None

    def get_version_history(self, project_id: str) -> List[ProjectVersion]:
        return self._history.get(project_id, [])

    def get_history(self, project_id: str) -> List[ProjectVersion]:
        return self.get_version_history(project_id)

    def rollback(
        self,
        project_id: str,
        files_map: Dict[str, str],
        target_version_id: Optional[str] = None,
        project_dir: Optional[Path] = None
    ) -> Optional[ProjectVersion]:
        """
        Restores files_map and disk files to the specified or last known-good version.
        """
        versions = self._history.get(project_id, [])
        if not versions:
            _logger.warning(f"Rollback failed: No version history for project '{project_id}'")
            return None

        target_ver = None
        if target_version_id:
            target_ver = next((v for v in versions if v.version_id == target_version_id), None)
        else:
            # Default to second to last version (or last passed version)
            target_ver = versions[-2] if len(versions) >= 2 else versions[0]

        if not target_ver:
            _logger.warning(f"Rollback failed: Target version '{target_version_id}' not found.")
            return None

        # Restore files_map
        files_map.clear()
        files_map.update(target_ver.files_snapshot)

        # Restore disk if project_dir provided
        if project_dir and project_dir.exists():
            for rel_path, content in target_ver.files_snapshot.items():
                dest_path = (project_dir / rel_path.replace("\\", "/").lstrip("/")).resolve()
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_text(content, encoding="utf-8")

        _logger.info(f"Rollback successful: Restored project '{project_id}' to version '{target_ver.version_id}'")
        return target_ver

    def detect_regression(
        self,
        prev_test_res: Dict[str, Any],
        new_test_res: Dict[str, Any],
        prev_score: float,
        new_score: float
    ) -> bool:
        """
        Returns True if new repair caused a regression in test pass count or overall quality score.
        """
        prev_passed = prev_test_res.get("passed", 0)
        new_passed = new_test_res.get("passed", 0)

        # Test regression check
        if new_passed < prev_passed:
            _logger.warning(f"Regression detected! Tests passed decreased from {prev_passed} to {new_passed}")
            return True

        # Quality score regression check
        if new_score < prev_score:
            _logger.warning(f"Regression detected! Quality score dropped from {prev_score} to {new_score}")
            return True

        return False

    def detect_repeated_failure(self, root_causes_history: List[str]) -> bool:
        """
        Returns True if the exact same root cause has repeated consecutively.
        """
        if len(root_causes_history) >= 2:
            if root_causes_history[-1] == root_causes_history[-2] and root_causes_history[-1] != "N/A":
                _logger.warning(f"Repeated failure detected: '{root_causes_history[-1]}'")
                return True
        return False


global_version_manager = VersionManager()
