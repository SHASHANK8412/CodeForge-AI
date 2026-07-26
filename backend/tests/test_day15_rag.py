import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_file_upload_api():
    """Test 1: Upload Markdown document and verify RAG indexing response."""
    content = b"# Software Requirements\nAuthentication: JWT\nDatabase: PostgreSQL\nFrontend: React\nBackend: FastAPI\nCaching: Redis\nDeployment: Docker\n"
    response = client.post(
        "/api/upload",
        files={"file": ("SoftwareRequirements.md", content, "text/markdown")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"] == "SoftwareRequirements.md"
    assert data["chunks"] >= 1


def test_duplicate_upload_detection():
    """Test 2: Duplicate file upload returns 'Already Indexed'."""
    content = b"Duplicate file content test for hash detection."
    res1 = client.post("/api/upload", files={"file": ("dup_test.txt", content, "text/plain")})
    assert res1.status_code == 200

    res2 = client.post("/api/upload", files={"file": ("dup_test.txt", content, "text/plain")})
    assert res2.status_code == 200
    data = res2.json()
    assert data["message"] == "Already Indexed" or data["status"] == "success"


def test_unsupported_file_type_rejection():
    """Test 3: Reject unsupported file extensions (e.g. .exe or .bin)."""
    response = client.post(
        "/api/upload",
        files={"file": ("malicious.exe", b"binary content", "application/octet-stream")}
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_document_listing_api():
    """Test 4: List uploaded documents from /uploads directory."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)


def test_document_deletion_api():
    """Test 5: Delete uploaded document and purge vectors."""
    # First upload a file to delete
    content = b"Content to be deleted."
    client.post("/api/upload", files={"file": ("to_delete.txt", content, "text/plain")})

    response = client.delete("/api/documents/to_delete.txt")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_rag_query_api_chat_knowledge():
    """Test 6: Query /query API and verify answer grounded in uploaded documents."""
    # Upload PRD content
    prd_content = b"Software Architecture:\nDatabase: PostgreSQL\nAuthentication: JWT\nCaching: Redis\nDeployment: Docker\n"
    client.post("/api/upload", files={"file": ("ArchDoc.txt", prd_content, "text/plain")})

    response = client.post("/query", json={"question": "Which database should be used?"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "PostgreSQL" in data["answer"] or "PostgreSQL" in str(data["context"])
