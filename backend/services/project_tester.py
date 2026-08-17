import time
import logging
import re
from pathlib import Path
from typing import Dict, Any, List

from backend.execution.project_runner import global_project_runner
from backend.execution.error_classifier import global_error_classifier

logger = logging.getLogger("aiforge.services.project_tester")


class ProjectTester:
    """
    ProjectTester runs automated test suites for a generated project on disk.
    - Scans for generated unit test scripts.
    - Executes pytest or npm test in a sandboxed, controlled manner.
    - Parses stdout/stderr outputs to extract pass/fail statistics, failed test names,
      stack traces, and categorized failure evidence for the autonomous debug loop.
    """

    def run_tests(self, project_path_str: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        logger.info(f"[TESTER] Starting test execution for project path: {project_path_str}")

        proj_path = Path(project_path_str).resolve()
        if not proj_path.exists() or not proj_path.is_dir():
            return {
                "overall_status": "FAIL",
                "message": "Project directory not found on disk.",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "command_executed": "pytest -q tests/",
                "exit_code": 1,
                "stdout": "",
                "stderr": "Project directory not found on disk.",
                "output": "No execution occurred: path not found.",
                "failed_tests": [],
                "stack_traces": ["Project directory not found on disk."],
                "failure_category": "CONFIGURATION_ERROR",
                "failures": ["Project folder missing."],
                "duration": round(time.perf_counter() - start_time, 2),
            }

        # 1. Detect if tests exist
        test_files = list(proj_path.glob("**/test_*.py")) + list(proj_path.glob("**/*test*.js")) + list(proj_path.glob("**/*spec*.js"))
        has_tests = len(test_files) > 0
        logger.info(f"[TESTER] Detected {len(test_files)} test file(s).")

        # 2. Execute project check/tests
        exec_res = global_project_runner.run_project(str(proj_path))
        elapsed_sec = round(time.perf_counter() - start_time, 2)

        # Default fallback values
        passed = 0
        failed = 0
        total = 0
        failures = []
        failed_tests = []
        stack_traces = []
        status = "PASS" if exec_res.exit_code == 0 else "FAIL"

        stdout = exec_res.stdout or ""
        stderr = exec_res.stderr or ""
        combined = f"{stdout}\n{stderr}"
        command_exec = f"pytest -q tests/" if any(p.name.endswith(".py") for p in test_files) else "npm test"

        # 3. Parse pytest output if python project
        if "pytest" in exec_res.language.lower() or any(p.name.endswith(".py") for p in test_files):
            # Parse failed test names (e.g. FAILED tests/test_auth.py::test_jwt_login)
            for match in re.finditer(r"FAILED\s+([^\s:]+::[^\s\n]+)", combined):
                failed_tests.append(match.group(1))

            # Parse tracebacks
            in_traceback = False
            curr_trace = []
            for line in combined.splitlines():
                if "Traceback (most recent call last)" in line or line.startswith("E   ") or "AssertionError" in line:
                    in_traceback = True
                if in_traceback:
                    curr_trace.append(line)
                    if line.startswith("FAILED ") or (line.strip().startswith("=") and len(curr_trace) > 3):
                        stack_traces.append("\n".join(curr_trace))
                        curr_trace = []
                        in_traceback = False
            if curr_trace:
                stack_traces.append("\n".join(curr_trace))

            # Match pytest summary line: e.g. "5 passed, 1 failed in 0.15s"
            summary_match = re.search(r"=\s*([\d]+)\s+passed(?:,\s*([\d]+)\s+failed)?", combined)
            if summary_match:
                passed = int(summary_match.group(1))
                failed = int(summary_match.group(2) or 0)
                total = passed + failed
            else:
                collected_match = re.search(r"collected (\d+) items", combined)
                if collected_match:
                    total = int(collected_match.group(1))
                    if exec_res.exit_code == 0:
                        passed = total
                    else:
                        failed = max(1, len(failed_tests))
                        passed = max(0, total - failed)

            for line in combined.splitlines():
                if "FAILURES" in line or "AssertionError" in line or "E   " in line:
                    failures.append(line.strip())

        # 4. Parse Node/Jest output
        elif "javascript" in exec_res.language.lower() or "typescript" in exec_res.language.lower():
            passed_match = re.search(r"(\d+)\s+passing", combined)
            failed_match = re.search(r"(\d+)\s+failing", combined)
            if passed_match:
                passed = int(passed_match.group(1))
                failed = int(failed_match.group(1) if failed_match else 0)
                total = passed + failed
            else:
                if exec_res.exit_code == 0:
                    passed = len(test_files)
                    total = len(test_files)
                else:
                    failed = 1
                    total = len(test_files)

        else:
            if not has_tests:
                if exec_res.exit_code == 0:
                    status = "PASS"
                    message = "Structural & compilation checks passed. No user tests found."
                else:
                    status = "FAIL"
                    message = "Structural/compilation checks failed."
                
                cat = global_error_classifier.classify(combined)
                return {
                    "overall_status": status,
                    "message": message,
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "command_executed": command_exec,
                    "exit_code": exec_res.exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "output": combined,
                    "failed_tests": [],
                    "stack_traces": [stderr] if stderr else [],
                    "failure_category": cat if status == "FAIL" else "NONE",
                    "failures": [stderr] if stderr else [],
                    "duration": elapsed_sec,
                }

        # Final status evaluation
        if failed > 0 or exec_res.exit_code != 0:
            status = "FAIL"
        elif total > 0 and passed == total:
            status = "PASS"

        cat = global_error_classifier.classify(combined) if status == "FAIL" else "NONE"

        result = {
            "overall_status": status,
            "message": f"Executed {total} tests: {passed} passed, {failed} failed.",
            "total": total,
            "passed": passed,
            "failed": failed,
            "command_executed": command_exec,
            "exit_code": exec_res.exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "output": combined,
            "failed_tests": failed_tests,
            "stack_traces": stack_traces[:5] if stack_traces else ([stderr] if stderr else []),
            "failure_category": cat,
            "failures": failures[:10],
            "duration": elapsed_sec,
        }

        logger.info(f"[TESTER] Test execution finished. Status={status}, Total={total}, Passed={passed}, Failed={failed}, Category={cat}")
        return result


# Global ProjectTester Instance
global_project_tester = ProjectTester()

