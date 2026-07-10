try:
    from .base_agent import BaseAgent
except ImportError:
    from agents.base_agent import BaseAgent


class ExplanationAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert programming teacher.

Explain concepts in simple language.

Use examples.

Be beginner friendly.
"""
        )