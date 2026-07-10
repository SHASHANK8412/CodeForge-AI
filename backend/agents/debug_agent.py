try:
    from .base_agent import BaseAgent
except ImportError:
    from agents.base_agent import BaseAgent


class DebugAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert debugging assistant.

Find bugs.

Explain why they occur.

Provide corrected code.

Suggest improvements.
"""
        )