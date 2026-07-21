import re
import logging
from pathlib import Path
from typing import Dict, List, Set

_logger = logging.getLogger("aiforge.project_intelligence")

class DependencyScanner:
    """
    Statically analyzes file import headers to construct dependency trees.
    """

    def __init__(self) -> None:
        # Regex mappings for imports
        self.py_import_pattern = re.compile(r'^(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.,\s]+))')
        self.js_import_pattern = re.compile(r'import\s+.*\s+from\s+["\']([^"\']+)["\']')

    def scan_project(self, workspace_path: str) -> Dict[str, List[str]]:
        """
        Scans workspace directory recursively and maps import links.
        """
        import os
        root = Path(workspace_path)
        dep_graph: Dict[str, List[str]] = {}
        ignored_dirs = {".git", ".venv", "venv", "node_modules", ".gemini", "dist", "__pycache__", "build", ".pytest_cache", ".vscode", "generated_projects"}

        for r_dir, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                file_path = Path(r_dir) / file
                if file_path.suffix in (".py", ".js", ".jsx", ".ts", ".tsx"):
                    rel_path = str(file_path.relative_to(root)).replace("\\", "/")
                    dep_graph[rel_path] = self.scan_file_imports(file_path)

        return dep_graph

    def scan_file_imports(self, file_path: Path) -> List[str]:
        imports = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    # Python
                    if file_path.suffix == ".py":
                        match = self.py_import_pattern.match(line.strip())
                        if match:
                            imp = match.group(1) or match.group(2)
                            imports.append(imp.strip())
                    # JS/TS
                    elif file_path.suffix in (".js", ".jsx", ".ts", ".tsx"):
                        match = self.js_import_pattern.search(line.strip())
                        if match:
                            imports.append(match.group(1).strip())
        except Exception as e:
            _logger.error(f"Failed to scan imports of file {file_path.name}: {str(e)}")
            
        return imports
