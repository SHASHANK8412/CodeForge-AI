from backend.agents.base_agent import BaseAgent


class DatabaseAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are an expert Database Engineer.

Generate ONLY:

# SQL Schema

# Relationships

Rules:
- Be concise. Tables, key fields, and relationships only.
- No lengthy explanations.
- Maximum 400 words.
""",
            task_name="database",
        )

    def run(self, state):

        architecture = state.get("architecture", "")
        backend = state.get("backend", "")
        prompt = state.get("user_prompt", "")

        database_schema = self.generate(
            f"""
Project:

{prompt}

Architecture:

{architecture}

Backend:

{backend}

Generate ONLY the SQL Schema and Relationships. Do NOT generate full migration scripts.
"""
        )

        state["database"] = database_schema

        return state

    async def run_async(self, state):

        architecture = state.get("architecture", "")
        backend = state.get("backend", "")
        prompt = state.get("user_prompt", "")

        database_schema = await self.generate_async(
            f"""
Project:

{prompt}

Architecture:

{architecture}

Backend:

{backend}

Generate ONLY the SQL Schema and Relationships. Do NOT generate full migration scripts.
"""
        )

        state["database"] = database_schema

        return state