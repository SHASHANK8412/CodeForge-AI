"""
AIForge Repository Understanding Agent
======================================
Analyzes existing project repository architecture, file hierarchy, imports, APIs, dependencies, and coding conventions.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.pair_programmer")

class RepositoryAgent:
    """
    Parses repository files, builds dependency graphs, and selects relevant context files.
    """

    def analyze_repository(self, workspace_path: str) -> Dict[str, Any]:
        root = Path(workspace_path)
        if not root.exists():
            return {"error": "Workspace path does not exist", "files": []}

        file_tree = []
        dependencies = set()
        api_endpoints = []
        imports = set()

        for current_root, dirs, files in os.walk(root):
            # Skip hidden and cache folders
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["__pycache__", "node_modules", "dist", "build"]]
            for file in files:
                rel = Path(current_root).relative_to(root) / file
                file_tree.append(str(rel).replace("\\", "/"))

                # Basic static analysis on python/js files
                if file.endswith((".py", ".js", ".jsx", ".ts", ".tsx")):
                    try:
                        full_p = Path(current_root) / file
                        content = full_p.read_text(encoding="utf-8", errors="ignore")
                        for line in content.splitlines():
                            line_str = line.strip()
                            if line_str.startswith(("import ", "from ", "require(")):
                                imports.add(line_str[:50])
                            if "@app.get" in line_str or "@app.post" in line_str or "app.get(" in line_str:
                                api_endpoints.append(line_str[:60])
                    except Exception:
                        pass

        _logger.info(f"RepositoryAgent analyzed workspace '{workspace_path}': Found {len(file_tree)} files.")
        return {
            "workspace_path": str(root),
            "total_files": len(file_tree),
            "file_tree": file_tree[:50], # Top 50 files summary
            "api_endpoints": api_endpoints[:10],
            "detected_imports": list(imports)[:15],
            "architecture": "FastAPI + React" if any("main.py" in f for f in file_tree) else "Modular Web App"
        }

    def select_relevant_context(self, repo_analysis: Dict[str, Any], prompt: str) -> List[str]:
        """
        Intelligently selects relevant files for context loading based on task prompt.
        """
        prompt_lower = prompt.lower()
        file_tree = repo_analysis.get("file_tree", [])
        selected = []

        for f in file_tree:
            f_lower = f.lower()
            if "logging" in prompt_lower or "log" in prompt_lower:
                if any(k in f_lower for k in ["main.py", "route", "api", "middleware"]):
                    selected.append(f)
            elif "auth" in prompt_lower or "jwt" in prompt_lower:
                if any(k in f_lower for k in ["auth", "user", "token", "middleware"]):
                    selected.append(f)
            elif "dark mode" in prompt_lower or "theme" in prompt_lower:
                if any(k in f_lower for k in ["theme", "style", "css", "nav", "app", "context"]):
                    selected.append(f)
            elif "database" in prompt_lower or "query" in prompt_lower or "db" in prompt_lower:
                if any(k in f_lower for k in ["db", "database", "model", "schema", "crud"]):
                    selected.append(f)

        if not selected:
            selected = file_tree[:5] # Default fallback context files

        return selected[:10] # Cap at top 10 relevant files
