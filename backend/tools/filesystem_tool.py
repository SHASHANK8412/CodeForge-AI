import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from .base_tool import BaseTool

_logger = logging.getLogger("aiforge.tools")

class FilesystemTool(BaseTool):
    """
    Exposes filesystem read, write, append, and lists utility wrappers.
    """

    def __init__(self) -> None:
        super().__init__("FilesystemTool")

    def initialize(self) -> None:
        pass

    def validate(self, **kwargs) -> bool:
        path_str = kwargs.get("path", "")
        # Prevent accessing system root files or relative lookups outside workspace
        if ".." in path_str or path_str.startswith("/") or path_str.startswith("\\"):
            return False
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action", "")
        path_str = kwargs.get("path", "")
        content = kwargs.get("content", "")

        if not self.validate(path=path_str):
            return self._format_result(False, "", "Path parameter is outside whitelisted boundaries.", 0.0, 1)

        start = time.perf_counter()
        target = Path(path_str)
        try:
            if action == "read":
                if not target.exists():
                    return self._format_result(False, "", "Target file does not exist.", 0.0, 2)
                with open(target, "r", encoding="utf-8") as f:
                    output = f.read()
                return self._format_result(True, output, "", time.perf_counter() - start)
            
            elif action == "write":
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
                return self._format_result(True, f"Wrote content to {target.name} successfully.", "", time.perf_counter() - start)
            
            elif action == "list":
                if not target.exists() or not target.is_dir():
                    return self._format_result(False, "", "Directory does not exist.", 0.0, 3)
                files = [str(f.name) for f in target.iterdir()]
                return self._format_result(True, json.dumps(files), "", time.perf_counter() - start)

            else:
                return self._format_result(False, "", f"Unknown filesystem action '{action}'", 0.0, 4)
        except Exception as e:
            return self._format_result(False, "", f"Filesystem operation error: {str(e)}", time.perf_counter() - start, -1)

    def cleanup(self) -> None:
        pass

    def health_check(self) -> bool:
        return True
