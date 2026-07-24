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

    def run(self, prompt_or_state, memory_context: str = "", previous_output: str = ""):
        if isinstance(prompt_or_state, dict):
            state = prompt_or_state
            architecture = str(state.get("architecture", ""))
            prompt = str(state.get("user_prompt", ""))
            plan = str(state.get("plan", ""))

            from backend.utils.summarizer import extract_backend_info
            db_info = extract_backend_info(plan, architecture)

            database_schema = super().run(
                f"Project: {prompt}\nDatabase Scope: {db_info}\nGenerate SQL Schema.",
                memory_context,
                previous_output
            )
            state["database"] = database_schema
            return state
        else:
            return super().run(str(prompt_or_state), memory_context, previous_output)

    async def run_async(self, prompt_or_state, memory_context: str = "", previous_output: str = ""):
        if isinstance(prompt_or_state, dict):
            state = prompt_or_state
            architecture = str(state.get("architecture", ""))
            prompt = str(state.get("user_prompt", ""))
            plan = str(state.get("plan", ""))

            from backend.utils.summarizer import extract_backend_info
            db_info = extract_backend_info(plan, architecture)

            database_schema = await super().run_async(
                f"Project: {prompt}\nDatabase Scope: {db_info}\nGenerate SQL Schema.",
                memory_context,
                previous_output
            )
            state["database"] = database_schema
            return state
        else:
            return await super().run_async(str(prompt_or_state), memory_context, previous_output)