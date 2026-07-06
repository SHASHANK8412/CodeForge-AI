from ollama import chat
from backend.config import OLLAMA_MODEL

def generate_response(prompt: str):
    response = chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]