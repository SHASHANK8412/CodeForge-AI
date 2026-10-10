"""
RAG routes: upload and query, scoped per project.

The original tests patched module attributes (rag_pipeline, document_loader, ...) that the routes
no longer have. These run the real upload -> chunk -> embed -> retrieve path (local hash
embeddings, no model server) and check the regressions fixed alongside:
  * /api/query ignored project_id, so a project's uploaded documents were never searched;
  * the RAG router's /api/upload shadowed the upload box's /api/upload (different form field);
  * project ids went straight into a filesystem path.
"""
import shutil
import uuid
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.rag.vector_store import global_vector_store
from backend.routes import rag as rag_routes

client = TestClient(app)

DOC = (
    "# Billing service\n\n"
    "Invoices are generated nightly by the ledger worker. Each invoice references the "
    "customer account and is retried three times when the payment gateway times out.\n"
)


@pytest.fixture
def project_id():
    pid = f"ragtest_{uuid.uuid4().hex[:8]}"
    yield pid
    global_vector_store.delete_project(pid)
    shutil.rmtree(rag_routes._DATA_ROOT / pid, ignore_errors=True)


def _upload(pid, name="billing.md", content=DOC):
    return client.post(f"/api/projects/{pid}/rag/upload", files={"files": (name, BytesIO(content.encode()), "text/markdown")})


def test_rag_upload_indexes_documents(project_id):
    res = _upload(project_id)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True and body["project_id"] == project_id
    assert body["chunks_indexed"] >= 1
    assert body["files"][0].endswith("_billing.md")
    assert (rag_routes._DATA_ROOT / project_id / "documents" / body["files"][0]).read_text(encoding="utf-8") == DOC
    assert global_vector_store.get_stats(project_id=project_id)


def test_rag_query_returns_answer_and_sources(project_id):
    assert _upload(project_id).status_code == 200
    res = client.post("/api/query", json={"question": "How are invoices retried when the payment gateway times out?",
                                          "project_id": project_id})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["citations"], body
    assert "retried three times" in body["answer"]

    # The legacy route returns the same answer.
    legacy = client.post("/rag/query", json={"question": "How are invoices retried when the payment gateway times out?",
                                             "project_id": project_id})
    assert legacy.status_code == 200 and legacy.json()["answer"] == body["answer"]


def test_rag_query_does_not_leak_between_projects(project_id):
    assert _upload(project_id).status_code == 200
    other = f"{project_id}_other"
    try:
        res = client.post("/api/query", json={"question": "How are invoices retried when the payment gateway times out?",
                                              "project_id": other})
        assert res.status_code == 200
        assert "retried three times" not in res.json()["answer"]
    finally:
        global_vector_store.delete_project(other)


@pytest.mark.parametrize("bad", ["..", "a..b", ".hidden", "x" * 200])
def test_rag_rejects_unsafe_project_ids(bad):
    res = client.post("/api/query", json={"question": "anything about invoices?", "project_id": bad})
    assert res.status_code == 400


def test_upload_box_route_is_not_shadowed():
    # UploadBox.jsx posts a single `file` field; the RAG router used to answer this path
    # first and reject it (it expects `files`).
    from backend.routes.upload import upload_file
    owners = [ctx.endpoint for r in app.router.routes if type(r).__name__ == "_IncludedRouter"
              for ctx in r.effective_route_contexts() if ctx.path == "/api/upload" and "POST" in (ctx.methods or ())]
    assert owners == [upload_file]
