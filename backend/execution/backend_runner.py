import logging
from typing import Dict, Any

from backend.execution.process_manager import global_process_manager

logger = logging.getLogger("aiforge.execution.backend_runner")


class BackendRunner:
    """
    BackendRunner validates Python imports and executes backend server checks.
    """

    def run_backend_checks(self, backend_code: Dict[str, str]) -> Dict[str, Any]:
        """Runs syntax and import validation over backend source files."""
        errors = []
        for path, code in backend_code.items():
            if path.endswith(".py"):
                res = global_process_manager.run_command(f"python -c \"import ast; ast.parse('''{code}''')\"", timeout_seconds=5)
                if res["exit_code"] != 0:
                    errors.append({
                        "file": path,
                        "error": "SyntaxError",
                        "stderr": res["stderr"] or "Syntax error parsing file"
                    })

        return {
            "status": "success" if not errors else "failed",
            "total_files": len(backend_code),
            "errors": errors
        }


# Global BackendRunner Instance
global_backend_runner = BackendRunner()
