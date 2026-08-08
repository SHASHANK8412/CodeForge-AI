"""
AIForge Repository Scanner
==========================
Walks approved workspace root directories, enforces path traversal security,
applies ignore rules, redacts secret credentials, and extracts metadata.
"""

import os
import re
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from backend.repository.models import RepositoryInfo, FileRecord

_logger = logging.getLogger("aiforge.repository.scanner")

MAX_INDEXABLE_FILE_SIZE = 500 * 1024  # 500 KB limit for inline file indexing


class RepositoryScanner:
    """
    Scans and indexes approved repository root directories safely.
    """

    IGNORE_DIRS = {
        ".git", "node_modules", "venv", ".venv", "__pycache__",
        "dist", "build", "coverage", ".next", "target", "vendor", ".idea", ".vscode",
        ".worktrees", ".claude", "workspace", "workspace_test_env", "generated_projects", "logs"
    }

    BINARY_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".zip", ".tar", ".gz",
        ".pdf", ".exe", ".dll", ".so", ".dylib", ".pyc", ".db", ".sqlite"
    }

    SECRET_PATTERNS = [
        (r"(?i)(api[_-]?key|secret|password|auth[_-]?token|private[_-]?key)\s*[:=]\s*['\"]([^'\"]+)['\"]", r"\1: '[REDACTED]'"),
        (r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]"),
        (r"bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", "Bearer [REDACTED_TOKEN]"),
        (r"postgres://[^:]+:[^@]+@", "postgres://[REDACTED]:[REDACTED]@"),
        (r"mongodb(?:\+srv)?://[^:]+:[^@]+@", "mongodb://[REDACTED]:[REDACTED]@")
    ]

    def validate_path_safety(self, root_path: str, target_path: str) -> str:
        """
        Validates that target_path resides strictly inside root_path (Prevents path traversal).
        """
        abs_root = os.path.abspath(root_path)
        abs_target = os.path.abspath(os.path.join(abs_root, target_path))

        if not abs_target.startswith(abs_root):
            _logger.error(f"[SecurityError] Path traversal attempt blocked: '{target_path}' outside root '{root_path}'")
            raise PermissionError(f"Security Error: Access to path outside workspace root is blocked: '{target_path}'")

        return abs_target

    def scan_repository(self, root_path: str) -> Tuple[RepositoryInfo, List[FileRecord]]:
        abs_root = os.path.abspath(root_path)
        if not os.path.exists(abs_root):
            raise FileNotFoundError(f"Repository root directory does not exist: {abs_root}")

        repo_name = os.path.basename(abs_root) or "repository"
        repo_id = hashlib.md5(abs_root.encode("utf-8")).hexdigest()[:10]

        file_records: List[FileRecord] = []
        languages = set()
        frameworks = set()
        package_managers = set()
        test_frameworks = set()

        total_files = 0
        source_files = 0
        total_lines = 0

        for dirpath, dirnames, filenames in os.walk(abs_root):
            # Exclude ignored and hidden directories
            dirnames[:] = [d for d in dirnames if d not in self.IGNORE_DIRS and not d.startswith(".")]

            for fname in filenames:
                total_files += 1
                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, abs_root).replace("\\", "/")

                ext = os.path.splitext(fname)[1].lower()

                # Binary detection
                is_binary = ext in self.BINARY_EXTENSIONS
                file_size = os.path.getsize(full_path)

                lang = self._detect_language(fname, ext)
                purpose = self._detect_purpose(rel_path, fname, ext)

                if lang != "unknown":
                    languages.add(lang)

                if purpose in ["SOURCE", "TEST"]:
                    source_files += 1

                # Detect frameworks and managers from config files
                self._detect_manifest_metadata(fname, full_path, frameworks, package_managers, test_frameworks)

                # Compute SHA-256 content hash
                content_hash = ""
                if not is_binary and purpose == "SOURCE" and file_size <= 100 * 1024:
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            raw_content = f.read()
                            total_lines += raw_content.count("\n") + 1
                            content_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
                    except Exception:
                        pass

                rec = FileRecord(
                    path=rel_path,
                    language=lang,
                    size_bytes=file_size,
                    purpose=purpose,
                    hash=content_hash,
                    is_binary=is_binary
                )
                file_records.append(rec)

        repo_info = RepositoryInfo(
            repository_id=repo_id,
            root_path=abs_root,
            name=repo_name,
            languages=sorted(list(languages)),
            frameworks=sorted(list(frameworks)),
            package_managers=sorted(list(package_managers)),
            test_frameworks=sorted(list(test_frameworks)),
            file_count=total_files,
            source_file_count=source_files,
            estimated_lines=total_lines
        )

        return repo_info, file_records

    def redact_secrets(self, content: str) -> str:
        """Redacts secret API keys, tokens, and credentials from text before LLM context entry."""
        if not content:
            return content
        clean_text = content
        for pattern, replacement in self.SECRET_PATTERNS:
            clean_text = re.sub(pattern, replacement, clean_text)
        return clean_text

    def _detect_language(self, fname: str, ext: str) -> str:
        if ext in [".py"]:
            return "python"
        elif ext in [".js", ".jsx"]:
            return "javascript"
        elif ext in [".ts", ".tsx"]:
            return "typescript"
        elif ext in [".java"]:
            return "java"
        elif ext in [".json"]:
            return "json"
        elif ext in [".yaml", ".yml"]:
            return "yaml"
        elif ext in [".sql"]:
            return "sql"
        elif ext in [".html", ".css"]:
            return "html"
        return "unknown"

    def _detect_purpose(self, rel_path: str, fname: str, ext: str) -> str:
        rel_lower = rel_path.lower()
        if "test" in rel_lower or fname.startswith("test_") or fname.endswith("_test.py") or fname.endswith(".spec.js"):
            return "TEST"
        if fname in ["package.json", "requirements.txt", "pyproject.toml", "pom.xml", "build.gradle", "vite.config.js"]:
            return "CONFIG"
        if ext in [".md", ".rst", ".txt"]:
            return "DOCUMENTATION"
        if ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".sql"]:
            return "SOURCE"
        return "UNKNOWN"

    def _detect_manifest_metadata(self, fname: str, full_path: str, frameworks: set, pkg_managers: set, test_fw: set):
        if fname == "package.json":
            pkg_managers.add("npm")
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                    if "react" in txt:
                        frameworks.add("React")
                    if "vite" in txt:
                        frameworks.add("Vite")
                    if "express" in txt:
                        frameworks.add("Express")
                    if "next" in txt:
                        frameworks.add("Next.js")
                    if "vitest" in txt:
                        test_fw.add("vitest")
                    if "jest" in txt:
                        test_fw.add("jest")
            except Exception:
                pass
        elif fname in ["requirements.txt", "pyproject.toml"]:
            pkg_managers.add("pip")
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                    if "fastapi" in txt:
                        frameworks.add("FastAPI")
                    if "django" in txt:
                        frameworks.add("Django")
                    if "flask" in txt:
                        frameworks.add("Flask")
                    if "pytest" in txt:
                        test_fw.add("pytest")
            except Exception:
                pass
        elif fname == "pom.xml":
            pkg_managers.add("maven")
            frameworks.add("Spring Boot")
            test_fw.add("JUnit")


global_repository_scanner = RepositoryScanner()
global_secret_scanner = global_repository_scanner

