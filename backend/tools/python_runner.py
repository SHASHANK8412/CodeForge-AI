import os
import subprocess
import sys
import tempfile
import logging
from typing import Dict, Any

from backend.plugins.sdk import BasePlugin

logger = logging.getLogger("aiforge.tools.python_runner")

CODE_TOOLS_ENV = "AIFORGE_ENABLE_CODE_TOOLS"


def code_tools_enabled() -> bool:
    """
    Tools that run arbitrary code or commands are off unless explicitly enabled: the API that
    reaches them has no per-user authorization, so on by default would mean remote code execution.
    """
    return os.environ.get(CODE_TOOLS_ENV, "").strip().lower() in ("1", "true", "yes")


def run_python_snippet(code: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Run code in a separate, isolated interpreter (-I) in an empty temp dir, with a timeout."""
    with tempfile.TemporaryDirectory(prefix="aiforge_snippet_") as workdir:
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", code],
                cwd=workdir, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"status": "error", "output": "", "error": f"Timed out after {timeout:g}s", "exit_code": None}
    return {
        "status": "success" if proc.returncode == 0 else "error",
        "output": proc.stdout[-20000:],
        "error": proc.stderr[-20000:] or None,
        "exit_code": proc.returncode,
    }


class PythonRunnerTool(BasePlugin):
    name = "python_runner"
    version = "1.0.0"
    description = "Executes Python code snippets in a separate, isolated interpreter"
    permissions = ["python_exec"]

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if not code_tools_enabled():
            return {"status": "error", "output": "", "error": f"Code execution is disabled. Set {CODE_TOOLS_ENV}=1 to enable it."}
        return run_python_snippet(params.get("code", ""), timeout=float(params.get("timeout", 10)))


# Global PythonRunnerTool Instance
global_python_runner_tool = PythonRunnerTool()
