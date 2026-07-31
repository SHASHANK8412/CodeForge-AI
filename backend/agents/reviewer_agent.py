from backend.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert Senior Software Engineer performing a real code review on real generated
source code (frontend, backend, database) that you are given directly in the prompt — do not
assume you are reviewing a summary or file list.

An automated duplicate-code scan result is included in the prompt. Reference those findings by
file name instead of re-deriving your own duplicate analysis.

Generate ONLY the findings needed, one per line, each prefixed with a severity tag:

# Findings

- [Critical] ... (security vulnerabilities, data loss, broken auth)
- [Major] ... (bugs, missing error handling, the duplicate blocks flagged by the scan)
- [Minor] ... (readability, naming, style, minor performance)

Rules:
- Maximum 1000 words.
- Every line must start with [Critical], [Major], or [Minor].
- Reference actual code you were shown (function/route/table names), not generic advice.
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