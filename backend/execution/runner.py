import time
import logging
from typing import Dict, Any, List

from backend.execution.backend_runner import global_backend_runner
from backend.execution.frontend_runner import global_frontend_runner
from backend.execution.test_runner import global_test_runner
from backend.execution.docker_runner import global_docker_runner

logger = logging.getLogger("aiforge.execution.runner")


class ProjectExecutionEngine:
    """
    ProjectExecutionEngine detects project type, starts backend/frontend checks,
    runs unit tests, monitors process health, and captures runtime errors.
    """

    def execute_project(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        """Executes full project runtime checks across backend, frontend, unit tests, and Docker."""
        start_time = time.time()

        be_files = {k: v for k, v in project_files.items() if "backend" in k or k.endswith(".py")}
        fe_files = {k: v for k, v in project_files.items() if "frontend" in k or k.endswith((".jsx", ".js"))}
        test_files = {k: v for k, v in project_files.items() if "test" in k}
        docker_files = {k: v for k, v in project_files.items() if "Dockerfile" in k or "compose" in k}

        be_res = global_backend_runner.run_backend_checks(be_files)
        fe_res = global_frontend_runner.run_frontend_checks(fe_files)
        test_res = global_test_runner.run_unit_tests(test_files)
        docker_res = global_docker_runner.test_container_build(docker_files)

        all_errors = be_res.get("errors", []) + fe_res.get("errors", [])
        is_healthy = len(all_errors) == 0 and test_res["status"] == "passed"

        elapsed = round(time.time() - start_time, 3)
        logger.info(f"ProjectExecutionEngine completed runtime checks in {elapsed}s (Healthy: {is_healthy})")

        return {
            "is_healthy": is_healthy,
            "execution_time_seconds": elapsed,
            "backend_status": be_res["status"],
            "frontend_status": fe_res["status"],
            "test_status": test_res["status"],
            "errors": all_errors,
            "test_summary": test_res
        }


# Global ProjectExecutionEngine Instance
global_project_execution_engine = ProjectExecutionEngine()
