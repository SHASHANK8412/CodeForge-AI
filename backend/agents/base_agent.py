from backend.services.ollama_service import OllamaService


class BaseAgent:

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.llm = OllamaService()

    def run(self, user_prompt):
        return self.llm.generate(
            self.system_prompt,
            user_prompt
        )