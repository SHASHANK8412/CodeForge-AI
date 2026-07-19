from backend.agents.base_agent import BaseAgent


class TestingAgent(BaseAgent):

    SYSTEM_PROMPT = """
You are an expert Software Testing Engineer.

Generate functional pytest unit and integration test scripts.
Include the Python test code inside markdown blocks annotated with the filepath in comments:
```python
# filepath: tests/test_app.py
def test_endpoints():
    ...
```
Do NOT write bullet points, summaries, or descriptions. Generate actual executable pytest code files.
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