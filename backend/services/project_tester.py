import logging
import re
from pathlib import Path
from typing import Dict, Any, List

from backend.execution.project_runner import global_project_runner
from backend.execution.models import ExecutionStatus

logger = logging.getLogger("aiforge.services.project_tester")


class ProjectTester:
    """
    ProjectTester runs automated test suites for a generated project on disk.
    - Scans for generated unit test scripts.
    - Executes pytest or npm test in a sandboxed, controlled manner.
    - Parses stdout/stderr outputs to extract pass/fail statistics.
    """

    def run_tests(self, project_path_str: str) -> Dict[str, Any]:
        logger.info(f"[TESTER] Starting test execution for project path: {project_path_str}")

        proj_path = Path(project_path_str).resolve()
        if not proj_path.exists() or not proj_path.is_dir():
            return {
                "overall_status": "FAIL",
                "message": "Project directory not found on disk.",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "output": "No execution occurred: path not found.",
                "failures": ["Project folder missing."]
            }

        # 1. Detect if tests exist
        test_files = list(proj_path.glob("**/test_*.py")) + list(proj_path.glob("**/*test*.js")) + list(proj_path.glob("**/*spec*.js"))
        has_tests = len(test_files) > 0
        logger.info(f"[TESTER] Detected {len(test_files)} test file(s).")

        # 2. Execute project check/tests
        exec_res = global_project_runner.run_project(str(proj_path))

        # Default fallback values
        passed = 0
        failed = 0
        total = 0
        failures = []
        status = "PASS" if exec_res.exit_code == 0 else "FAIL"

        # 3. Parse pytest output if python project
        stdout = exec_res.stdout or ""
        stderr = exec_res.stderr or ""
        combined = f"{stdout}\n{stderr}"

        if "pytest" in exec_res.language.lower() or any(p.name.endswith(".py") for p in test_files):
            # Try to match pytest summary line: e.g. "5 passed, 1 failed, 2 warnings in 0.15s"
            # Or "3 passed in 0.10s"
            summary_match = re.search(r"=\s*([\d]+)\s+passed(?:,\s*([\d]+)\s+failed)?", combined)
            if summary_match:
                passed = int(summary_match.group(1))
                failed = int(summary_match.group(2) or 0)
                total = passed + failed
            else:
                # Fallback: check if we see "collected X items"
                collected_match = re.search(r"collected (\d+) items", combined)
                if collected_match:
                    total = int(collected_match.group(1))
                    if exec_res.exit_code == 0:
                        passed = total
                    else:
                        # Estimate failures if exit code non-zero
                        failed = 1
                        passed = max(0, total - 1)

            # Extract failure messages (AssertionError lines etc.)
            for line in combined.splitlines():
                if "FAILURES" in line or "AssertionError" in line or "E   " in line:
                    failures.append(line.strip())

        # 4. Parse Node/Jest output
        elif "javascript" in exec_res.language.lower() or "typescript" in exec_res.language.lower():
            # Match jest patterns: "Tests:       5 passed, 5 total"
            passed_match = re.search(r"(\d+)\s+passing", combined)
            failed_match = re.search(r"(\d+)\s+failing", combined)
            if passed_match:
                passed = int(passed_match.group(1))
                failed = int(failed_match.group(1) if failed_match else 0)
                total = passed + failed
            else:
                # Generic fallback for node
                if exec_res.exit_code == 0:
                    passed = len(test_files)
                    total = len(test_files)
                else:
                    failed = 1
                    total = len(test_files)

        else:
            # If no tests were found and runner just compiled python successfully
            if not has_tests:
                if exec_res.exit_code == 0:
                    status = "PASS"
                    message = "Structural & compilation checks passed. No user tests found."
                else:
                    status = "FAIL"
                    message = "Structural/compilation checks failed."
                
                return {
                    "overall_status": status,
                    "message": message,
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "output": combined,
                    "failures": [stderr] if stderr else []
                }

        # Final status evaluation
        if failed > 0:
            status = "FAIL"
        elif total > 0 and passed == total:
            status = "PASS"

        result = {
            "overall_status": status,
            "message": f"Executed {total} tests: {passed} passed, {failed} failed.",
            "total": total,
            "passed": passed,
            "failed": failed,
            "output": combined,
            "failures": failures[:10]  # Cap failure logs
        }

        logger.info(f"[TESTER] Test execution finished. Status={status}, Total={total}, Passed={passed}, Failed={failed}")
        return result


# Global ProjectTester Instance
global_project_tester = ProjectTester()
