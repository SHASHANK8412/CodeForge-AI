from backend.services.llm import generate_text


class OllamaService:

    def generate(self, system_prompt, user_prompt):
        return generate_text(system_prompt, user_prompt, task="general")
