import re
from typing import Dict, Any, List, Optional
from backend.agents.base_agent import BaseAgent
from backend.execution.models import TestResult, TestFailureDetail


class TestingAgent(BaseAgent):
    __test__ = False

    SYSTEM_PROMPT = """

You are an expert Software Testing Engineer. You are given real generated backend and frontend
source code directly in the prompt — write tests against the actual functions, routes, and
components shown, not generic placeholders.

Generate four labeled test suites, each as one fenced code block annotated with a filepath
comment, in this exact order:

## Unit Tests
```python
# filepath: tests/test_unit.py
def test_...():
    ...
```

## Integration Tests
```python
# filepath: tests/test_integration.py
def test_...():
    ...
```

## API Tests
```python
# filepath: tests/test_api.py
from fastapi.testclient import TestClient
def test_...():
    ...
```

## End-to-End Tests
```python
# filepath: tests/test_e2e.py
def test_...():
    ...
```

Rules:
- Each suite must contain multiple distinct `def test_...` functions covering different
  scenarios (happy path, edge cases, and at least one negative/failure case per suite).
- Do NOT repeat the same test scenario across suites — each suite validates a different concern.
- Do NOT write bullet points, summaries, or descriptions outside the four labeled sections.
- Generate actual executable pytest code, not placeholders like `pass` or `assert True`.
"""

    def __init__(self):
        super().__init__(self.SYSTEM_PROMPT, task_name="testing")

    def run(self, user_prompt, memory_context="", previous_output=""):
        prompt = f"""
Code to Analyze:

{user_prompt}
"""

        return super().run(prompt, memory_context, previous_output)

    async def run_async(self, user_prompt, memory_context="", previous_output=""):
        prompt = f"""
Code to Analyze:

{user_prompt}
"""

        return await super().run_async(prompt, memory_context, previous_output)

    def process(self, user_prompt, memory_context="", previous_output=""):
        return self.run(user_prompt, memory_context, previous_output)

    async def process_async(self, user_prompt, memory_context="", previous_output=""):
        return await self.run_async(user_prompt, memory_context, previous_output)

    def evaluate_execution_results(
        self,
        exec_results: Dict[str, Any],
        project_spec: Optional[Dict[str, Any]] = None,
        architecture: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """
        Parses raw execution evidence from ProjectRunner / SandboxExecutor,
        maps failures against project requirements, and constructs a structured TestResult.
        """
        if not exec_results:
            return TestResult(
                success=False,
                passed=0,
                failed=1,
                total=1,
                errors=["No execution results provided."],
                summary="Verification failed: No execution results available."
            )

        stdout = str(exec_results.get("stdout", ""))
        stderr = str(exec_results.get("stderr", ""))
        exit_code = exec_results.get("exit_code", -1)
        raw_status = str(exec_results.get("status", "FAIL")).upper()

        combined_text = f"{stdout}\n{stderr}"
        failures_list = []
        errors_list = []

        # Parse pytest failure lines
        failed_matches = re.findall(r"FAILED\s+([^\s:]+)::([^\s\-]+)\s*-\s*(.*)", combined_text)
        for filepath, testfunc, err_msg in failed_matches:
            failures_list.append(TestFailureDetail(
                test_name=testfunc,
                error=err_msg.strip(),
                file=filepath,
                requirement=self._map_test_to_requirement(testfunc, project_spec)
            ))
            errors_list.append(f"{testfunc} failed in {filepath}: {err_msg.strip()}")

        passed_count = 0
        failed_count = 0
        p_match = re.search(r"(\d+)\s+passed", combined_text)
        if p_match:
            passed_count = int(p_match.group(1))

        f_match = re.search(r"(\d+)\s+failed", combined_text)
        if f_match:
            failed_count = int(f_match.group(1))
        elif failures_list:
            failed_count = len(failures_list)

        total_count = passed_count + failed_count
        if total_count == 0 and exit_code == 0:
            passed_count = 1
            total_count = 1

        is_success = (exit_code == 0 and failed_count == 0 and raw_status in ["PASS", "SUCCESS", "EXECUTIONSTATUS.PASS"])

        if is_success:
            summary_text = f"Project verification PASSED ({passed_count}/{total_count} checks passed)."
        else:
            if errors_list:
                err_summary = "; ".join(errors_list[:3])
            elif stderr:
                err_summary = stderr[:300]
            else:
                err_summary = f"Command failed with exit code {exit_code}"
            summary_text = f"Project verification FAILED ({failed_count} failures): {err_summary}"

        return TestResult(
            success=is_success,
            passed=passed_count,
            failed=failed_count,
            total=total_count,
            failures=failures_list,
            errors=errors_list or ([stderr] if stderr else []),
            summary=summary_text,
            duration_ms=float(exec_results.get("duration_ms", 0.0))
        )

    def _map_test_to_requirement(self, test_name: str, project_spec: Optional[Dict[str, Any]]) -> str:
        if not project_spec:
            return ""
        reqs = project_spec.get("functional_requirements") or project_spec.get("requirements", [])
        for req in reqs:
            req_str = str(req).lower()
            if any(term in req_str for term in test_name.lower().split("_")):
                return str(req)
        return ""