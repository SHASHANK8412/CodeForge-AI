"""
AIForge Empirical Evaluation Test Runner
========================================
Executes project test suites inside physical project directories,
parsing exit codes, stdout, and stderr into EvaluationTestSummary models.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from backend.execution.project_runner import global_project_runner
from backend.execution.models import ExecutionResult
from backend.evaluation.models import EvaluationTestSummary

_logger = logging.getLogger("aiforge.evaluation.test_runner")


class EvaluationTestRunner:
    """
    Executes tests empirically in target project path using ProjectRunner sandbox executor.
    """

    def run_tests(self, project_path: str) -> Dict[str, Any]:
        """
        Executes pytest in project_path and parses test results.
        Returns Dict with:
        - summary: EvaluationTestSummary
        - raw_execution: ExecutionResult
        - failure_output: str
        """
        _logger.info(f"EvaluationTestRunner: Running tests for project at '{project_path}'...")
        exec_res: ExecutionResult = global_project_runner.run_project(project_path)

        stdout = exec_res.stdout or ""
        stderr = exec_res.stderr or ""
        output_text = stdout + "\n" + stderr

        # Parse pytest output metrics
        passed = 0
        failed = 0

        pass_match = re.search(r"(\d+)\s+passed", output_text, re.IGNORECASE)
        fail_match = re.search(r"(\d+)\s+failed", output_text, re.IGNORECASE)

        if pass_match:
            passed = int(pass_match.group(1))
        if fail_match:
            failed = int(fail_match.group(1))

        # Fallback if no pytest line was matched but exit code is 0
        if passed == 0 and failed == 0:
            if exec_res.exit_code == 0 and exec_res.status == "PASS":
                passed = 1
                failed = 0
            else:
                passed = 0
                failed = max(1, exec_res.exit_code)

        total = passed + failed
        success = (exec_res.exit_code == 0 and failed == 0 and exec_res.status == "PASS")

        summary = EvaluationTestSummary(
            total_tests=total,
            tests_passed=passed,
            tests_failed=failed,
            success=success
        )

        return {
            "summary": summary,
            "raw_execution": exec_res,
            "failure_output": output_text if not success else ""
        }


global_evaluation_test_runner = EvaluationTestRunner()
