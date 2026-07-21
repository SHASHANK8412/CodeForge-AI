import re
import logging
from pathlib import Path
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.knowledge")

class APIExtractor:
    """
    Statically analyzes route endpoints (REST API paths, HTTP methods) inside Python routes.
    """

    def __init__(self) -> None:
        pass

    def extract_endpoints(self, workspace_path: str) -> List[Dict[str, str]]:
        """
        Parses routers decorator routes mapping paths and methods.
        """
        root = Path(workspace_path)
        endpoints: List[Dict[str, str]] = []
        
        # FastAPI router decorator search regex
        route_pattern = re.compile(r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']')

        for file_path in root.glob("backend/**/*.py"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                matches = route_pattern.findall(content)
                for method, path in matches:
                    endpoints.append({
                        "file": file_path.name,
                        "method": method.upper(),
                        "path": path
                    })
            except Exception as e:
                _logger.error(f"Skipping API endpoint scrape on file {file_path.name}: {str(e)}")

        return endpoints
