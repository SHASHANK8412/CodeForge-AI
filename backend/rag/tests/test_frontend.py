from backend.graph.workflow import graph

prompt = """
Create a modern React login page using Tailwind CSS.
"""

result = graph.invoke(
    {
        "session_id": "frontend_test",
        "prompt": prompt,
    }
)

print(result["response"])