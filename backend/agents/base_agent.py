from backend.services.llm import generate_text


class BaseAgent:

    def __init__(self, system_prompt, task_name: str = "general"):
        self.system_prompt = system_prompt
        self.task_name = task_name

    def build_prompt(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ) -> str:

        sections = []

        if memory_context:
            sections.append(f"Memory Context\n{memory_context}")

        if previous_output:
            sections.append(f"Previous Agent Output\n{previous_output}")

        sections.append(f"Current Task\n{user_prompt}")
        sections.append(
            "Response Format\n"
            "- Use Markdown headings and bullet points.\n"
            "- Start with a brief one-line summary.\n"
            "- Keep the response concise and structured.\n"
            "- Use code fences for code, commands, and config.\n"
            "- Avoid filler, greetings, and repeated wording."
        )

        return "\n\n".join(sections)

    def run(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ):
        final_prompt = self.build_prompt(user_prompt, memory_context, previous_output)
        return generate_text(self.system_prompt, final_prompt, task=self.task_name)