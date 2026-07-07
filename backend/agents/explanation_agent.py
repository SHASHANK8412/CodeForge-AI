from backend.agents.base_agent import BaseAgent


class ExplanationAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            """
You are an expert teacher.

Explain programming concepts in a simple way.

Use step-by-step explanations.

Give examples whenever possible.

Keep the explanation beginner-friendly.
"""
        )