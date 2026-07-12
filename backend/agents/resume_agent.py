from backend.agents.base_agent import BaseAgent


class ResumeAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an ATS resume expert.

Improve resumes.

Improve LinkedIn profiles.

Suggest professional bullet points.
"""
        )

    def run(self, user_prompt: str, memory_context: str = "", previous_output: str = ""):
        return super().run(user_prompt, memory_context, previous_output)