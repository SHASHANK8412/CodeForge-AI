from pathlib import Path

from langchain_chroma import Chroma

from backend.rag.utils.embeddings import EmbeddingGenerator


class VectorStore:

    def __init__(self):

        self.persist_directory = (
            Path(__file__).resolve().parent.parent / "chroma_db"
        )

        self.embedding_model = EmbeddingGenerator().embedding_model

        self.db = Chroma(
            persist_directory=str(self.persist_directory),
            embedding_function=self.embedding_model,
            collection_name="aiforge_docs"
        )

    def add_documents(self, chunks):

        if not chunks:
            return

        ids = []
        for index, chunk in enumerate(chunks):
            source = str(chunk.metadata.get("source", "document"))
            page = str(chunk.metadata.get("page", index))
            ids.append(f"{source}:{page}:{index}")

        self.db.add_documents(chunks, ids=ids)

        print("=" * 60)
        print(f"Stored {len(chunks)} chunks in ChromaDB")
        print("=" * 60)

    def similarity_search(self, query, k=3):

        return self.db.similarity_search(query, k=k)