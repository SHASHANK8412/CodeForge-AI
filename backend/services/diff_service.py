"""
AIForge Git-Style Diff Service
==============================
Computes unified Git-style patches (+ additions, - deletions) for single and multi-file modifications.
"""

import difflib
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.pair_programmer")

class DiffService:
    """
    Generates unified Git-style diff previews for file edits.
    """

    def generate_unified_diff(self, file_path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        ))

        patch_text = "".join(diff)
        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        _logger.info(f"DiffService generated patch for '{file_path}': +{additions}, -{deletions} lines.")
        return {
            "file_path": file_path,
            "patch_text": patch_text,
            "additions": additions,
            "deletions": deletions,
            "has_changes": len(diff) > 0
        }

    def generate_multi_file_diff(self, file_edits: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Processes dictionary of {file_path: {'old': ..., 'new': ...}} and returns multi-file diff report.
        """
        file_patches = []
        total_additions = 0
        total_deletions = 0

        for f_path, content in file_edits.items():
            patch_data = self.generate_unified_diff(f_path, content.get("old", ""), content.get("new", ""))
            file_patches.append(patch_data)
            total_additions += patch_data["additions"]
            total_deletions += patch_data["deletions"]

        return {
            "total_files_changed": len(file_patches),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "file_patches": file_patches
        }
