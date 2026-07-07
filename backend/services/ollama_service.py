import ollama


class OllamaService:

    def generate(self, system_prompt, user_prompt):

        response = ollama.chat(
            model="qwen2.5",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        return response["message"]["content"]