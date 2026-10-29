"""
AIForge Codebase Intelligence — Language-Aware Incremental Indexer
===================================================================
Scans software projects, computes file hashes, extracts structural symbols
(FastAPI routes, Pydantic schemas, SQLAlchemy models, React components, functions,
classes, imports, exports), and maintains an incremental index without reprocessing
unchanged files.
"""

import os
import re
import ast
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Tuple

_logger = logging.getLogger("aiforge.memory.codebase_indexer")

EXCLUDED_FILENAMES: Set[str] = {
    ".env", ".env.local", ".env.production", ".env.development", ".env.test",
    "credentials.json", "secrets.json", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"
}

EXCLUDED_EXTENSIONS: Set[str] = {
    ".pem", ".key", ".crt", ".cer", ".pfx", ".p12", ".pyc", ".pyo", ".pyd",
    ".db", ".sqlite", ".sqlite3", ".log", ".tmp", ".swp", ".bak"
}

EXCLUDED_DIRECTORIES: Set[str] = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules", "dist", "build",
    ".venv", "venv", "env", ".next", ".pytest_cache", ".coverage"
}


def is_secret_or_excluded_file(file_path: str) -> bool:
    """Returns True if the file matches secret patterns or excluded directories."""
    clean_p = file_path.replace("\\", "/")
    parts = clean_p.split("/")
    filename = parts[-1]

    # Check directory exclusion
    for part in parts[:-1]:
        if part in EXCLUDED_DIRECTORIES:
            return True

    # Check filename exclusion
    if filename in EXCLUDED_FILENAMES or filename.startswith(".env"):
        return True

    # Check extension exclusion
    ext = os.path.splitext(filename)[1].lower()
    if ext in EXCLUDED_EXTENSIONS:
        return True

    return False


def compute_file_hash(content: str) -> str:
    """Computes SHA256 hash of file text content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class CodebaseIndexer:
    """
    Language-aware codebase intelligence indexer supporting incremental updates.
    """

    def __init__(self, store_path: Optional[str] = None):
        if store_path is None:
            data_dir = Path(__file__).resolve().parent / "store"
            data_dir.mkdir(parents=True, exist_ok=True)
            store_path = str(data_dir / "codebase_index.json")
        self.store_file = Path(store_path)
        self._index: Dict[str, Dict[str, Any]] = {}  # { project_id: { file_path: file_meta } }
        self._load()

    def _load(self) -> None:
        if self.store_file.exists():
            try:
                raw = json.loads(self.store_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._index = raw
            except Exception as e:
                _logger.warning(f"Could not load codebase index file: {e}")
                self._index = {}

    def _save(self) -> None:
        try:
            self.store_file.parent.mkdir(parents=True, exist_ok=True)
            self.store_file.write_text(json.dumps(self._index, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.error(f"Could not save codebase index file: {e}")

    def extract_symbols(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Extracts structural symbols, imports, and exports based on file language.
        """
        ext = os.path.splitext(file_path)[1].lower()
        symbols: List[str] = []
        imports: List[str] = []
        exports: List[str] = []
        routes: List[Dict[str, str]] = []
        models: List[str] = []
        components: List[str] = []
        language = "text"

        if ext == ".py":
            language = "python"
            symbols, imports, exports, routes, models = self._parse_python(content)
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            language = "javascript" if ext in (".js", ".jsx") else "typescript"
            symbols, imports, exports, components = self._parse_javascript(content)
        elif ext == ".sql":
            language = "sql"
            symbols, models = self._parse_sql(content)
        elif ext in (".json", ".yaml", ".yml", ".toml"):
            language = "config"
        elif ext == ".md":
            language = "markdown"

        return {
            "language": language,
            "symbols": symbols,
            "imports": imports,
            "exports": exports,
            "routes": routes,
            "models": models,
            "components": components,
        }

    def _parse_python(self, content: str) -> Tuple[List[str], List[str], List[str], List[Dict[str, str]], List[str]]:
        symbols = []
        imports = []
        exports = []
        routes = []
        models = []

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    symbols.append(node.name)
                    # Check decorators for FastAPI routes
                    for dec in node.decorator_list:
                        dec_str = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                        if any(method in dec_str for method in (".get(", ".post(", ".put(", ".delete(", ".patch(")):
                            match = re.search(r'\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', dec_str)
                            if match:
                                routes.append({"method": match.group(1).upper(), "path": match.group(2), "handler": node.name})

                elif isinstance(node, ast.ClassDef):
                    symbols.append(node.name)
                    models.append(node.name)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    imports.append(mod)
                    for alias in node.names:
                        symbols.append(f"{mod}.{alias.name}" if mod else alias.name)

        except Exception:
            # Fallback regex parsing if AST syntax parsing fails
            for match in re.finditer(r"^(?:async\s+)?def\s+([a-zA-Z_0-9]+)\s*\(", content, re.MULTILINE):
                symbols.append(match.group(1))
            for match in re.finditer(r"^class\s+([a-zA-Z_0-9]+)", content, re.MULTILINE):
                symbols.append(match.group(1))
                models.append(match.group(1))
            for match in re.finditer(r"^(?:from\s+([a-zA-Z_0-9.]+)\s+import|import\s+([a-zA-Z_0-9.]+))", content, re.MULTILINE):
                imports.append(match.group(1) or match.group(2))
            for match in re.finditer(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', content):
                routes.append({"method": match.group(1).upper(), "path": match.group(2)})

        return list(dict.fromkeys(symbols)), list(dict.fromkeys(imports)), exports, routes, list(dict.fromkeys(models))

    def _parse_javascript(self, content: str) -> Tuple[List[str], List[str], List[str], List[str]]:
        symbols = []
        imports = []
        exports = []
        components = []

        # React Components & Functions
        for match in re.finditer(r"(?:export\s+(?:default\s+)?)?(?:function|const|class)\s+([A-Z][a-zA-Z0-9_]*)", content):
            comp_name = match.group(1)
            components.append(comp_name)
            symbols.append(comp_name)

        for match in re.finditer(r"(?:export\s+)?(?:async\s+)?function\s+([a-z][a-zA-Z0-9_]*)\s*\(", content):
            symbols.append(match.group(1))

        for match in re.finditer(r"(?:export\s+)?const\s+([a-z][a-zA-Z0-9_]*)\s*=\s*(?:async\s*)?\(", content):
            symbols.append(match.group(1))

        # Imports
        for match in re.finditer(r"import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]", content):
            imports.append(match.group(1))

        # Exports
        for match in re.finditer(r"export\s+(?:default\s+)?(?:const|function|class|let|var)?\s*([a-zA-Z0-9_]+)", content):
            exports.append(match.group(1))

        return list(dict.fromkeys(symbols)), list(dict.fromkeys(imports)), list(dict.fromkeys(exports)), list(dict.fromkeys(components))

    def _parse_sql(self, content: str) -> Tuple[List[str], List[str]]:
        tables = []
        for match in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+)", content, re.IGNORECASE):
            tables.append(match.group(1))
        return tables, tables

    def index_project_files(
        self,
        project_id: str,
        files_map: Dict[str, str],
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Incrementally indexes a project files map.
        Skips unchanged files based on SHA256 hash comparison.
        Returns indexing metrics (indexed_count, skipped_count, total_files).
        """
        proj_index = self._index.setdefault(project_id, {})
        indexed_count = 0
        skipped_count = 0
        indexed_files = []
        skipped_files = []

        for rel_path, content in files_map.items():
            clean_path = rel_path.replace("\\", "/").lstrip("/")

            # Exclude secrets, keys, and temp directories
            if is_secret_or_excluded_file(clean_path):
                _logger.info(f"Skipping excluded/secret file from indexing: {clean_path}")
                continue

            content_hash = compute_file_hash(content)
            existing_entry = proj_index.get(clean_path)

            # Incremental check: if hash matches and not force, skip re-indexing
            if not force_reindex and existing_entry and existing_entry.get("file_hash") == content_hash:
                skipped_count += 1
                skipped_files.append(clean_path)
                continue

            # Process & extract symbols
            analysis = self.extract_symbols(clean_path, content)
            now_iso = datetime.now(timezone.utc).isoformat()

            file_metadata = {
                "project_id": project_id,
                "path": clean_path,
                "file_hash": content_hash,
                "language": analysis["language"],
                "size": len(content.encode("utf-8")),
                "symbols": analysis["symbols"],
                "imports": analysis["imports"],
                "exports": analysis["exports"],
                "routes": analysis.get("routes", []),
                "models": analysis.get("models", []),
                "components": analysis.get("components", []),
                "last_indexed": now_iso,
            }

            proj_index[clean_path] = file_metadata
            indexed_count += 1
            indexed_files.append(clean_path)

        # Remove deleted files from index
        current_paths = set(p.replace("\\", "/").lstrip("/") for p in files_map.keys())
        deleted_paths = [p for p in proj_index.keys() if p not in current_paths]
        for dp in deleted_paths:
            del proj_index[dp]

        self._save()
        _logger.info(f"CodebaseIndexer for '{project_id}': Indexed {indexed_count} files, Skipped {skipped_count} unchanged files, Total {len(proj_index)}")

        return {
            "project_id": project_id,
            "indexed_count": indexed_count,
            "skipped_count": skipped_count,
            "total_files": len(proj_index),
            "indexed_files": indexed_files,
            "skipped_files": skipped_files,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_project_index(self, project_id: str) -> Dict[str, Any]:
        """Retrieves full codebase index metadata for a project."""
        return self._index.get(project_id, {})

    def find_files_by_symbol(self, project_id: str, symbol_name: str) -> List[str]:
        """Finds all file paths defining or importing a symbol."""
        proj_index = self.get_project_index(project_id)
        matching = []
        sym_lower = symbol_name.lower()

        for path, meta in proj_index.items():
            symbols = [s.lower() for s in meta.get("symbols", [])]
            models = [m.lower() for m in meta.get("models", [])]
            components = [c.lower() for c in meta.get("components", [])]
            imports = [i.lower() for i in meta.get("imports", [])]

            if any(sym_lower in s for s in symbols + models + components + imports):
                matching.append(path)

        return matching

    def search_codebase(self, project_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Searches project codebase index by path, symbol, route, or component."""
        proj_index = self.get_project_index(project_id)
        if not proj_index or not query.strip():
            return []

        q_terms = set(query.lower().split())
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for path, meta in proj_index.items():
            path_lower = path.lower()
            symbols = " ".join(meta.get("symbols", [])).lower()
            routes = " ".join(r.get("path", "") for r in meta.get("routes", [])).lower()
            components = " ".join(meta.get("components", [])).lower()

            score = 0.0
            for term in q_terms:
                if term in path_lower:
                    score += 5.0
                if term in symbols:
                    score += 3.0
                if term in routes:
                    score += 4.0
                if term in components:
                    score += 3.5

            if score > 0:
                scored.append((score, meta))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]


# Global CodebaseIndexer instance
global_codebase_indexer = CodebaseIndexer()
