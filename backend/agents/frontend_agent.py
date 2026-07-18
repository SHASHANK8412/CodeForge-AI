from backend.agents.base_agent import BaseAgent


class FrontendAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            system_prompt="""
You are an expert React Frontend Engineer.

Generate ONLY:

# Components

# Folder Structure

# Routing

Rules:
- Do NOT generate full source code.
- Be extremely concise. Use short bullet points.
- Maximum 400 words.
""",
            task_name="frontend",
        )

    def run(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return super().run(prompt, memory_context, previous_output)

    async def run_async(self, prompt: str, memory_context: str = "", previous_output: str = ""):
        return await super().run_async(prompt, memory_context, previous_output)