from backend.agents.base_agent import BaseAgent


class TestingAgent(BaseAgent):

    SYSTEM_PROMPT = """
You are an expert Software Testing Engineer.

Analyze the given code and provide:

1. Possible Bugs
2. Edge Cases
3. Unit Tests
4. Time Complexity
5. Space Complexity
6. Code Quality Score (out of 10)
7. Suggestions for Improvement

Return the answer in a clean markdown format.
"""

    def __init__(self):
        super().__init__(self.SYSTEM_PROMPT, task_name="testing")

    def run(self, user_prompt, memory_context="", previous_output=""):
        prompt = f"""
Code to Analyze:

{user_prompt}
"""

        return super().run(prompt, memory_context, previous_output)

    def process(self, user_prompt, memory_context="", previous_output=""):
        return self.run(user_prompt, memory_context, previous_output)