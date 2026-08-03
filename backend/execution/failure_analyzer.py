"""
AIForge Failure Analyzer
========================
Analyzes failing ExecutionResult or TestResult structures and produces a
typed FailureAnalysis for the SelfDebugController.
"""

import re
import logging
from backend.execution.models import ExecutionResult, TestResult, FailureAnalysis

_logger = logging.getLogger("aiforge.execution.failure_analyzer")


class FailureAnalyzer:
    """
    Categorizes execution/test failures into actionable bug reports.
    """

    def analyze(self, test_res: TestResult, code: str = "") -> FailureAnalysis:
        exec_res = test_res.execution_result
        stderr = exec_res.stderr if exec_res else ""
        stdout = exec_res.stdout if exec_res else ""

        err_combined = f"{stderr}\n{stdout}\n" + "\n".join(test_res.errors)

        if exec_res and exec_res.timed_out:
            return FailureAnalysis(
                failure_type="TIMEOUT",
                summary="Execution timed out due to infinite loop or unblocked operation.",
                likely_location="Loop condition or recursive call",
                action="Ensure loop termination conditions are met and step pointers update correctly."
            )

        if "SyntaxError" in err_combined:
            return FailureAnalysis(
                failure_type="SYNTAX_ERROR",
                summary="Python syntax error encountered during parsing.",
                likely_location="Syntax block / missing parenthesis or colon",
                action="Fix invalid syntax, missing colons, or unbalanced parentheses."
            )

        if "AssertionError" in err_combined:
            match = re.search(r"AssertionError:\s*(.*)", err_combined)
            msg = match.group(1) if match else "Assertion failed during test run."
            return FailureAnalysis(
                failure_type="ASSERTION_FAILURE",
                summary=f"Test assertion failed: {msg}",
                likely_location="Algorithm logic / boundary condition",
                action="Adjust loop bounds, equality checks, or edge case handling (e.g. left <= right)."
            )

        if "IndexError" in err_combined or "out of range" in err_combined:
            return FailureAnalysis(
                failure_type="BOUNDARY_ERROR",
                summary="Array index out of bounds error.",
                likely_location="Array index access",
                action="Add index boundary check (0 <= idx < len(arr))."
            )

        if "TypeError" in err_combined or "AttributeError" in err_combined:
            return FailureAnalysis(
                failure_type="TYPE_ERROR",
                summary="Type or attribute error encountered.",
                likely_location="Object attribute dereference / parameter type",
                action="Verify variable initialization and non-null object state before property access."
            )

        return FailureAnalysis(
            failure_type="RUNTIME_ERROR",
            summary="Runtime execution error encountered.",
            likely_location="Executable block",
            action="Fix runtime exception and re-run test suite."
        )


global_failure_analyzer = FailureAnalyzer()
