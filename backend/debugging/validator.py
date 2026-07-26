import logging
from typing import Dict, Any

from backend.execution.test_runner import global_test_runner

logger = logging.getLogger("aiforge.debugging.validator")


class RegressionValidator:
    """
    RegressionValidator runs regression unit tests after self-healing code patches
    to ensure no existing functionality was broken by the fix.
    """

    def validate_regression(self, patched_files: Dict[str, str]) -> Dict[str, Any]:
        test_files = {k: v for k, v in patched_files.items() if "test" in k}
        res = global_test_runner.run_unit_tests(test_files)

        no_regressions = res["status"] == "passed"
        logger.info(f"Regression testing validation status: {res['status']}")

        return {
            "no_regressions": no_regressions,
            "test_summary": res
        }


# Global RegressionValidator Instance
global_regression_validator = RegressionValidator()
