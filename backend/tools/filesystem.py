import os
import logging
from pathlib import Path
from typing import Dict, Any, List

from backend.plugins.sdk import BasePlugin

logger = logging.getLogger("aiforge.tools.filesystem")


class FilesystemTool(BasePlugin):
    name = "filesystem"
    version = "1.0.0"
    description = "Read, write, list, and delete files on local filesystem"
    permissions = ["read_files", "write_files"]

    def read_file(self, path: str) -> str:
        p = Path(path)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""

    def write_file(self, path: str, content: str) -> bool:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return True

    def list_dir(self, path: str = ".") -> List[str]:
        p = Path(path)
        if p.exists() and p.is_dir():
            return [f.name for f in p.iterdir()]
        return []

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        action = params.get("action", "read")
        path = params.get("path", "")
        content = params.get("content", "")

        if action == "read":
            res = self.read_file(path)
            return {"content": res, "path": path}
        elif action == "write":
            success = self.write_file(path, content)
            return {"success": success, "path": path}
        elif action == "list":
            files = self.list_dir(path or ".")
            return {"files": files, "path": path}

        return {"error": f"Unknown action '{action}'"}


# Global FilesystemTool Instance
global_filesystem_tool = FilesystemTool()
