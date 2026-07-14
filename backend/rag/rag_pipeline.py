from backend.rag.utils.retriever import Retriever
from backend.services.llm import generate_response


class RAGPipeline:

    def __init__(self):
        self.retriever = Retriever()

    def build_prompt(self, question, documents):

        context = "\n\n".join(doc.page_content for doc in documents)

        return f"""
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

    def format_sources(self, documents):

        sources = []
        for doc in documents:
            metadata = doc.metadata or {}
            sources.append(
                {
                    "source": metadata.get("source", "unknown"),
                    "page": metadata.get("page", metadata.get("page_number", "")),
                    "snippet": doc.page_content[:240],
                }
            )
        return sources

    def query(self, question):

        documents = self.retriever.retrieve(
            query=question,
            k=5,
        )

        if not documents:
            return {
                "answer": "I couldn't find that information.",
                "sources": [],
            }

        prompt = self.build_prompt(question, documents)
        response = generate_response(prompt, task="explanation")

        return {
            "answer": response,
            "sources": self.format_sources(documents),
        }

    def ask(self, question):

        return self.query(question)["answer"]