from backend.graph.workflow import graph


if __name__ == "__main__":

    prompt = input("Enter Prompt: ")

    result = graph.invoke(
        {
            "prompt": prompt
        }
    )

    print("\n")
    print("=" * 50)
    print("PLAN")
    print("=" * 50)
    print(result["plan"])

    print("\n")
    print("=" * 50)
    
    print("RESPONSE")
    print("=" * 50)
    print(result["response"])