from backend.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert Senior Software Engineer.

Review the given output. Generate ONLY the improvements needed:

# Improvements

Rules:
- Maximum 300 words.
- Short, actionable bullet points only (bugs, security, performance,
  readability, best practices).
- Do NOT rewrite or return full code.
""",
        task_name="reviewer",
        )

    def run(self, user_prompt: str, memory_context: str = "", previous_output: str = ""):
        review_prompt = f"""
Generated Code
{previous_output}

User Request
{user_prompt}
"""

        return super().run(review_prompt, memory_context, previous_output)

    async def run_async(self, user_prompt: str, memory_context: str = "", previous_output: str = ""):
        review_prompt = f"""
Generated Code
{previous_output}

User Request
{user_prompt}
"""

        return await super().run_async(review_prompt, memory_context, previous_output)