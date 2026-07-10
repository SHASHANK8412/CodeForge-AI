try:
    from .base_agent import BaseAgent
except ImportError:
    from agents.base_agent import BaseAgent


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