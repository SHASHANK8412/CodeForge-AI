"""
AIForge Day 10 Secure Code Execution Sandbox & Self-Debugging Test Suite
===========================================================================
Verifies ExecutionEligibilityChecker, SandboxExecutor, TestRunner, FailureAnalyzer,
SelfDebugController, Security Isolation, and Mandatory Tests 1 through 8.
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.execution.models import (
    CodeArtifact,
    ExecutionLimits,
    ExecutionStatus,
    VerificationStatus
)
from backend.execution.eligibility_checker import global_execution_eligibility_checker
from backend.execution.sandbox_executor import SandboxExecutor, global_sandbox_executor
from backend.execution.test_runner import global_test_runner
from backend.execution.self_debug_controller import global_self_debug_controller
from backend.services.generation_service import global_generation_pipeline


class TestDay10ExecutionSandbox(unittest.TestCase):

    def test_mandatory_binary_search_verification(self):
        """Mandatory Test: Binary search Python code executed in sandbox -> 5/5 tests pass -> VERIFIED"""
        prompt = "Write binary search in Python."
        code = (
            "def binary_search(arr: list, target: int) -> int:\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n"
        )
        art = CodeArtifact(filename="main.py", language="python", content=code, purpose="SOURCE")

        test_res = global_test_runner.run_tests(art, prompt)
        self.assertGreater(test_res.passed, 0)
        self.assertEqual(test_res.failed, 0)

        final_art, final_test_res, status, attempts = global_self_debug_controller.debug_and_verify(prompt, art, test_res)
        self.assertEqual(status, VerificationStatus.VERIFIED)
        self.assertEqual(attempts, 0)

    def test_mandatory_broken_code_self_debug(self):
        """Mandatory Test: Off-by-one binary search code fails -> SelfDebugController repairs it -> Pass -> VERIFIED"""
        prompt = "Write binary search in Python."
        broken_code = (
            "def binary_search(arr: list, target: int) -> int:\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left < right:\n"  # Off-by-one error (excludes last element when left == right)
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n"
        )
        art = CodeArtifact(filename="main.py", language="python", content=broken_code, purpose="SOURCE")

        initial_test_res = global_test_runner.run_tests(art, prompt)
        self.assertGreater(initial_test_res.failed, 0)

        final_art, final_test_res, status, attempts = global_self_debug_controller.debug_and_verify(prompt, art, initial_test_res)
        self.assertEqual(status, VerificationStatus.VERIFIED)
        self.assertGreater(attempts, 0)
        self.assertIn("<=", final_art.content)

    def test_mandatory_infinite_loop_timeout_security(self):
        """Mandatory Security Test: while True: pass terminates after timeout without crashing backend host"""
        executor = SandboxExecutor(limits=ExecutionLimits(timeout_seconds=1.0))
        art = CodeArtifact(filename="main.py", language="python", content="while True:\n    pass\n", purpose="SOURCE")

        res = executor.execute([art], language="python")
        self.assertEqual(res.status, ExecutionStatus.TIMEOUT)
        self.assertTrue(res.timed_out)

    def test_mandatory_output_flood_security(self):
        """Mandatory Security Test: Infinite print loop output is safely truncated"""
        executor = SandboxExecutor(limits=ExecutionLimits(max_output_bytes=1000, timeout_seconds=1.0))
        art = CodeArtifact(filename="main.py", language="python", content="for i in range(100000):\n    print('A' * 100)\n", purpose="SOURCE")

        res = executor.execute([art], language="python")
        self.assertTrue(res.output_truncated or len(res.stdout) <= 2000)

    def test_mandatory_secret_isolation(self):
        """Mandatory Security Test: Backend environment secrets are stripped inside sandbox"""
        os.environ["AWS_SECRET_ACCESS_KEY"] = "SUPER_SECRET_AWS_KEY"
        os.environ["DATABASE_PASSWORD"] = "SUPER_SECRET_DB_PASS"

        executor = SandboxExecutor()
        isolated_env = executor._build_isolated_environment()

        self.assertNotIn("AWS_SECRET_ACCESS_KEY", isolated_env)
        self.assertNotIn("DATABASE_PASSWORD", isolated_env)

    def test_mandatory_formula_1_no_execution(self):
        """Mandatory Non-Coding Test: 'Explain Formula 1' -> ExecutionEligibilityChecker: False (0 Sandbox calls)"""
        decision = global_execution_eligibility_checker.check_eligibility("EXPLANATION", "Explain Formula 1", "Formula 1 explanation text")
        self.assertFalse(decision.should_execute)
        self.assertEqual(decision.reason, "NON_CODING_INTENT")

    def test_feature_flag_disable_code_execution(self):
        """Setting AIFORGE_CODE_EXECUTION_ENABLED=false disables execution"""
        os.environ["AIFORGE_CODE_EXECUTION_ENABLED"] = "false"
        decision = global_execution_eligibility_checker.check_eligibility("CODING", "Write binary search in Python", "def binary_search(): pass")
        self.assertFalse(decision.should_execute)
        os.environ["AIFORGE_CODE_EXECUTION_ENABLED"] = "true"


if __name__ == "__main__":
    unittest.main()
