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
        from backend.utils.summarizer import extract_backend_info
        architecture = state.get("architecture", "")
        prompt = state.get("user_prompt", "")
        plan = state.get("plan", "")

        db_info = extract_backend_info(plan, architecture)

        database_schema = self.generate(
            f"""
Project:
{prompt}

Database and Table Architecture Scope:
{db_info}

Generate the actual SQL Database Schema. Include it in a code block with the filepath annotation.
"""
        )

        state["database"] = database_schema
        return state

    async def run_async(self, state):
        from backend.utils.summarizer import extract_backend_info
        architecture = state.get("architecture", "")
        prompt = state.get("user_prompt", "")
        plan = state.get("plan", "")

        db_info = extract_backend_info(plan, architecture)

        database_schema = await self.generate_async(
            f"""
Project:
{prompt}

Database and Table Architecture Scope:
{db_info}

Generate the actual SQL Database Schema. Include it in a code block with the filepath annotation.
"""
        )

        state["database"] = database_schema
        return state