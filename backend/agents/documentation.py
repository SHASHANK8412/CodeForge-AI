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

    def run(self, state):

        prompt = state.get("user_prompt", "")
        plan = state.get("plan", "")
        architecture = state.get("architecture", "")
        frontend = state.get("frontend", "")
        backend = state.get("backend", "")
        database = state.get("database", "")

        documentation = self.generate(
            f"""
Generate ONLY a README.md for this project.

Project:

{prompt}

Plan:

{plan}

Architecture:

{architecture}

Frontend:

{frontend}

Backend:

{backend}

Database:

{database}

Return a professional README.md.
"""
        )

        state["documentation"] = documentation

        return state

    async def run_async(self, state):

        prompt = state.get("user_prompt", "")
        plan = state.get("plan", "")
        architecture = state.get("architecture", "")
        frontend = state.get("frontend", "")
        backend = state.get("backend", "")
        database = state.get("database", "")

        documentation = await self.generate_async(
            f"""
Generate ONLY a README.md for this project.

Project:

{prompt}

Plan:

{plan}

Architecture:

{architecture}

Frontend:

{frontend}

Backend:

{backend}

Database:

{database}

Return a professional README.md.
"""
        )

        state["documentation"] = documentation

        return state