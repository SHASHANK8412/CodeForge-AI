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