"""
AIForge Codebase Static Analysis Parser
=======================================
Parses Python, JS/TS, HTML/CSS, JSON, and config files to extract AST definitions:
Classes, Functions, APIs, Imports, Components, Database Tables, Environment Variables, and Dependencies.
"""

import os
import ast
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Set

_logger = logging.getLogger("aiforge.graph")


class CodebaseParser:
    """
    Parses source code files to build structured AST metadata representations.
    """

    def scan_file(self, file_path: Path, workspace_root: Path) -> Dict[str, Any]:
        rel_path = str(file_path.relative_to(workspace_root)).replace("\\", "/")
        file_ext = file_path.suffix.lower()

        info = {
            "file_path": rel_path,
            "ext": file_ext,
            "classes": [],
            "functions": [],
            "apis": [],
            "imports": [],
            "components": [],
            "db_tables": [],
            "env_vars": [],
            "dependencies": []
        }

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            _logger.error(f"Error reading file '{rel_path}': {e}")
            return info

        # Parse Python files via AST & Regex
        if file_ext == ".py":
            self._parse_python(content, rel_path, info)
        # Parse JS/TS/JSX/TSX files via Regex
        elif file_ext in [".js", ".jsx", ".ts", ".tsx"]:
            self._parse_javascript(content, rel_path, info)
        # Parse requirements.txt or package.json
        elif file_path.name in ["requirements.txt", "package.json"]:
            self._parse_dependencies(content, file_path.name, info)

        return info

    def _parse_python(self, content: str, rel_path: str, info: Dict[str, Any]) -> None:
        # Regex extraction for APIs & Env vars
        for line in content.splitlines():
            line_str = line.strip()
            # APIs / Routes
            route_match = re.search(r'@(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', line_str)
            if route_match:
                method, endpoint = route_match.groups()
                info["apis"].append({"method": method.upper(), "endpoint": endpoint, "line": line_str[:60]})

            # Env vars
            env_match = re.search(r'os\.(?:getenv|environ\.get)\(\s*["\']([^"\']+)["\']', line_str)
            if env_match:
                info["env_vars"].append(env_match.group(1))

        # AST parsing for Classes, Functions, Imports, DB tables
        try:
            tree = ast.parse(content, filename=rel_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    info["classes"].append(node.name)
                    # Check DB model inheritance
                    base_names = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    if any(b in ["Base", "Model", "DeclarativeBase"] for b in base_names):
                        info["db_tables"].append(node.name.lower() + "s")

                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    info["functions"].append(node.name)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info["imports"].append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        info["imports"].append(f"{module}.{alias.name}" if module else alias.name)
        except Exception:
            # Fallback regex parsing if AST fails
            funcs = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*', content)
            info["functions"].extend(funcs)
            info["classes"].extend(classes)

    def _parse_javascript(self, content: str, rel_path: str, info: Dict[str, Any]) -> None:
        # Functions & Components
        funcs = re.findall(r'(?:function|const|let)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:function|\([^)]*\)\s*=>)', content)
        named_funcs = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
        all_funcs = list(set(funcs + named_funcs))
        info["functions"].extend(all_funcs)

        # Components (Capitalized functions in JS/JSX)
        components = [f for f in all_funcs if f[0].isupper()]
        info["components"].extend(components)

        # Imports
        imports = re.findall(r'(?:import|require)\s*\(?[\s\S]*?from\s*["\']([^"\']+)["\']', content)
        info["imports"].extend(imports)

        # API fetch calls
        api_calls = re.findall(r'(?:fetch|axios\.(?:get|post|put|delete))\(\s*["\']([^"\']+)["\']', content)
        for ep in api_calls:
            info["apis"].append({"method": "GET/POST", "endpoint": ep, "line": f"Client API call to {ep}"})

        # Process Env
        env_vars = re.findall(r'process\.env\.([a-zA-Z_][a-zA-Z0-9_]*)', content)
        info["env_vars"].extend(env_vars)

    def _parse_dependencies(self, content: str, filename: str, info: Dict[str, Any]) -> None:
        if filename == "requirements.txt":
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    pkg = line.split("==")[0].split(">=")[0].strip()
                    info["dependencies"].append(pkg)
        elif filename == "package.json":
            try:
                import json
                data = json.loads(content)
                deps = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
                info["dependencies"].extend(deps)
            except Exception:
                pass
