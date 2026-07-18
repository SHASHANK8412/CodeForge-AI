from backend.agents.base_agent import BaseAgent


class ArchitectAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an Expert Software Architect.

Your job is NOT to generate code.

You receive a software implementation plan. Expand it into a concise
architecture with exactly these sections:

# Architecture

# Folder Structure

# Database Choice

# API Design

Rules:
- Maximum 500 words total.
- Use short bullet points, not paragraphs.
- No code, no explanations outside these sections.
""",
        task_name="architect",
        )

    def run(self, plan: str, memory_context: str = "", previous_output: str = ""):
        return super().run(plan, memory_context, previous_output)

    async def run_async(self, plan: str, memory_context: str = "", previous_output: str = ""):
        return await super().run_async(plan, memory_context, previous_output)