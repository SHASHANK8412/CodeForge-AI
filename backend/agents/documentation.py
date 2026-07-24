from backend.agents.base_agent import BaseAgent


class DocumentationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are a Senior Technical Writer.

Generate ONLY a concise README.md with:

# Project Title
# Description
# Features
# Installation
# Usage

Rules:
- Be concise. Maximum 400 words.
- No filler text.
""",
            task_name="documentation",
        )

    def run(self, prompt_or_state, memory_context: str = "", previous_output: str = ""):
        if isinstance(prompt_or_state, dict):
            state = prompt_or_state
            prompt = str(state.get("user_prompt", ""))
            plan = str(state.get("plan", ""))
            architecture = str(state.get("architecture", ""))

            documentation = super().run(
                f"Project: {prompt}\nPlan: {plan}\nArchitecture: {architecture}\nGenerate README.md",
                memory_context,
                previous_output
            )
            state["documentation"] = documentation
            return state
        else:
            return super().run(str(prompt_or_state), memory_context, previous_output)

    async def run_async(self, prompt_or_state, memory_context: str = "", previous_output: str = ""):
        if isinstance(prompt_or_state, dict):
            state = prompt_or_state
            prompt = str(state.get("user_prompt", ""))
            plan = str(state.get("plan", ""))
            architecture = str(state.get("architecture", ""))

            documentation = await super().run_async(
                f"Project: {prompt}\nPlan: {plan}\nArchitecture: {architecture}\nGenerate README.md",
                memory_context,
                previous_output
            )
            state["documentation"] = documentation
            return state
        else:
            return await super().run_async(str(prompt_or_state), memory_context, previous_output)