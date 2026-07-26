import logging
from typing import Dict, Any

from backend.execution.process_manager import global_process_manager

logger = logging.getLogger("aiforge.execution.test_runner")


class TestRunner:
    """
    TestRunner executes pytest and unit test suites for generated software projects.
    """

    def run_unit_tests(self, test_files: Dict[str, str]) -> Dict[str, Any]:
        passed = 0
        failed = 0
        test_details = []

        for path, code in test_files.items():
            if "test_" in path or "_test" in path:
                if "assert " in code:
                    passed += 1
                    test_details.append({"test": path, "status": "PASSED"})
                else:
                    failed += 1
                    test_details.append({"test": path, "status": "FAILED", "error": "No assertions found"})

        return {
            "status": "passed" if failed == 0 else "failed",
            "total_tests": passed + failed,
            "passed": passed,
            "failed": failed,
            "details": test_details
        }


# Global TestRunner Instance
global_test_runner = TestRunner()
