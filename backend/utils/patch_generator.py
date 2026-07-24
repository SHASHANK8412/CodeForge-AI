"""
AIForge Day 95 Patch & Backup Generator Utility
===============================================
1. Generates unified git patches and diffs (+ Added JWT middleware, + Added login endpoint).
2. Preserves code formatting, comments, and imports.
3. Automatically creates safe backups in .backup/ before editing code to prevent file corruption.
"""

import os
import difflib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.utils.patch_generator")


class PatchAndBackupGenerator:
    """
    Patch & Safe Backup System.
    """

    def __init__(self, backup_dir: Optional[str] = None) -> None:
        if backup_dir is None:
            bk_path = Path(__file__).resolve().parents[1] / ".backup"
            bk_path.mkdir(parents=True, exist_ok=True)
            backup_dir = str(bk_path)
        self.backup_directory = Path(backup_dir)

    def create_safe_backup(self, filepath: str, content: str) -> str:
        _logger.info(f"PatchAndBackupGenerator: Creating backup for '{filepath}'...")
        try:
            safe_name = filepath.replace("/", "_").replace("\\", "_")
            backup_file = self.backup_directory / f"{safe_name}.bak"
            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(content)
            return str(backup_file)
        except Exception as e:
            _logger.error(f"Failed to create backup for '{filepath}': {e}")
            return ""

    def generate_diff_patch(self, filepath: str, original_code: str, modified_code: str) -> Dict[str, Any]:
        _logger.info(f"PatchAndBackupGenerator: Generating diff patch for '{filepath}'...")

        original_lines = original_code.splitlines(keepends=True)
        modified_lines = modified_code.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
            lineterm=""
        ))

        patch_str = "".join(diff)

        # Summary lines
        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "filepath": filepath,
            "has_changes": len(diff) > 0,
            "additions_count": additions,
            "deletions_count": deletions,
            "unified_diff": patch_str,
            "summary": f"+{additions} additions, -{deletions} deletions in {filepath}"
        }


global_patch_generator = PatchAndBackupGenerator()
