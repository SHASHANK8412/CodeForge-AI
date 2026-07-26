import sys
import io
import logging
from typing import Dict, Any

from backend.plugins.sdk import BasePlugin

logger = logging.getLogger("aiforge.tools.python_runner")


class PythonRunnerTool(BasePlugin):
    name = "python_runner"
    version = "1.0.0"
    description = "Executes Python code snippets in a controlled environment"
    permissions = ["python_exec"]

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        code = params.get("code", "print('Hello AIForge')")
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()

        try:
            exec(code, {"__builtins__": __builtins__})
            out = redirected_output.getvalue()
            return {"status": "success", "output": out, "error": None}
        except Exception as e:
            return {"status": "error", "output": "", "error": str(e)}
        finally:
            sys.stdout = old_stdout


# Global PythonRunnerTool Instance
global_python_runner_tool = PythonRunnerTool()
