from backend.services.ollama_service import OllamaService


class BaseAgent:

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.llm = OllamaService()

    def build_prompt(self, user_prompt: str, memory_context: str = "") -> str:

        if not memory_context:
            return user_prompt

        return f"""Memory Context
{memory_context}

Current Task
{user_prompt}"""

    def run(self, user_prompt: str, memory_context: str = ""):
        final_prompt = self.build_prompt(user_prompt, memory_context)
        return self.llm.generate(
            self.system_prompt,
            final_prompt
        )