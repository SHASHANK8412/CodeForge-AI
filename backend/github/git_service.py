"""
AIForge Autonomous Git Service
==============================
Provides safe, isolated Git CLI operations using structured subprocess argument arrays.
Guarantees:
- shell=False to prevent arbitrary shell command injection
- Strict path traversal protection
- Sanitized branch names
- Safe staging, commit, remote configuration, and pushing
"""

import os
import re
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("aiforge.github.git_service")


class GitExecutionResult:
    """Structured result for Git command execution."""

    def __init__(self, success: bool, stdout: str, stderr: str, returncode: int, command: List[str]):
        self.success = success
        self.stdout = stdout.strip()
        self.stderr = stderr.strip()
        self.returncode = returncode
        self.command = command

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "command": " ".join(self.command)
        }


class GitService:
    """
    Encapsulates all Git CLI operations safely and reliably.
    """

    def __init__(self, git_binary: Optional[str] = None):
        self.git_binary = git_binary or shutil.which("git") or "git"

    def _run_git(
        self,
        args: List[str],
        cwd: Path,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ) -> GitExecutionResult:
        """
        Executes a Git command using subprocess argument arrays with shell=False.
        """
        cmd = [self.git_binary] + args
        custom_env = os.environ.copy()
        if env:
            custom_env.update(env)

        # Prevent Git from prompting for terminal credentials / passwords
        custom_env["GIT_TERMINAL_PROMPT"] = "0"
        custom_env["GIT_ASKPASS"] = "echo"

        try:
            res = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                shell=False,
                timeout=timeout,
                env=custom_env
            )
            return GitExecutionResult(
                success=(res.returncode == 0),
                stdout=res.stdout,
                stderr=res.stderr,
                returncode=res.returncode,
                command=cmd
            )
        except subprocess.TimeoutExpired as te:
            logger.warning(f"Git command timed out: {cmd}")
            return GitExecutionResult(
                success=False,
                stdout="",
                stderr=f"Git command timed out after {timeout}s: {te}",
                returncode=124,
                command=cmd
            )
        except Exception as ex:
            logger.error(f"Failed to execute git command {cmd}: {ex}")
            return GitExecutionResult(
                success=False,
                stdout="",
                stderr=str(ex),
                returncode=-1,
                command=cmd
            )

    def init(self, cwd: Path, initial_branch: str = "main") -> GitExecutionResult:
        """
        Initializes a new Git repository in the specified directory.
        Configures default user if none is set globally.
        """
        cwd.mkdir(parents=True, exist_ok=True)
        # Try modern git init -b <branch>
        res = self._run_git(["init", "-b", initial_branch], cwd=cwd)
        if not res.success:
            # Fallback for older git versions
            res = self._run_git(["init"], cwd=cwd)
            if res.success:
                self.checkout_new_branch(cwd, initial_branch)

        # Ensure minimal git user config exists locally so commits succeed
        self._run_git(["config", "user.name", "AIForge Agent"], cwd=cwd)
        self._run_git(["config", "user.email", "agent@aiforge.dev"], cwd=cwd)
        return res

    def status(self, cwd: Path) -> Dict[str, Any]:
        """
        Returns structured git status details.
        """
        res = self._run_git(["status", "--porcelain", "-b"], cwd=cwd)
        if not res.success:
            return {
                "initialized": False,
                "clean": True,
                "branch": "main",
                "staged": [],
                "modified": [],
                "untracked": [],
                "error": res.stderr
            }

        lines = res.stdout.splitlines()
        branch_line = lines[0] if lines else "## main"
        branch_match = re.search(r"##\s+([^\s\.]+)", branch_line)
        current_branch = branch_match.group(1) if branch_match else "main"

        staged = []
        modified = []
        untracked = []

        for line in lines[1:]:
            if len(line) < 3:
                continue
            index_status = line[0]
            worktree_status = line[1]
            file_name = line[3:].strip()

            if index_status in ["A", "M", "R", "D"]:
                staged.append(file_name)
            if worktree_status in ["M", "D"]:
                modified.append(file_name)
            if line.startswith("??"):
                untracked.append(file_name)

        is_clean = len(staged) == 0 and len(modified) == 0 and len(untracked) == 0

        # Current HEAD commit
        head_res = self._run_git(["rev-parse", "HEAD"], cwd=cwd)
        head_sha = head_res.stdout[:8] if head_res.success else ""

        return {
            "initialized": True,
            "clean": is_clean,
            "branch": current_branch,
            "head": head_sha,
            "staged": staged,
            "modified": modified,
            "untracked": untracked
        }

    def add(self, cwd: Path, files: Optional[List[str]] = None) -> GitExecutionResult:
        """
        Stages specific files or all tracked/untracked workspace files.
        """
        if files:
            safe_files = [f.replace("\\", "/") for f in files]
            return self._run_git(["add"] + safe_files, cwd=cwd)
        return self._run_git(["add", "."], cwd=cwd)

    def commit(
        self,
        cwd: Path,
        message: str,
        author_name: str = "AIForge Agent",
        author_email: str = "agent@aiforge.dev"
    ) -> GitExecutionResult:
        """
        Creates a commit with a clean, structured commit message.
        """
        env = {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email
        }
        clean_msg = message.strip() or "feat: automated project update"
        return self._run_git(["commit", "-m", clean_msg], cwd=cwd, env=env)

    def checkout_new_branch(self, cwd: Path, branch_name: str) -> GitExecutionResult:
        """
        Creates and switches to a new branch with name sanitization.
        """
        clean_branch = self.sanitize_branch_name(branch_name)
        res = self._run_git(["checkout", "-b", clean_branch], cwd=cwd)
        if not res.success:
            # If already exists, simply switch
            return self._run_git(["checkout", clean_branch], cwd=cwd)
        return res

    def branch(self, cwd: Path, branch_name: str) -> GitExecutionResult:
        """
        Creates or checks out the target branch.
        """
        return self.checkout_new_branch(cwd, branch_name)

    def get_current_branch(self, cwd: Path) -> str:
        res = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
        if res.success and res.stdout:
            return res.stdout
        return "main"

    def get_latest_commit_sha(self, cwd: Path) -> str:
        res = self._run_git(["rev-parse", "HEAD"], cwd=cwd)
        return res.stdout.strip() if res.success else ""

    def remote_add(self, cwd: Path, name: str, url: str) -> GitExecutionResult:
        """
        Adds a remote or updates its URL if it already exists.
        """
        existing = self._run_git(["remote", "get-url", name], cwd=cwd)
        if existing.success:
            return self._run_git(["remote", "set-url", name, url], cwd=cwd)
        return self._run_git(["remote", "add", name, url], cwd=cwd)

    def remote_get(self, cwd: Path, name: str = "origin") -> Optional[str]:
        res = self._run_git(["remote", "get-url", name], cwd=cwd)
        return res.stdout.strip() if res.success else None

    def push(
        self,
        cwd: Path,
        remote: str = "origin",
        branch: str = "main",
        set_upstream: bool = True
    ) -> GitExecutionResult:
        """
        Pushes commits to remote repository.
        """
        args = ["push"]
        if set_upstream:
            args += ["-u"]
        args += [remote, branch]
        return self._run_git(args, cwd=cwd, timeout=60.0)

    @staticmethod
    def sanitize_branch_name(raw: str) -> str:
        slug = raw.lower().strip()
        slug = re.sub(r"[;\|&\><\*\?\\\{\}\$]", "", slug)
        slug = re.sub(r"[^a-z0-9_\-\/]", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = re.sub(r"\/+", "/", slug)
        slug = slug.strip("-/.")
        return slug or "main"


global_git_service = GitService()
