import subprocess
import time
import logging
from typing import Dict, Any

from .base_tool import BaseTool
from .safety.command_validator import CommandValidator

_logger = logging.getLogger("aiforge.tools")

class TerminalTool(BaseTool):
    """
    Secure subprocess execution terminal wrapper.
    """

    def __init__(self) -> None:
        super().__init__("TerminalTool")
        self.validator = CommandValidator()

    def initialize(self) -> None:
        pass

    def validate(self, **kwargs) -> bool:
        command = kwargs.get("command", "")
        return self.validator.validate_command(command)

    def execute(self, **kwargs) -> Dict[str, Any]:
        command = kwargs.get("command", "")
        cwd = kwargs.get("cwd", None)
        timeout = kwargs.get("timeout", 30)

        if not self.validate(command=command):
            return self._format_result(False, "", "Command failed security validation checklist", 0.0, 1)

        start_time = time.perf_counter()
        try:
            # Execute subprocess safely
            res = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = time.perf_counter() - start_time
            success = res.returncode == 0
            return self._format_result(
                success,
                res.stdout,
                res.stderr,
                elapsed,
                res.returncode,
                {"cwd": cwd}
            )
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - start_time
            return self._format_result(False, "", f"Command execution timed out after {timeout} seconds.", elapsed, -1)
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            return self._format_result(False, "", f"Failed to run subprocess: {str(e)}", elapsed, -2)

    def cleanup(self) -> None:
        pass

    def health_check(self) -> bool:
        # Verify shell is responsive
        try:
            res = subprocess.run("echo check", shell=True, capture_output=True)
            return res.returncode == 0
        except Exception:
            return False
