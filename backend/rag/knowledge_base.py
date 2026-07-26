import time
import logging
from pathlib import Path
from typing import Dict, Any, List

from backend.rag.loader import DocumentLoader
from backend.rag.splitter import TextSplitter
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import SemanticRetriever

logger = logging.getLogger("aiforge.rag.knowledge_base")


class KnowledgeBase:
    """
    KnowledgeBase orchestrates document loading, text splitting, embedding generation,
    vector store indexing, and semantic retrieval for the AIForge platform.
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or str(Path(__file__).resolve().parent.parent / "data" / "docs")
        self.loader = DocumentLoader()
        self.splitter = TextSplitter(chunk_size=1000, overlap=200)
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.retriever = SemanticRetriever(
            vector_store=self.vector_store,
            embedding_generator=self.embedding_generator
        )

        self.last_updated: float = 0.0
        self.is_indexed: bool = False

        # Auto-index data directory if exists
        self.index_directory(self.data_dir)

    def index_directory(self, dir_path: str) -> Dict[str, Any]:
        """Indexes all documents in the target directory into the vector store."""
        docs = self.loader.load_directory(dir_path)
        if not docs:
            logger.info(f"No documents found to index in '{dir_path}'")
            return self.get_stats()

        chunks = self.splitter.split_documents(docs)
        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_generator.generate_batch(texts)

        self.vector_store.clear()
        self.vector_store.add_documents(chunks, embeddings)

        self.last_updated = time.time()
        self.is_indexed = True
        logger.info(f"KnowledgeBase successfully indexed {len(docs)} docs ({len(chunks)} chunks)")

        return self.get_stats()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Performs semantic retrieval against indexed knowledge base."""
        return self.retriever.retrieve(query, top_k=top_k)

    def get_context_for_prompt(self, query: str, top_k: int = 5) -> str:
        """Returns formatted RAG context block for prompt injection."""
        return self.retriever.retrieve_context_string(query, top_k=top_k)

    def get_stats(self) -> Dict[str, Any]:
        """Returns knowledge base telemetry and indexing statistics."""
        stats = self.vector_store.get_stats()
        stats.update({
            "is_indexed": self.is_indexed,
            "last_updated": self.last_updated,
            "data_dir": self.data_dir
        })
        return stats


# Global KnowledgeBase Instance
global_knowledge_base = KnowledgeBase()
