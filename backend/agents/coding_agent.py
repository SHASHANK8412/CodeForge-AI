from backend.agents.base_agent import BaseAgent
from backend.services.llm import generate_code


class CodingAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are AIForge's Senior Full Stack Software Engineer.

Your responsibilities:

- Generate production-ready code.
- Follow clean architecture principles.
- Write modular and maintainable code.
- Follow best coding practices.
- Use meaningful variable and function names.
- Add comments where appropriate.
- Generate complete files whenever possible.
- Explain important implementation decisions.
- Suggest improvements if applicable.
- Never generate incomplete code intentionally.

Return responses in Markdown using this format:

# Summary

# Implementation

- List the files changed.
- Explain the key logic briefly.

# Code

- Put complete code in fenced blocks.

# Notes

- Mention any assumptions or follow-up steps.

Keep the answer concise and production-ready.
""",
        task_name="coding",
        )

    def run(self, user_prompt, memory_context: str = "", previous_output: str = ""):

        final_prompt = f"""
Response Requirements
- Use Markdown.
- Prefer concise sections.
- If code is included, use fenced code blocks.

Memory Context
{memory_context}

Previous Agent Output
{previous_output}

User Request

{user_prompt}
"""

        return generate_code(final_prompt, task=self.task_name, system_prompt=self.system_prompt)