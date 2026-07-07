from backend.agents.base_agent import BaseAgent


class CodingAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert software engineer.

Write clean Python code.

Explain your solution.

Provide examples whenever needed.
"""
        )