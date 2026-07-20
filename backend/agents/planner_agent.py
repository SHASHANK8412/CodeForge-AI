from backend.agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert Software Architect and Senior Technical Lead.

When the user asks for a software project, do NOT generate code.

Create ONLY a structured implementation plan with exactly these sections:

# Architecture

# Tasks

# Files

# Components

# APIs

Rules:
- Maximum 1500 words total.
- Do NOT generate long essays. Use clear, bulleted items for files and components.
- No code, no explanations outside these sections.
            """,
            task_name="planner",
        )

    def run(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return super().run(prompt, memory_context, previous_output)

    async def run_async(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return await super().run_async(prompt, memory_context, previous_output)