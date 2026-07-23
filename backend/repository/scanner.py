"""
AIForge Repository Intelligence Scanner
========================================
Scans full repositories across Python, JavaScript, TypeScript, React, HTML, CSS, JSON, Markdown, and YAML files.
Extracts metadata: filename, language, imports, exports, functions, classes, routes, models, components, dependencies, size, last_modified.
"""

import os
import ast
import re
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.repository")


class RepositoryScanner:
    """
    Scans repository files and extracts language-specific AST & symbol metadata.
    """

    def scan_repository(self, workspace_root: str) -> Dict[str, Any]:
        root = Path(workspace_root)
        if not root.exists():
            return {"error": "Workspace path does not exist", "files": []}

        _logger.info(f"RepositoryScanner scanning workspace: '{workspace_root}'")
        file_metadata_list = []
        supported_exts = {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".md", ".yaml", ".yml"}

        scanned_count = 0
        language_counts = {}

        for current_root, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules", "dist", "build", ".venv", "venv", "brain", ".system_generated"]]
            for file_name in files:
                file_path = Path(current_root) / file_name
                ext = file_path.suffix.lower()

                if ext in supported_exts or file_name in ["Dockerfile", "docker-compose.yml"]:
                    scanned_count += 1
                    meta = self.extract_file_metadata(file_path, root)
                    file_metadata_list.append(meta)
                    lang = meta["language"]
                    language_counts[lang] = language_counts.get(lang, 0) + 1

        _logger.info(f"RepositoryScanner completed: Scanned {scanned_count} files across {len(language_counts)} languages.")
        return {
            "workspace_root": str(root),
            "scanned_files_count": scanned_count,
            "language_breakdown": language_counts,
            "file_metadata": file_metadata_list
        }

    def extract_file_metadata(self, file_path: Path, workspace_root: Path) -> Dict[str, Any]:
        rel_path = str(file_path.relative_to(workspace_root)).replace("\\", "/")
        file_ext = file_path.suffix.lower()
        stat = file_path.stat()

        lang_map = {
            ".py": "Python", ".js": "JavaScript", ".jsx": "React JS",
            ".ts": "TypeScript", ".tsx": "React TS", ".html": "HTML",
            ".css": "CSS", ".json": "JSON", ".md": "Markdown",
            ".yaml": "YAML", ".yml": "YAML"
        }
        language = lang_map.get(file_ext, "Config")

        meta = {
            "filename": rel_path,
            "language": language,
            "ext": file_ext,
            "imports": [],
            "exports": [],
            "functions": [],
            "classes": [],
            "routes": [],
            "models": [],
            "components": [],
            "dependencies": [],
            "size_bytes": stat.st_size,
            "last_modified": stat.st_mtime
        }

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return meta

        if file_ext == ".py":
            self._scan_python(content, rel_path, meta)
        elif file_ext in [".js", ".jsx", ".ts", ".tsx"]:
            self._scan_javascript(content, rel_path, meta)
        elif file_ext in [".json", ".yaml", ".yml", ".md"]:
            self._scan_config_or_doc(content, file_path.name, meta)

        return meta

    def _scan_python(self, content: str, rel_path: str, meta: Dict[str, Any]) -> None:
        for line in content.splitlines():
            line_str = line.strip()
            # Routes
            r_match = re.search(r'@(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', line_str)
            if r_match:
                meta["routes"].append(f"{r_match.group(1).upper()} {r_match.group(2)}")

        try:
            tree = ast.parse(content, filename=rel_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    meta["classes"].append(node.name)
                    meta["exports"].append(node.name)
                    # Check ORM model
                    if any(b.id in ["Base", "Model"] for b in node.bases if isinstance(b, ast.Name)):
                        meta["models"].append(node.name)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    meta["functions"].append(node.name)
                    meta["exports"].append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        meta["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for alias in node.names:
                        meta["imports"].append(f"{mod}.{alias.name}" if mod else alias.name)
        except Exception:
            funcs = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*', content)
            meta["functions"].extend(funcs)
            meta["classes"].extend(classes)

    def _scan_javascript(self, content: str, rel_path: str, meta: Dict[str, Any]) -> None:
        funcs = re.findall(r'(?:function|const|let)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:function|\([^)]*\)\s*=>)', content)
        named_funcs = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
        all_funcs = list(set(funcs + named_funcs))
        meta["functions"].extend(all_funcs)

        components = [f for f in all_funcs if f[0].isupper()]
        meta["components"].extend(components)

        imports = re.findall(r'(?:import|require)\s*\(?[\s\S]*?from\s*["\']([^"\']+)["\']', content)
        meta["imports"].extend(imports)

        exports = re.findall(r'export\s+(?:default\s+)?(?:function|class|const|var|let)\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
        meta["exports"].extend(exports)

    def _scan_config_or_doc(self, content: str, filename: str, meta: Dict[str, Any]) -> None:
        if filename == "requirements.txt":
            deps = [line.strip().split("==")[0].split(">=")[0] for line in content.splitlines() if line.strip() and not line.startswith("#")]
            meta["dependencies"].extend(deps)
        elif filename == "package.json":
            try:
                import json
                data = json.loads(content)
                meta["dependencies"].extend(list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys()))
            except Exception:
                pass
