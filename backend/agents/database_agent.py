from backend.agents.base_agent import BaseAgent


class DatabaseAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are an expert Database Engineer.

Generate a functional SQL schema script.
Include the SQL code inside markdown blocks annotated with the filepath in comments:
```sql
-- filepath: database/schema.sql
CREATE TABLE ...
```
Do NOT write bullet points, descriptions, or short summaries. Generate actual SQL database schema scripts.
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

Generate the actual SQL Database Schema. Include it in a code block with the filepath annotation.
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

Generate the actual SQL Database Schema. Include it in a code block with the filepath annotation.
"""
        )

        state["database"] = database_schema

        return state