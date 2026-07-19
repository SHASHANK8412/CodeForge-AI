from backend.agents.base_agent import BaseAgent


class BackendAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are an expert FastAPI Backend Engineer.

Generate a functional FastAPI application backend.
Include the Python code files inside markdown blocks annotated with the filepath in comments:
```python
# filepath: backend/main.py
from fastapi import FastAPI
...
```
Do NOT write bullet points, descriptions, or short summaries. Generate actual FastAPI backend code.
""",
            task_name="backend",
        )

    def run(self, state):

        architecture = state.get("architecture", "")
        plan = state.get("plan", "")
        prompt = state.get("user_prompt", "")

        backend_code = self.generate(
            f"""
Project:
{prompt}

Plan:
{plan}

Architecture:
{architecture}

Generate the actual FastAPI backend implementation. Include it in a code block with the filepath annotation.
"""
        )

        state["backend"] = backend_code

        return state

    async def run_async(self, state):

        architecture = state.get("architecture", "")
        plan = state.get("plan", "")
        prompt = state.get("user_prompt", "")

        backend_code = await self.generate_async(
            f"""
Project:
{prompt}

Plan:
{plan}

Architecture:
{architecture}

Generate the actual FastAPI backend implementation. Include it in a code block with the filepath annotation.
"""
        )

        state["backend"] = backend_code

        return state