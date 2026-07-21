import re
import logging
from pathlib import Path
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.project_intelligence")

class ApiMapper:
    """
    Correlates frontend URL requests with backend routes endpoints mapping.
    """

    def __init__(self) -> None:
        self.endpoint_pattern = re.compile(r'@app\.(?:get|post|put|delete)\(["\']([^"\']+)["\']\)')
        self.fetch_pattern = re.compile(r'(?:fetch|axios\.(?:get|post))\(["\']([^"\']+)["\']\)')

    def map_apis(self, workspace_path: str) -> Dict[str, Any]:
        """
        Scans frontend and backend components, locating mapping pairs.
        """
        import os
        root = Path(workspace_path)
        backend_routes = []
        frontend_calls = []
        ignored_dirs = {".git", ".venv", "venv", "node_modules", ".gemini", "dist", "__pycache__", "build", ".pytest_cache", ".vscode", "generated_projects"}

        for r_dir, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                file_path = Path(r_dir) / file
                if file_path.suffix in (".py", ".js", ".jsx", ".ts", ".tsx"):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        # Find decorator routes in py
                        if file_path.suffix == ".py":
                            for route in self.endpoint_pattern.findall(content):
                                backend_routes.append({"file": file_path.name, "route": route})
                        # Find fetch calls in frontend js/jsx/ts/tsx
                        elif file_path.suffix in (".js", ".jsx", ".ts", ".tsx"):
                            for call in self.fetch_pattern.findall(content):
                                frontend_calls.append({"file": file_path.name, "endpoint_called": call})
                    except Exception as e:
                        _logger.error(f"Failed to scan API calls of {file_path.name}: {str(e)}")

        # Find matching pairs
        mappings = []
        for fc in frontend_calls:
            for br in backend_routes:
                if fc["endpoint_called"] in br["route"] or br["route"] in fc["endpoint_called"]:
                    mappings.append({
                        "frontend_file": fc["file"],
                        "backend_file": br["file"],
                        "route_matched": br["route"]
                    })

        return {
            "backend_endpoints": backend_routes,
            "frontend_calls": frontend_calls,
            "resolved_mappings": mappings
        }
