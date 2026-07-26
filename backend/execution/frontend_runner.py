import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.execution.frontend_runner")


class FrontendRunner:
    """
    FrontendRunner validates React JSX component structures and frontend assets.
    """

    def run_frontend_checks(self, frontend_code: Dict[str, str]) -> Dict[str, Any]:
        errors = []
        for path, code in frontend_code.items():
            if "export default" not in code and "export function" not in code and path.endswith((".jsx", ".js")):
                errors.append({
                    "file": path,
                    "error": "ExportMissing",
                    "stderr": "Component lacks export statement"
                })

        return {
            "status": "success" if not errors else "failed",
            "total_files": len(frontend_code),
            "errors": errors
        }


# Global FrontendRunner Instance
global_frontend_runner = FrontendRunner()
