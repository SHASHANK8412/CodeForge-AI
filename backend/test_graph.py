from backend.graph.workflow import graph

result = graph.invoke(
    {
        "prompt": "Write a Python calculator",
        "response": "",
    }
)

print(result["response"])