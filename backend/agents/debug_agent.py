from backend.agents.base_agent import BaseAgent


class DebugAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            """
You are a debugging expert.

Find bugs.

Explain why the bug occurs.

Suggest the best fix.

Improve the code.
"""
        )