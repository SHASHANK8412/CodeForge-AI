from backend.agents.base_agent import BaseAgent


class TestingAgent(BaseAgent):

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