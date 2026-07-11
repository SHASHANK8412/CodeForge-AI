from ollama import chat


def generate_response(prompt):
    response = chat(
        model="qwen2.5-coder",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response["message"]["content"]


def generate_code(prompt):
    system_prompt = """
You are an expert software engineer.

Generate clean, production-quality code.

Return only the code unless the user explicitly asks for an explanation.
"""

    response = chat(
        model="qwen2.5-coder",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]