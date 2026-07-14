from io import BytesIO

from fastapi.testclient import TestClient

from backend.main import app
from backend.routes import rag as rag_routes


client = TestClient(app)


def test_rag_query_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(
        rag_routes.rag_pipeline,
        "query",
        lambda question: {
            "answer": "RAG answer",
            "sources": [{"source": "sample.txt", "page": 1, "snippet": "alpha"}],
        },
    )

    response = client.post("/rag/query", json={"question": "What is in the document?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "RAG answer"
    assert payload["sources"] == ["sample.txt"]
    assert payload["source_details"][0]["source"] == "sample.txt"


def test_rag_upload_indexes_documents(monkeypatch):
    loaded_paths = []
    split_documents = []
    indexed_chunks = []

    monkeypatch.setattr(rag_routes.document_loader, "load_paths", lambda paths: loaded_paths.extend(paths) or ["doc1"])
    monkeypatch.setattr(rag_routes.document_splitter, "split_documents", lambda documents: split_documents.extend(documents) or ["chunk1", "chunk2"])
    monkeypatch.setattr(rag_routes.vector_store, "add_documents", lambda chunks: indexed_chunks.extend(chunks))

    response = client.post(
        "/rag/upload",
        files={"files": ("sample.txt", BytesIO(b"hello document"), "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["chunks_indexed"] == 2
    assert loaded_paths
    assert split_documents == ["doc1"]
    assert indexed_chunks == ["chunk1", "chunk2"]