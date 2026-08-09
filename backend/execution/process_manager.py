import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("aiforge.execution.process_manager")


class ProcessManager:
    """
    ProcessManager spawns, tracks, and terminates background execution processes safely.
    """

    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}

    def run_command(self, cmd: str, cwd: str = ".", timeout_seconds: int = 15) -> Dict[str, Any]:
        """Runs a command synchronously with timeout handling."""
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "command": cmd
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_seconds} seconds.",
                "command": cmd
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "command": cmd
            }


# Global ProcessManager Instance
global_process_manager = ProcessManager()
