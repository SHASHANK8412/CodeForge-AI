from backend.agents.base_agent import BaseAgent


class TestingAgent(BaseAgent):

    SYSTEM_PROMPT = """
You are an expert Software Testing Engineer.

Generate ONLY the most important test cases for the given code/project:

# Key Test Cases

# Edge Cases

Rules:
- Be concise. List only what matters most, not exhaustive coverage.
- Use short bullet points and brief code fences only where essential.
- No long explanations.
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