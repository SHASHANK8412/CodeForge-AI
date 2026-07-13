from rag.utils.retriever import Retriever


retriever = Retriever()

query = "Tell me about AIForge."

results = retriever.retrieve(query)

print("\nRetrieved Documents\n")

for index, document in enumerate(results, start=1):

    print("=" * 60)
    print(f"Result {index}")
    print(document.page_content)
    print(document.metadata)