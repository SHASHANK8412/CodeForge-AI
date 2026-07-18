from backend.agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert Software Architect and Senior Technical Lead.

When the user asks for a software project, do NOT generate code.

Create ONLY a short implementation plan with exactly these sections:

# Features

# Modules

# Development Plan

Rules:
- Maximum 300 words total.
- Use short bullet points, not paragraphs.
- No code, no explanations outside these sections.
            """,
            task_name="planner",
        )

    def run(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return super().run(prompt, memory_context, previous_output)

    async def run_async(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return await super().run_async(prompt, memory_context, previous_output)