"""
AIForge Real Project Multi-File Directory Builder
=================================================
Assembles multi-file project workspace:
Formula-Racing/
├── frontend/
│   ├── App.jsx
│   ├── Home.jsx
│   ├── Cars.jsx
│   ├── Gallery.jsx
│   └── Login.jsx
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── cars.py
│   └── drivers.py
├── database/
│   └── schema.sql
├── docs/
├── docker/
└── README.md
"""

import json
import logging
import re
from pathlib import Path, PurePosixPath
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.builder")

_FENCE_RE = re.compile(r"```[ \t]*([A-Za-z0-9_+#.-]*)[^\n]*\n(.*?)```", re.DOTALL)
# "# filepath: backend/main.py", "// filepath: src/App.jsx", "-- file: schema.sql", "<!-- filepath: x -->"
_INLINE_PATH_RE = re.compile(
    r"^\s*(?:#|//|--|<!--|/\*)\s*(?:file\s*path|filepath|file|path)\s*[:=]\s*([^\s*>]+)",
    re.IGNORECASE,
)
# A heading/bold/backticked path on the line right before a fence: "### `backend/main.py`"
_HEADING_PATH_RE = re.compile(r"[`*#\s]*([\w][\w./-]*\.[A-Za-z0-9]{1,6})[`*:\s]*$")
KNOWN_TOP_DIRS = ("frontend/", "backend/", "database/", "tests/", "docs/", "docker/")


def _safe_rel_path(raw: str) -> Optional[str]:
    """Normalises an LLM-supplied path; returns None for absolute or escaping paths."""
    cleaned = raw.strip().strip("`'\"").replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    if not cleaned or cleaned.startswith("/") or re.match(r"^[A-Za-z]:", cleaned):
        return None
    parts = PurePosixPath(cleaned).parts
    if any(part == ".." for part in parts):
        return None
    return str(PurePosixPath(*parts))


def split_llm_files(text: str, default_path: str, prefix: str = "") -> Dict[str, str]:
    """Turns an agent's markdown answer into ``{relative_path: source}``.

    Agents are prompted to return fenced code blocks annotated with
    ``# filepath: ...``. Writing that markdown verbatim into ``main.py`` gives a
    file that cannot even be parsed, so every block is extracted on its own:

    * a block whose first line (or the line before the fence) names a path is
      written to that path, under ``prefix`` unless it already starts with a
      known top-level directory;
    * unnamed blocks are concatenated into ``default_path``;
    * text with no fences at all is treated as raw source for ``default_path``.
    """
    if not text or not text.strip():
        return {}

    matches = list(_FENCE_RE.finditer(text))
    if not matches:
        return {default_path: text.strip() + "\n"}

    files: Dict[str, str] = {}
    unnamed: List[str] = []
    for match in matches:
        body = match.group(2)
        lines = body.splitlines()
        path: Optional[str] = None

        if lines:
            inline = _INLINE_PATH_RE.match(lines[0])
            if inline:
                path = _safe_rel_path(inline.group(1))
                if path is None:
                    _logger.warning("Dropping code block with unsafe path %r", inline.group(1))
                    continue
                lines = lines[1:]

        if path is None:
            # Only look at the text between the previous fence and this one.
            gap_start = matches[matches.index(match) - 1].end() if matches.index(match) > 0 else 0
            preceding = text[gap_start: match.start()].rstrip().splitlines()
            if preceding and len(preceding[-1]) < 120:
                heading = _HEADING_PATH_RE.search(preceding[-1])
                if heading:
                    path = _safe_rel_path(heading.group(1))

        code = "\n".join(lines).strip("\n") + "\n"
        if path is None:
            unnamed.append(code)
            continue
        if prefix and not path.startswith(KNOWN_TOP_DIRS):
            path = f"{prefix.rstrip('/')}/{path}"
        files[path] = (files[path] + "\n" + code) if path in files else code

    if unnamed:
        joined = "\n\n".join(unnamed)
        files[default_path] = (files[default_path] + "\n" + joined) if default_path in files else joined
    return files


class StructuredProjectBuilder:
    """
    Assembles structured multi-file project workspace directories.
    """

    def assemble_real_project(
        self,
        project_name: str,
        plan_json: Dict[str, Any],
        arch_json: Dict[str, Any],
        frontend_code: str,
        backend_code: str,
        database_code: str,
        testing_code: str,
        docs_code: str
    ) -> Dict[str, Any]:
        _logger.info(f"StructuredProjectBuilder: Assembling real multi-file project for '{project_name}'...")

        safe_name = "".join([c if c.isalnum() or c in " -_" else "_" for c in project_name]).strip()
        files_manifest = {
            "frontend/src/App.jsx": frontend_code or "// React App Root",
            "frontend/src/components/Navbar.jsx": "// React Navbar Component",
            "frontend/src/pages/Home.jsx": "// React Home Page",
            "backend/main.py": backend_code or "# FastAPI Main App",
            "backend/models.py": "# SQLAlchemy Models",
            "backend/auth.py": "# JWT Authentication Middleware",
            "database/schema.sql": database_code or "-- SQL Database Schema",
            "tests/test_main.py": testing_code or "# Pytest Integration Tests",
            "docs/API.md": "# API Documentation",
            "docker/Dockerfile": "FROM python:3.11-alpine\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"-m\", \"uvicorn\", \"backend.main:app\"]",
            "README.md": docs_code or f"# {project_name}\n\nGenerated by AIForge Autonomous Engineering Platform."
        }

        # Replace the raw markdown answers with the real files they contain.
        for raw, default_path, prefix in (
            (frontend_code, "frontend/src/App.jsx", "frontend"),
            (backend_code, "backend/main.py", "backend"),
            (database_code, "database/schema.sql", "database"),
            (testing_code, "tests/test_main.py", "tests"),
        ):
            for rel_path, content in split_llm_files(raw, default_path, prefix).items():
                files_manifest[rel_path] = content

        return {
            "project_name": project_name,
            "safe_dir_name": safe_name,
            "total_files": len(files_manifest),
            "file_structure": list(files_manifest.keys()),
            "manifest": files_manifest
        }

    def write_project_to_disk(
        self,
        project_name: str,
        files_manifest: Dict[str, str],
        base_dir: str = "generated_projects"
    ) -> Path:
        """
        Safely writes files from manifest to generated_projects/<ProjectName>/ on disk.
        Enforces strict path traversal security checks to prevent writing outside target directory.
        """
        safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in project_name]).strip("_") or "AIForgeProject"
        base_path = Path(base_dir).resolve()
        target_dir = (base_path / safe_name).resolve()

        # Security check: ensure target_dir is strictly inside base_path
        if not str(target_dir).startswith(str(base_path)):
            raise ValueError(f"Unsafe project directory path: {target_dir}")

        target_dir.mkdir(parents=True, exist_ok=True)

        for rel_path_str, content in files_manifest.items():
            clean_rel = rel_path_str.replace("\\", "/").lstrip("/")
            if rel_path_str.startswith("/") or rel_path_str.startswith("\\"):
                raise ValueError(f"Absolute path rejected: {rel_path_str}")

            dest_path = (target_dir / clean_rel).resolve()

            # Path traversal security check
            if not str(dest_path).startswith(str(target_dir)):
                raise ValueError(f"Security Warning: Path traversal detected for path '{rel_path_str}'")

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content, encoding="utf-8")

        _logger.info(f"Successfully wrote {len(files_manifest)} files to disk at '{target_dir}'")
        return target_dir


global_structured_project_builder = StructuredProjectBuilder()

