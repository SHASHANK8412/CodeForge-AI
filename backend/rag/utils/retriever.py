from backend.rag.utils.vector_store import VectorStore


class Retriever:

    def __init__(self):

        self.vector_store = VectorStore()

    def retrieve(self, query, k=3):

        results = self.vector_store.similarity_search(
            query=query,
            k=k
        )

        return results