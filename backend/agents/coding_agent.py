from backend.agents.base_agent import BaseAgent


class CodingAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            """
You are an expert software engineer.

Explain concepts clearly.

Write clean Python code.

Always provide examples.
"""
        )