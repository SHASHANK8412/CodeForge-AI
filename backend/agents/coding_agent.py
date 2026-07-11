from backend.agents.base_agent import BaseAgent
from backend.services.llm import generate_code


class CodingAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert software engineer.

Write clean Python code.

Explain your solution when requested.

Provide examples whenever useful.
"""
        )

    def run(self, user_prompt):

        final_prompt = f"""
{self.system_prompt}

User Request:

{user_prompt}
"""

        return generate_code(final_prompt)