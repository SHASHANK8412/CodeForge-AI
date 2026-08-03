"""
AIForge Day 12 - Git Repository Manager
========================================
Handles safe local Git execution, branch creation, dirty repository checks,
explicit staging, and commit operations using trusted subprocess arrays.
"""

import re
import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from backend.git_workflow.models import CommitPlan, CommitResult

logger = logging.getLogger("aiforge.git_workflow.git_manager")


class GitRepositoryManager:
    """
    Manages local Git repository operations without shell execution security risks.
    Protects user developer working trees from accidental resets or cleanups.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def _run_git(self, args: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
        """
        Runs a git command securely using subprocess argument array (shell=False).
        """
        target_dir = cwd or self.repo_path
        cmd = ["git"] + args
        try:
            res = subprocess.run(
                cmd,
                cwd=target_dir,
                capture_output=True,
                text=True,
                check=False
            )
            return (res.returncode == 0, res.stdout.strip(), res.stderr.strip())
        except Exception as e:
            logger.error(f"GitRepositoryManager subprocess error running {cmd}: {e}")
            return (False, "", str(e))

    def get_status(self, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """
        Inspect git status: returns branch, HEAD commit, clean/dirty state, and modified/untracked files.
        """
        success, out, err = self._run_git(["status", "--porcelain", "-b"], cwd=cwd)
        if not success:
            return {
                "clean": True,
                "branch": "main",
                "head": "",
                "dirty": False,
                "modified": [],
                "untracked": [],
                "error": err
            }

        lines = out.splitlines()
        branch_line = lines[0] if lines else "## main"
        branch_match = re.search(r"##\s+([\w\.\/\-]+)", branch_line)
        current_branch = branch_match.group(1) if branch_match else "main"

        modified = []
        untracked = []
        for line in lines[1:]:
            if line.startswith("??"):
                untracked.append(line[3:].strip())
            elif line.strip():
                modified.append(line[3:].strip())

        is_dirty = len(modified) > 0 or len(untracked) > 0

        # Get HEAD sha
        _, head_sha, _ = self._run_git(["rev-parse", "HEAD"], cwd=cwd)

        return {
            "clean": not is_dirty,
            "dirty": is_dirty,
            "branch": current_branch,
            "head": head_sha[:8] if head_sha else "head",
            "full_head": head_sha,
            "modified": modified,
            "untracked": untracked
        }

    def get_current_head(self, cwd: Optional[Path] = None) -> str:
        success, out, _ = self._run_git(["rev-parse", "HEAD"], cwd=cwd)
        return out.strip() if success else "0000000000000000000000000000000000000000"

    def list_branches(self, cwd: Optional[Path] = None) -> List[str]:
        success, out, _ = self._run_git(["branch", "--list"], cwd=cwd)
        if not success or not out:
            return ["main"]
        branches = []
        for line in out.splitlines():
            cleaned = line.replace("*", "").strip()
            if cleaned:
                branches.append(cleaned)
        return branches

    def sanitize_branch_name(self, raw_name: str) -> str:
        """
        Sanitizes branch names to avoid shell injection, spaces, or illegal git ref characters.
        Example: "; rm -rf /" -> "aiforge/fix-issue"
        """
        # Extract title or slug
        slug = raw_name.lower().strip()
        # Remove malicious shell chars
        slug = re.sub(r"[;\|&\><\*\?\\\{\}\$]", "", slug)
        # Replace non-alphanumeric chars with hyphens
        slug = re.sub(r"[^a-z0-9]", "-", slug)
        # Collapse multiple hyphens
        slug = re.sub(r"-+", "-", slug).strip("-")

        if not slug or slug in ("main", "master", "head"):
            slug = "fix-issue"

        if len(slug) > 40:
            slug = slug[:40].rstrip("-")

        return f"aiforge/{slug}"

    def create_local_branch(self, branch_name: str, base_ref: str = "HEAD", cwd: Optional[Path] = None) -> str:
        """
        Creates a new local branch with collision resolution.
        """
        sanitized = self.sanitize_branch_name(branch_name)
        existing = self.list_branches(cwd=cwd)

        final_branch = sanitized
        counter = 2
        while final_branch in existing:
            final_branch = f"{sanitized}-{counter}"
            counter += 1

        success, out, err = self._run_git(["checkout", "-b", final_branch, base_ref], cwd=cwd)
        if not success:
            logger.warning(f"GitRepositoryManager: failed checkout -b {final_branch}: {err}")
            # Try simple branch creation
            self._run_git(["branch", final_branch, base_ref], cwd=cwd)

        return final_branch

    def commit_changes(
        self,
        commit_plan: CommitPlan,
        cwd: Optional[Path] = None
    ) -> CommitResult:
        """
        Stages explicitly approved files and creates a local git commit.
        Never executes 'git add .' blindly!
        """
        if not commit_plan.files:
            return CommitResult(created=False, status="NO_CHANGES", message="No files specified for commit.")

        target_dir = cwd or self.repo_path

        # Stage specific files
        staged_files = []
        for file_path in commit_plan.files:
            success, _, err = self._run_git(["add", file_path], cwd=target_dir)
            if success:
                staged_files.append(file_path)
            else:
                logger.warning(f"GitRepositoryManager: Failed to stage file '{file_path}': {err}")

        if not staged_files:
            return CommitResult(created=False, status="NO_STAGED_FILES", message="Failed to stage any target files.")

        # Build commit message
        msg_header = f"{commit_plan.type}"
        if commit_plan.scope:
            msg_header += f"({commit_plan.scope})"
        msg_header += f": {commit_plan.summary}"

        full_msg = f"{msg_header}\n\n{commit_plan.body}".strip()

        # Commit
        success, out, err = self._run_git(["commit", "-m", full_msg], cwd=target_dir)
        if not success:
            if "nothing to commit" in out.lower() or "nothing to commit" in err.lower():
                return CommitResult(created=False, status="NO_CHANGES", message="Nothing to commit.")
            return CommitResult(created=False, status="COMMIT_FAILED", message=f"Commit failed: {err}")

        # Extract sha
        sha = self.get_current_head(cwd=target_dir)[:8]

        return CommitResult(
            created=True,
            commit_sha=sha,
            message=msg_header,
            files=staged_files,
            status="COMMITTED"
        )


global_git_manager = GitRepositoryManager()
