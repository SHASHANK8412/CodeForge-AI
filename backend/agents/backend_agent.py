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

    def run(self, prompt_or_state, memory_context: str = "", previous_output: str = ""):
        if isinstance(prompt_or_state, dict):
            state = prompt_or_state
            architecture = str(state.get("architecture", ""))
            plan = str(state.get("plan", ""))
            prompt = str(state.get("user_prompt", ""))

            from backend.utils.summarizer import extract_backend_info
            backend_info = extract_backend_info(plan, architecture)

            backend_code = super().run(
                f"Project: {prompt}\nBackend Scope: {backend_info}\nGenerate FastAPI Backend.",
                memory_context,
                previous_output
            )
            state["backend"] = backend_code
            return state
        else:
            return super().run(str(prompt_or_state), memory_context, previous_output)

    async def run_async(self, prompt_or_state, memory_context: str = "", previous_output: str = ""):
        if isinstance(prompt_or_state, dict):
            state = prompt_or_state
            architecture = str(state.get("architecture", ""))
            plan = str(state.get("plan", ""))
            prompt = str(state.get("user_prompt", ""))

            from backend.utils.summarizer import extract_backend_info
            backend_info = extract_backend_info(plan, architecture)

            backend_code = await super().run_async(
                f"Project: {prompt}\nBackend Scope: {backend_info}\nGenerate FastAPI Backend.",
                memory_context,
                previous_output
            )
            state["backend"] = backend_code
            return state
        else:
            return await super().run_async(str(prompt_or_state), memory_context, previous_output)