"""
AIForge Patch Engine
====================
Applies atomic FilePatches to repository files with hash verification and rollback support.
Enforces MAX_FILES_PER_CHANGE limit and path security sandbox.
"""

import os
import hashlib
import shutil
import tempfile
import logging
from typing import List, Dict, Tuple, Optional

from backend.repository.models import FilePatch, ChangeSet
from backend.repository.scanner import global_repository_scanner

_logger = logging.getLogger("aiforge.repository.patch_engine")

MAX_FILES_PER_CHANGE = 10


class PatchEngine:
    """
    Applies atomic file modifications within an approved workspace root.
    """

    def apply_patches(self, root_path: str, patches: List[FilePatch]) -> Tuple[ChangeSet, bool]:
        abs_root = os.path.abspath(root_path)

        if len(patches) > MAX_FILES_PER_CHANGE:
            _logger.warning(f"[PatchEngine] Patch size limit exceeded: {len(patches)} > {MAX_FILES_PER_CHANGE}")
            return ChangeSet(summary=f"Change size limit exceeded ({len(patches)} > {MAX_FILES_PER_CHANGE})"), False

        created = []
        modified = []
        deleted = []

        # Create temporary rollback snapshot
        # Original bytes, so a rollback restores the file exactly (encoding and line endings included).
        snapshots: Dict[str, Optional[bytes]] = {}

        try:
            for patch in patches:
                # 1. Path Safety Validation
                target_abs = global_repository_scanner.validate_path_safety(abs_root, patch.path)

                # Record original content for rollback
                newline = None                      # new files: the platform's line ending, as before
                if os.path.exists(target_abs):
                    with open(target_abs, "rb") as f:
                        snapshots[target_abs] = f.read()
                    # keep the file's own line endings, so a change does not rewrite every line
                    newline = "\r\n" if b"\r\n" in snapshots[target_abs] else "\n"

                    # Stale File Hash Verification
                    if patch.original_hash:
                        text = snapshots[target_abs].decode("utf-8", errors="ignore").replace("\r\n", "\n")
                        current_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        if current_hash != patch.original_hash:
                            raise ValueError(f"Stale File Error: '{patch.path}' content changed on disk before patch execution.")
                else:
                    snapshots[target_abs] = None

                # 2. Apply Operation Atomic Write
                os.makedirs(os.path.dirname(target_abs), exist_ok=True)
                if patch.operation == "DELETE":
                    if os.path.exists(target_abs):
                        os.remove(target_abs)
                        deleted.append(patch.path)
                else:
                    # Direct file write (content normalized to "\n"; `newline` sets what is written)
                    with open(target_abs, "w", encoding="utf-8", newline=newline) as f:
                        f.write(patch.updated_content.replace("\r\n", "\n"))

                    if snapshots[target_abs] is None:
                        created.append(patch.path)
                    else:
                        modified.append(patch.path)

            changeset = ChangeSet(
                files_created=created,
                files_modified=modified,
                files_deleted=deleted,
                verification="APPLIED",
                summary=f"Successfully updated {len(modified)} files, created {len(created)} files."
            )
            return changeset, True

        except Exception as e:
            _logger.error(f"[PatchEngine] Patch application failed: {e}; rolling back all snapshot modifications.")
            self._rollback_snapshots(snapshots)
            return ChangeSet(summary=f"Patch application failed and was rolled back: {str(e)}"), False

    def apply_changes(self, root_path: str, changes: Dict[str, Optional[str]], reason: str = "") -> Tuple[List[str], bool]:
        """
        Applies a {relative path: new content} map from a repair; None deletes the file.
        All-or-nothing: an unsafe path or failed write rolls everything back.
        Returns (normalized paths changed, applied).
        """
        patches = [
            FilePatch(path=rel.replace("\\", "/").lstrip("/"), operation="DELETE" if content is None else "MODIFY",
                      updated_content=content or "", reason=reason)
            for rel, content in (changes or {}).items()
        ]
        if not patches:
            return [], True
        _, ok = self.apply_patches(root_path, patches)
        return ([p.path for p in patches] if ok else []), ok

    def _rollback_snapshots(self, snapshots: Dict[str, Optional[bytes]]):
        """Restores original files from snapshot dict (exact bytes)."""
        for fpath, orig_content in snapshots.items():
            try:
                if orig_content is None:
                    if os.path.exists(fpath):
                        os.remove(fpath)
                else:
                    with open(fpath, "wb") as f:
                        f.write(orig_content)
            except Exception as e:
                _logger.error(f"[PatchEngine] Rollback error on '{fpath}': {e}")


global_patch_engine = PatchEngine()
