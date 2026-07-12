from backend.agents.base_agent import BaseAgent


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

    def run(self, user_prompt: str, memory_context: str = "", previous_output: str = ""):
        return super().run(user_prompt, memory_context, previous_output)