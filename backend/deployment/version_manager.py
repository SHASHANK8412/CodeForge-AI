"""
AIForge Version Manager
=======================
Manages Semantic Versioning (vMajor.Minor.Patch) and version release history.
"""

import time
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.deployment.version_manager")


class VersionManager:
    """
    Manages semantic versioning (Major, Minor, Patch) and tags.
    """

    def __init__(self) -> None:
        self.current_version = "v2.1.0"
        self.version_history: List[Dict[str, Any]] = [
            {"version": "v1.0.0", "type": "Major", "release_date": time.time() - 86400 * 30, "tag": "v1.0.0-release"},
            {"version": "v2.0.0", "type": "Major", "release_date": time.time() - 86400 * 7, "tag": "v2.0.0-release"},
            {"version": "v2.1.0", "type": "Minor", "release_date": time.time() - 3600, "tag": "v2.1.0-release"}
        ]

    def get_current_version(self) -> str:
        return self.current_version

    def increment_version(self, release_type: str = "patch") -> Dict[str, Any]:
        """
        release_type: 'major', 'minor', 'patch'
        """
        rel_type = release_type.lower()
        v_str = self.current_version.lstrip("v")
        parts = [int(p) for p in v_str.split(".")]

        if rel_type == "major":
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif rel_type == "minor":
            parts[1] += 1
            parts[2] = 0
        else:  # patch
            parts[2] += 1

        new_v = f"v{parts[0]}.{parts[1]}.{parts[2]}"
        tag = f"{new_v}-release"

        entry = {
            "version": new_v,
            "type": release_type.capitalize(),
            "release_date": time.time(),
            "tag": tag,
            "previous_version": self.current_version
        }

        self.current_version = new_v
        self.version_history.append(entry)

        _logger.info(f"VersionManager: Incremented version from '{entry['previous_version']}' to '{new_v}' ({release_type})")
        return entry

    def get_version_history(self) -> List[Dict[str, Any]]:
        return list(self.version_history)


global_version_manager = VersionManager()
