from backend.services.ollama_service import OllamaService


class BaseAgent:

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.llm = OllamaService()

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

        return "\n\n".join(sections)

    def run(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ):
        final_prompt = self.build_prompt(user_prompt, memory_context, previous_output)
        return self.llm.generate(
            self.system_prompt,
            final_prompt
        )