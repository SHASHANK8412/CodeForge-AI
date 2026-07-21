import time
import subprocess
import logging
from typing import Dict, Any

from .base_tool import BaseTool

_logger = logging.getLogger("aiforge.tools")

class GitTool(BaseTool):
    """
    Exposes Git checkout, commit, status, and clone adapters.
    """

    def __init__(self) -> None:
        super().__init__("GitTool")

    def initialize(self) -> None:
        pass

    def validate(self, **kwargs) -> bool:
        cmd = kwargs.get("git_cmd", "")
        # Prevent push credentials leaks
        if "http" in cmd and "@" in cmd:
            return False
        return True

    def execute(self, **kwargs) -> Dict[str, Any]:
        git_cmd = kwargs.get("git_cmd", "status")
        cwd = kwargs.get("cwd", None)

        if not self.validate(git_cmd=git_cmd):
            return self._format_result(False, "", "Git command failed security validation.", 0.0, 1)

        start = time.perf_counter()
        full_command = f"git {git_cmd}"
        try:
            res = subprocess.run(
                full_command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            elapsed = time.perf_counter() - start
            return self._format_result(
                res.returncode == 0,
                res.stdout,
                res.stderr,
                elapsed,
                res.returncode
            )
        except Exception as e:
            return self._format_result(False, "", f"Git execute error: {str(e)}", time.perf_counter() - start, -1)

    def cleanup(self) -> None:
        pass

    def health_check(self) -> bool:
        try:
            res = subprocess.run("git --version", shell=True, capture_output=True)
            return res.returncode == 0
        except Exception:
            return False
