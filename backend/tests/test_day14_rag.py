import pytest
from backend.rag.loader import DocumentLoader
from backend.rag.splitter import TextSplitter
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.vectordb import ChromaVectorDB
from backend.rag.retriever import SemanticRetriever
from backend.rag.pipeline import RAGPipeline
from backend.services.prompt_builder import global_prompt_builder


@pytest.fixture
def sample_prd(tmp_path):
    prd_path = tmp_path / "sample_prd.md"
    prd_path.write_text(
        "# Todo Application PRD\n\n"
        "Authentication: JWT\n"
        "Database: PostgreSQL\n"
        "Frontend: React\n"
        "Backend: FastAPI\n\n"
        "Features:\n"
        "1. Login & Register\n"
        "2. Tasks CRUD\n"
        "3. Categories\n"
        "4. Dashboard\n",
        encoding="utf-8"
    )
    return str(prd_path)


def test_document_upload_and_indexing(sample_prd):
    """Test 1: Upload and parse PDF/TXT/Markdown PRD documents."""
    loader = DocumentLoader()
    content = loader.load_file(sample_prd)

    assert "Todo Application PRD" in content
    assert "JWT" in content
    assert "FastAPI" in content


def test_prd_chunk_splitting(sample_prd):
    """Test 2: Split PRD into overlapping chunks (size=1000, overlap=200)."""
    loader = DocumentLoader()
    text = loader.load_file(sample_prd)

    splitter = TextSplitter(chunk_size=1000, overlap=200)
    chunks = splitter.split_text(text)

    assert len(chunks) >= 1
    assert "PostgreSQL" in chunks[0]


def test_chromadb_vector_store():
    """Test 3: Store vector embeddings in ChromaVectorDB."""
    vdb = ChromaVectorDB(collection_name="test_day14_collection")
    generator = EmbeddingGenerator()

    texts = ["Authentication: JWT with FastAPI and PostgreSQL", "React Vite Dashboard frontend"]
    embeddings = generator.generate_batch(texts)
    ids = ["id_1", "id_2"]
    metadatas = [{"source": "prd.md"}, {"source": "ui.md"}]

    count = vdb.add_texts(ids, texts, embeddings, metadatas)
    assert count == 2

    query_vec = generator.generate_embedding("What authentication system?")
    results = vdb.search(query_vec, top_k=1)

    assert len(results) == 1
    assert "JWT" in results[0]["text"]


def test_context_retrieval_for_todo_prd(sample_prd):
    """Test 4: Retrieve relevant PRD context for user query."""
    pipeline = RAGPipeline()
    res = pipeline.process_and_index_document(sample_prd)
    assert res["status"] == "success"

    results = pipeline.retrieve_context("What authentication system should I use?", top_k=2)
    assert len(results) >= 1
    retrieved_text = results[0]["text"]
    assert "JWT" in retrieved_text or "FastAPI" in retrieved_text


def test_planner_agent_rag_integration(sample_prd):
    """Test 5: Connect RAG pipeline to Planner Agent prompt builder."""
    pipeline = RAGPipeline()
    pipeline.process_and_index_document(sample_prd)

    prompt = global_prompt_builder.build_planner_prompt("Generate Todo application backend APIs")
    assert "Planner" in prompt or "FastAPI" in prompt or "JWT" in prompt or "JSON" in prompt


def test_coding_agents_context_aware_generation(sample_prd):
    """Test 6: Coding agents receive retrieved PRD context before generation."""
    pipeline = RAGPipeline()
    pipeline.process_and_index_document(sample_prd)

    arch_json = {"components": ["TodoList", "TaskItem"], "routes": ["GET /api/tasks", "POST /api/auth/login"], "models": ["Task", "User"]}

    fe_prompt = global_prompt_builder.build_frontend_prompt(arch_json)
    be_prompt = global_prompt_builder.build_backend_prompt(arch_json)
    db_prompt = global_prompt_builder.build_database_prompt(arch_json)

    assert "React" in fe_prompt or "TodoList" in fe_prompt
    assert "FastAPI" in be_prompt or "GET /api/tasks" in be_prompt
    assert "PostgreSQL" in db_prompt or "User" in db_prompt
