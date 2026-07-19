import os
import ast
import shutil
import logging
from pathlib import Path

_logger = logging.getLogger("aiforge.performance")


class PatchApplier:
    """
    Applies minimal range patches to file layouts, supporting backup copies
    and transaction rollbacks on syntax check failures.
    """

    def __init__(self) -> None:
        pass

    def apply_patch(self, project_path: Path, patch: dict) -> bool:
        """
        Applies a patch object to the targeted file under project_path.
        """
        rel_file = patch["file"]
        target_file = project_path / rel_file
        
        if not target_file.exists():
            _logger.error(f"Target file for patch application does not exist: {target_file}")
            return False

        # 1. Create a backup file copy
        backup_file = target_file.with_name(f"{target_file.name}.bak")
        try:
            shutil.copy2(target_file, backup_file)
            _logger.info(f"Backup copy created: {backup_file}")
        except Exception as exc:
            _logger.error(f"Failed to create backup copy for {target_file}: {exc}")
            return False

        try:
            # 2. Read current lines
            with open(target_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            start_line = int(patch["start_line"])
            end_line = int(patch["end_line"])
            replacement = patch["replacement"]

            # Line numbers are 1-indexed. Index in list is line_no - 1.
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)

            # Preserve line ending of original file if possible
            line_ending = "\n"
            if lines:
                if lines[0].endswith("\r\n"):
                    line_ending = "\r\n"
            
            # Format replacement as list of lines
            replacement_lines = []
            for line in replacement.splitlines():
                if not line.endswith(("\n", "\r")):
                    replacement_lines.append(line + line_ending)
                else:
                    replacement_lines.append(line)

            # 3. Replace range
            new_lines = lines[:start_idx] + replacement_lines + lines[end_idx:]

            # 4. Validate resulting code syntax before saving
            new_content = "".join(new_lines)
            if rel_file.endswith(".py"):
                try:
                    ast.parse(new_content)
                except SyntaxError as exc:
                    _logger.error(f"Syntax validation failed on modified content for {rel_file}: {exc}")
                    # Rollback
                    self._rollback(target_file, backup_file)
                    _logger.warning("ERROR Patch rejected due to syntax compilation failure")
                    return False

            # 5. Write to file
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Remove backup on successful apply
            if backup_file.exists():
                os.remove(backup_file)
            
            _logger.info(f"INFO Patch validated and applied successfully to {rel_file}")
            return True

        except Exception as exc:
            _logger.error(f"Failed to apply patch to {rel_file}: {exc}")
            self._rollback(target_file, backup_file)
            return False

    def _rollback(self, target_file: Path, backup_file: Path) -> None:
        """
        Restores the backup file, rolling back changes.
        """
        if backup_file.exists():
            try:
                shutil.copy2(backup_file, target_file)
                os.remove(backup_file)
                _logger.info(f"Successfully rolled back changes using backup: {target_file}")
            except Exception as exc:
                _logger.error(f"Critical: Failed to rollback backup copy for {target_file}: {exc}")
