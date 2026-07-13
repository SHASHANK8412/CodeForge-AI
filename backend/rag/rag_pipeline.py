from rag.utils.retriever import Retriever
from backend.services.llm import generate_response


class RAGPipeline:

    def __init__(self):
        self.retriever = Retriever()

    def ask(self, question):

        # Retrieve more chunks for better context
        documents = self.retriever.retrieve(
            query=question,
            k=5
        )

        print("\n" + "=" * 70)
        print("Retrieved Documents")
        print("=" * 70)

        if not documents:
            print("No documents found!")
            return "I couldn't find that information."

        for i, doc in enumerate(documents, start=1):
            print(f"\nDocument {i}")
            print("-" * 70)
            print(doc.page_content)
            print("\nMetadata:")
            print(doc.metadata)

        # Build context
        context = "\n\n".join(
            doc.page_content
            for doc in documents
        )

        print("\n" + "=" * 70)
        print("Context Sent To LLM")
        print("=" * 70)
        print(context)

        prompt = f"""
You are AIForge's knowledge assistant.

Use ONLY the information present in the context.

If the answer exists in the context, answer it clearly.

Do NOT say "I couldn't find that information" unless the answer is genuinely absent.

-------------------- CONTEXT --------------------

{context}

-------------------------------------------------

Question:
{question}

Answer:
"""

        print("\n" + "=" * 70)
        print("Prompt Sent To LLM")
        print("=" * 70)
        print(prompt)

        response = generate_response(prompt)

        print("\n" + "=" * 70)
        print("LLM Response")
        print("=" * 70)
        print(response)

        return response