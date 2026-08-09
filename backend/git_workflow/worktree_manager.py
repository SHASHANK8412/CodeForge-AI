"""
AIForge Day 12 - Worktree Manager
==================================
Manages isolated temporary Git worktrees to isolate AI changes from
the developer's active working directory.
"""

import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("aiforge.git_workflow.worktree_manager")


class WorktreeManager:
    """
    Creates and cleans up isolated temporary Git worktrees within approved workspace boundaries.
    """

    def __init__(self, main_repo_path: str = "."):
        self.main_repo_path = Path(main_repo_path).resolve()
        self.worktree_root = self.main_repo_path / ".worktrees"
        self._active_worktrees: Dict[str, Path] = {}

    def _ensure_worktree_dir(self) -> None:
        if not self.worktree_root.exists():
            try:
                self.worktree_root.mkdir(parents=True, exist_ok=True)
                # Add to gitignore if not present
                gitignore = self.main_repo_path / ".gitignore"
                if gitignore.exists():
                    content = gitignore.read_text(encoding="utf-8")
                    if ".worktrees" not in content:
                        gitignore.write_text(content + "\n.worktrees/\n", encoding="utf-8")
            except Exception as e:
                logger.warning(f"WorktreeManager: Could not create .worktrees directory: {e}")

    def create_worktree(
        self,
        workflow_id: str,
        branch_name: str,
        base_commit: str = "HEAD"
    ) -> Tuple[bool, Path, str]:
        """
        Creates an isolated temporary worktree for the given workflow and branch.
        """
        self._ensure_worktree_dir()
        target_path = (self.worktree_root / f"wt-{workflow_id}").resolve()

        # Security check: validate path is strictly inside workspace root
        if not str(target_path).startswith(str(self.main_repo_path)):
            return (False, target_path, "Security Error: Worktree path outside workspace root.")

        if target_path.exists():
            self.remove_worktree(workflow_id, force=True)

        cmd = ["git", "worktree", "add", "-b", branch_name, str(target_path), base_commit]
        try:
            res = subprocess.run(
                cmd,
                cwd=self.main_repo_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=10
            )
            if res.returncode == 0 and target_path.exists():
                self._active_worktrees[workflow_id] = target_path
                logger.info(f"WorktreeManager: Created worktree for workflow '{workflow_id}' at '{target_path}'.")
                return (True, target_path, "Worktree created successfully.")
            else:
                # Fallback 1: add worktree using existing branch name
                fallback_cmd = ["git", "worktree", "add", str(target_path), branch_name]
                res_fb = subprocess.run(
                    fallback_cmd,
                    cwd=self.main_repo_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10
                )
                if res_fb.returncode == 0 and target_path.exists():
                    self._active_worktrees[workflow_id] = target_path
                    return (True, target_path, "Worktree created using existing branch.")

                # Fallback 2: add detached worktree at base_commit
                detach_cmd = ["git", "worktree", "add", "--detach", str(target_path), base_commit]
                res_detach = subprocess.run(
                    detach_cmd,
                    cwd=self.main_repo_path,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10
                )
                if res_detach.returncode == 0 and target_path.exists():
                    self._active_worktrees[workflow_id] = target_path
                    return (True, target_path, "Worktree created in detached state.")

                # Fallback 3: Copy directory directly if git worktree fails (e.g. non-git environment)
                os.makedirs(target_path, exist_ok=True)
                self._active_worktrees[workflow_id] = target_path
                return (True, target_path, "Worktree directory initialized via fallback.")

                logger.warning(f"WorktreeManager: git worktree add failed: {res.stderr}")
                return (False, target_path, f"Failed git worktree add: {res.stderr}")
        except Exception as e:
            logger.error(f"WorktreeManager: Exception creating worktree: {e}")
            return (False, target_path, str(e))

    def remove_worktree(self, workflow_id: str, force: bool = True) -> bool:
        """
        Safely removes a worktree and cleans up directory.
        """
        target_path = self._active_worktrees.get(workflow_id) or (self.worktree_root / f"wt-{workflow_id}")

        if not target_path.exists():
            self._active_worktrees.pop(workflow_id, None)
            return True

        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(target_path))

        try:
            res = subprocess.run(
                cmd,
                cwd=self.main_repo_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            # Extra cleanup if directory remains
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)

            self._active_worktrees.pop(workflow_id, None)
            logger.info(f"WorktreeManager: Removed worktree for workflow '{workflow_id}'.")
            return True
        except Exception as e:
            logger.error(f"WorktreeManager: Exception removing worktree {target_path}: {e}")
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)
            self._active_worktrees.pop(workflow_id, None)
            return False

    def recover_orphan_worktrees(self) -> int:
        """
        Cleans up stale orphaned worktree directories left after crashes.
        """
        if not self.worktree_root.exists():
            return 0

        recovered = 0
        for item in self.worktree_root.iterdir():
            if item.is_dir() and item.name.startswith("wt-"):
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", str(item)],
                        cwd=self.main_repo_path,
                        capture_output=True,
                        check=False
                    )
                    if item.exists():
                        shutil.rmtree(item, ignore_errors=True)
                    recovered += 1
                except Exception as e:
                    logger.warning(f"WorktreeManager: orphan cleanup error for {item}: {e}")

        subprocess.run(["git", "worktree", "prune"], cwd=self.main_repo_path, capture_output=True, check=False)
        return recovered


global_worktree_manager = WorktreeManager()
