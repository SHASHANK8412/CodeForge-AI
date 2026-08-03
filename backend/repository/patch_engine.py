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
        snapshots: Dict[str, Optional[str]] = {}

        try:
            for patch in patches:
                # 1. Path Safety Validation
                target_abs = global_repository_scanner.validate_path_safety(abs_root, patch.path)

                # Record original content for rollback
                if os.path.exists(target_abs):
                    with open(target_abs, "r", encoding="utf-8", errors="ignore") as f:
                        snapshots[target_abs] = f.read()

                    # Stale File Hash Verification
                    if patch.original_hash:
                        current_hash = hashlib.sha256(snapshots[target_abs].encode("utf-8")).hexdigest()
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
                    # Direct file write
                    with open(target_abs, "w", encoding="utf-8") as f:
                        f.write(patch.updated_content)

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

    def _rollback_snapshots(self, snapshots: Dict[str, Optional[str]]):
        """Restores original files from snapshot dict."""
        for fpath, orig_content in snapshots.items():
            try:
                if orig_content is None:
                    if os.path.exists(fpath):
                        os.remove(fpath)
                else:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(orig_content)
            except Exception as e:
                _logger.error(f"[PatchEngine] Rollback error on '{fpath}': {e}")


global_patch_engine = PatchEngine()
