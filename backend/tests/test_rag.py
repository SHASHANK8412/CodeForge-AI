import pytest
from backend.rag.loader import DocumentLoader
from backend.rag.splitter import TextSplitter
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import SemanticRetriever
from backend.rag.pipeline import RAGPipeline


def test_document_loading(tmp_path):
    """Test 1: Document loading from markdown, txt, and files."""
    doc_file = tmp_path / "test_doc.md"
    doc_file.write_text("# Test Title\nThis is a sample test document for RAG testing.", encoding="utf-8")

    loader = DocumentLoader()
    text = loader.load_file(str(doc_file))
    assert "# Test Title" in text

    docs = loader.load_directory(str(tmp_path))
    assert len(docs) == 1
    assert "test_doc.md" in docs


def test_text_splitting():
    """Test 2: Document text splitting into chunks with overlap."""
    splitter = TextSplitter(chunk_size=50, overlap=10)
    sample_text = "Python is an interpreted high-level general-purpose programming language. Fast execution and readable syntax."

    chunks = splitter.split_text(sample_text)
    assert len(chunks) >= 2
    assert "Python" in chunks[0]


def test_embedding_generation():
    """Test 3: Vector embedding generation."""
    generator = EmbeddingGenerator()
    vec = generator.generate_embedding("JWT authentication with FastAPI and React")

    assert len(vec) == 384
    assert isinstance(vec[0], float)


def test_vector_storage():
    """Test 4: VectorStore document chunk indexing and search."""
    store = VectorStore(collection_name="test_collection")
    docs = [
        {"id": "doc1", "text": "FastAPI enables high performance async python web APIs.", "source": "fastapi.md"},
        {"id": "doc2", "text": "React 18 provides component state and JSX UI rendering.", "source": "react.md"}
    ]
    generator = EmbeddingGenerator()
    embeddings = generator.generate_batch([d["text"] for d in docs])

    added = store.add_documents(docs, embeddings)
    assert added == 2

    query_vec = generator.generate_embedding("FastAPI async python")
    results = store.search(query_vec, top_k=2)

    assert len(results) == 2
    assert results[0]["id"] == "doc1"
    assert results[0]["score"] > 0.0


def test_semantic_retrieval():
    """Test 5: SemanticRetriever query resolution."""
    store = VectorStore(collection_name="retriever_test")
    generator = EmbeddingGenerator()

    docs = [{"id": "jwt1", "text": "Always store JWT secret key in environment variables.", "source": "jwt.md"}]
    store.add_documents(docs, generator.generate_batch(["Always store JWT secret key in environment variables."]))

    retriever = SemanticRetriever(vector_store=store, embedding_generator=generator)
    results = retriever.retrieve("Where to store JWT secret?", top_k=1)

    assert len(results) == 1
    assert "JWT" in results[0]["text"]

    context_str = retriever.retrieve_context_string("JWT secret", top_k=1)
    assert "Retrieved Knowledge" in context_str
    assert "jwt.md" in context_str


def test_rag_pipeline_context_injection():
    """Test 6: RAGPipeline prompt augmentation and context injection."""
    pipeline = RAGPipeline()
    augmented_prompt = pipeline.build_augmented_prompt(
        user_prompt="Build authentication system",
        agent_name="planner",
        memory_context="Previous project used React"
    )

    assert "Retrieved Technical Knowledge" in augmented_prompt or "Task Instructions" in augmented_prompt
    assert "planner" in augmented_prompt.lower()
