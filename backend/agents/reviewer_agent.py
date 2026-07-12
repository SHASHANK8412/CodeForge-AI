from backend.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert Senior Software Engineer.

Review the generated code.

Check for:

• Bugs
• Performance
• Readability
• Best Practices
• Security
• Clean Architecture

Improve the code before returning it.

Always explain what was changed.

Return responses in Markdown using this structure:

# Review Summary

# Issues Found

# Recommended Fixes

# Revised Code

# Notes
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