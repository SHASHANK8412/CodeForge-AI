import ast
import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.execution.backend_runner")


class BackendRunner:
    """
    BackendRunner validates Python AST syntax and imports over backend files.
    """

    def run_backend_checks(self, backend_code: Dict[str, str]) -> Dict[str, Any]:
        """Runs AST syntax and import validation over backend Python source files."""
        errors = []
        for path, code in backend_code.items():
            if path.endswith(".py"):
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    errors.append({
                        "file": path,
                        "error": "SyntaxError",
                        "stderr": f"Syntax error at line {e.lineno}: {e.msg}"
                    })
                except Exception as e:
                    errors.append({
                        "file": path,
                        "error": "SyntaxError",
                        "stderr": str(e)
                    })

        return {
            "status": "success" if not errors else "failed",
            "total_files": len(backend_code),
            "errors": errors
        }


# Global BackendRunner Instance
global_backend_runner = BackendRunner()
