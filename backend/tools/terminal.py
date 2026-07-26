import subprocess
import logging
from typing import Dict, Any

from backend.plugins.sdk import BasePlugin

logger = logging.getLogger("aiforge.tools.terminal")


class TerminalTool(BasePlugin):
    name = "terminal"
    version = "1.0.0"
    description = "Execute shell commands, capture stdout/stderr, and return exit codes"
    permissions = ["execute_commands"]

    def run_cmd(self, command: str, cwd: str = ".") -> Dict[str, Any]:
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "command": command
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command execution timed out (30s limit)",
                "command": command
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "command": command
            }

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        cmd = params.get("command", "")
        cwd = params.get("cwd", ".")
        return self.run_cmd(cmd, cwd)


# Global TerminalTool Instance
global_terminal_tool = TerminalTool()
