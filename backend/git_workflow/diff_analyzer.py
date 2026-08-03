"""
AIForge Day 12 - Diff Analyzer & Secret Scanner
================================================
Analyzes Git diffs between base commit and worktree to detect secrets,
sensitive file modifications, scope creep, dependency changes, and DB migrations.
"""

import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from backend.git_workflow.models import DiffAnalysis, TaskRisk, EngineeringTask

logger = logging.getLogger("aiforge.git_workflow.diff_analyzer")


class DiffAnalyzer:
    """
    Analyzes unified git diffs for scope, secrets, sensitive files, and risks.
    """

    SECRET_PATTERNS = [
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
        (r"(?i)aws_secret_access_key\s*=\s*['\"][0-9a-zA-Z\/+]{40}['\"]", "AWS Secret Access Key"),
        (r"(?i)github_token\s*=\s*['\"][a-zA-Z0-9_]{36,40}['\"]", "GitHub Personal Access Token"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"-----BEGIN (RSA|OPENSSH|PRIVATE) KEY-----", "Private Key Header"),
        (r"(?i)api[_-]?key\s*=\s*['\"](?!\$\{)[a-zA-Z0-9_\-]{20,}['\"]", "Hardcoded API Key"),
        (r"(?i)password\s*=\s*['\"](?!admin|test|secret|dummy)[a-zA-Z0-9_!@#$%^&*]{8,}['\"]", "Hardcoded Password"),
    ]

    SENSITIVE_FILE_PATTERNS = [
        r"\.env", r"\.pem$", r"\.key$", r"id_rsa", r"credentials", r"secret", r"production\.json"
    ]

    DEPENDENCY_MANIFESTS = [
        "requirements.txt", "package.json", "Pipfile", "poetry.lock", "go.mod", "Cargo.toml"
    ]

    def analyze_worktree_diff(
        self,
        worktree_path: Path,
        base_commit: str = "HEAD",
        expected_files: Optional[List[str]] = None,
        task: Optional[EngineeringTask] = None
    ) -> DiffAnalysis:
        """
        Runs git diff against base commit, parses line additions/deletions, scans for secrets and sensitive changes.
        """
        raw_diff, files_changed = self._extract_git_diff(worktree_path, base_commit)

        lines_added = 0
        lines_removed = 0
        added_lines_text = []

        for line in raw_diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                lines_added += 1
                added_lines_text.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                lines_removed += 1

        # 1. Secret Scanning
        has_secrets, secrets_detected = self._scan_for_secrets("\n".join(added_lines_text))

        # 2. Sensitive File Check
        has_sensitive_files = False
        sensitive_changes = []
        for file in files_changed:
            for pattern in self.SENSITIVE_FILE_PATTERNS:
                if re.search(pattern, file, re.IGNORECASE):
                    has_sensitive_files = True
                    sensitive_changes.append(file)
                    break

        # 3. Unexpected Files / Scope Creep
        unexpected_files = []
        if expected_files:
            expected_set = set(expected_files)
            for f in files_changed:
                if f not in expected_set and not any(exp in f for exp in expected_set):
                    unexpected_files.append(f)

        scope_creep = len(unexpected_files) > 0 or lines_added + lines_removed > 1000

        # 4. Dependency Changes
        dependency_changes = []
        for f in files_changed:
            if any(manifest in f for manifest in self.DEPENDENCY_MANIFESTS):
                dependency_changes.append({"file": f, "change_type": "modified"})

        # 5. Schema Migrations
        schema_migrations = [f for f in files_changed if "migration" in f.lower() or "schema" in f.lower()]

        # 6. API Changes
        api_changes = [f for f in files_changed if "api" in f.lower() or "route" in f.lower() or "endpoint" in f.lower()]

        # Risk Classification
        risk = TaskRisk.LOW
        if has_secrets or has_sensitive_files:
            risk = TaskRisk.CRITICAL
        elif len(files_changed) > 5 or scope_creep or schema_migrations:
            risk = TaskRisk.HIGH
        elif len(files_changed) > 2 or dependency_changes:
            risk = TaskRisk.MEDIUM

        summary = f"Diff: {len(files_changed)} files changed (+{lines_added}, -{lines_removed})."
        if has_secrets:
            summary += " CRITICAL: Secrets detected in diff!"
        elif scope_creep:
            summary += " WARNING: Unexpected files or high line count detected."

        return DiffAnalysis(
            files_changed=files_changed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            unexpected_files=unexpected_files,
            sensitive_changes=sensitive_changes,
            risk=risk,
            summary=summary,
            has_secrets=has_secrets,
            secrets_detected=secrets_detected,
            has_sensitive_files=has_sensitive_files,
            dependency_changes=dependency_changes,
            schema_migrations=schema_migrations,
            api_changes=api_changes,
            scope_creep_detected=scope_creep
        )

    def _extract_git_diff(self, worktree_path: Path, base_commit: str) -> Tuple[str, List[str]]:
        raw_diff_parts = []
        files = []

        try:
            # 1. Fast file status inspection via porcelain
            res_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=2
            )
            for line in res_status.stdout.splitlines():
                if len(line) > 2:
                    fpath = line[2:].strip()
                    if fpath:
                        files.append(fpath)

            # 2. Diff text against HEAD
            res_diff = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=False,
                timeout=2
            )
            if res_diff.stdout:
                raw_diff_parts.append(res_diff.stdout)

            # 3. Read untracked files diff content if untracked files exist
            for f in files:
                f_abs = worktree_path / f
                if f_abs.is_file():
                    try:
                        # Append untracked file content to diff for secret scanner
                        if f_abs.stat().st_size <= 200 * 1024:
                            with open(f_abs, "r", encoding="utf-8", errors="ignore") as file_obj:
                                file_text = file_obj.read()
                                prefixed_lines = "\n".join(f"+{l}" for l in file_text.splitlines())
                                raw_diff_parts.append(f"--- /dev/null\n+++ b/{f}\n" + prefixed_lines)
                    except Exception:
                        pass

            return "\n".join(raw_diff_parts), list(set(files))
        except Exception as e:
            logger.error(f"DiffAnalyzer: Exception extracting diff: {e}")
            return "", files

    def _scan_for_secrets(self, text: str) -> (bool, List[str]):
        detected = []
        for pattern, label in self.SECRET_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                detected.append(f"{label} (Pattern matched)")

        has_secrets = len(detected) > 0
        return has_secrets, detected


global_diff_analyzer = DiffAnalyzer()
