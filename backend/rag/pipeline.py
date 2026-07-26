import logging
from pathlib import Path
from typing import Dict, Any, List

from backend.rag.loader import DocumentLoader
from backend.rag.splitter import TextSplitter
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.vectordb import ChromaVectorDB, global_vectordb
from backend.rag.retriever import SemanticRetriever

logger = logging.getLogger("aiforge.rag.pipeline")


class RAGPipeline:
    """
    Complete RAG Pipeline for Day 14:
    Document -> Loader -> Splitter -> Embeddings -> VectorDB (ChromaDB) -> Retriever -> Agents
    """

    def __init__(self, vectordb: ChromaVectorDB = None):
        self.loader = DocumentLoader()
        self.splitter = TextSplitter(chunk_size=1000, overlap=200)
        self.embeddings = EmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        self.vectordb = vectordb or global_vectordb
        self.retriever = SemanticRetriever(
            vector_store=self.vectordb,
            embedding_generator=self.embeddings
        )

    def process_and_index_document(self, filepath: str) -> Dict[str, Any]:
        """Loads a PDF, TXT, or Markdown document, splits into chunks, and stores in ChromaDB."""
        text = self.loader.load_file(filepath)
        filename = Path(filepath).name
        raw_chunks = self.splitter.split_text(text)

        ids = [f"{filename}_chunk_{idx}" for idx in range(len(raw_chunks))]
        metadatas = [{"source": filename, "chunk_index": idx} for idx in range(len(raw_chunks))]
        emb_vectors = self.embeddings.generate_batch(raw_chunks)

        count = self.vectordb.add_texts(ids, raw_chunks, emb_vectors, metadatas)
        logger.info(f"Indexed document '{filename}' into ChromaDB with {count} chunks")
        return {
            "filename": filename,
            "chunks_count": count,
            "status": "success"
        }

    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top_k relevant context chunks for a query from ChromaDB."""
        query_vector = self.embeddings.generate_embedding(query)
        return self.vectordb.search(query_vector, top_k=top_k)

    def get_context_string_for_agent(self, agent_name: str, prompt: str, top_k: int = 3) -> str:
        """Constructs formatted RAG documentation context to inject into an agent's LLM prompt."""
        query = f"{prompt} {agent_name} requirements specifications"
        results = self.retrieve_context(query, top_k=top_k)
        if not results:
            return ""

        lines = [f"### Uploaded PRD & Project Documentation Context ({agent_name.upper()})"]
        for idx, res in enumerate(results, 1):
            source = res.get("source", "uploaded_doc")
            text = res.get("text", "").strip()
            score = res.get("score", 0.0)
            lines.append(f"**[{idx}] Source: {source} (Relevance: {score})**\n{text}\n")

        return "\n".join(lines)

    def augment_agent_prompt(self, agent_name: str, user_prompt: str, base_prompt: str = "") -> str:
        """Augments an agent prompt with retrieved PRD documentation."""
        rag_context = self.get_context_string_for_agent(agent_name, user_prompt)
        if not rag_context:
            return base_prompt or user_prompt

        return f"{rag_context}\n\n### Agent Request\n{base_prompt or user_prompt}"

    def get_stats(self) -> Dict[str, Any]:
        """Returns stats from persistent vector database."""
        return self.vectordb.get_stats()


# Global RAGPipeline Instance
global_rag_pipeline = RAGPipeline()
