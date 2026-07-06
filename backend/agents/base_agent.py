from backend.services.llm import generate_response


class BaseAgent:

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt

    def run(self, user_prompt):

        prompt = f"""
{self.system_prompt}

User:
{user_prompt}
"""

        return generate_response(prompt)