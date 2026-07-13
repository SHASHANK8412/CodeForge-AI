from langchain_ollama import OllamaEmbeddings


class EmbeddingGenerator:
    """
    Generates embeddings using Ollama's nomic-embed-text model.
    """

    def __init__(self):
        self.embedding_model = OllamaEmbeddings(
            model="nomic-embed-text"
        )

    def embed_documents(self, chunks):
        texts = [chunk.page_content for chunk in chunks]

        embeddings = self.embedding_model.embed_documents(texts)

        print("=" * 60)
        print(f"Generated embeddings for {len(embeddings)} chunks")
        print("=" * 60)

        return embeddings

    def embed_query(self, query: str):
        return self.embedding_model.embed_query(query)