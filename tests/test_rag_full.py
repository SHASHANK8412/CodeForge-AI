"""
tests/test_rag_full.py
=======================
Comprehensive tests for Day 13 Advanced RAG & Knowledge-Aware Agent System.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.rag.loader import global_document_loader
from backend.rag.splitter import global_text_splitter
from backend.rag.embedding_service import global_embedding_service
from backend.rag.vector_store import VectorStore, global_vector_store
from backend.rag.query_analyzer import global_query_analyzer
from backend.rag.ingestion import redact_secrets, DocumentIngestionPipeline
from backend.rag.hybrid_retriever import global_hybrid_retriever
from backend.rag.pipeline import global_rag_pipeline
from backend.rag.code_indexer import index_generated_code
from backend.services.context_builder import build_agent_context


@pytest.fixture()
def tmp_vector_store():
    return VectorStore(collection_name="test_rag_collection")


@pytest.fixture()
def app_client():
    from backend.main import app
    return TestClient(app, raise_server_exceptions=True)


class TestDay13RAG:

    def test_loader_file_support(self, tmp_path):
        # Create test markdown file
        md_file = tmp_path / "test_doc.md"
        md_file.write_text("# Heading\nSample documentation text", encoding="utf-8")
        text = global_document_loader.load_file(str(md_file))
        assert "Sample documentation text" in text

        # Create test json file
        json_file = tmp_path / "config.json"
        json_file.write_text('{"api_name": "AIForge"}', encoding="utf-8")
        json_text = global_document_loader.load_file(str(json_file))
        assert "AIForge" in json_text

        # Binary file rejection
        bin_file = tmp_path / "app.exe"
        bin_file.write_bytes(b"\x00\x01\x02")
        with pytest.raises(ValueError, match="unsupported"):
            global_document_loader.load_file(str(bin_file))

    def test_structure_aware_chunking(self):
        md_text = "# Section 1\nIntro text\n## Subsection 1.1\nDetailed content"
        chunks = global_text_splitter.split_markdown(md_text, "doc.md")
        assert len(chunks) >= 2
        assert chunks[0]["heading"] == "Section 1"

        code_text = "def handle_login():\n    return True\n\nclass AuthController:\n    pass"
        code_chunks = global_text_splitter.split_code(code_text, "auth.py")
        assert len(code_chunks) >= 2

    def test_secret_redaction(self):
        raw_text = "AWS_KEY = 'AKIA1234567890ABCDEF' and TOKEN = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'"
        redacted = redact_secrets(raw_text)
        assert "AKIA1234567890ABCDEF" not in redacted
        assert "[REDACTED_AWS_KEY]" in redacted
        assert "[REDACTED_GITHUB_TOKEN]" in redacted

    def test_embedding_service(self):
        emb1 = global_embedding_service.embed_document("FastAPI backend REST API")
        emb2 = global_embedding_service.embed_query("FastAPI REST endpoints")
        assert len(emb1) == 384
        assert len(emb2) == 384

    def test_vector_store_project_isolation(self, tmp_vector_store):
        emb_a = global_embedding_service.embed_document("Project A secret specification")
        emb_b = global_embedding_service.embed_document("Project B internal architecture")

        tmp_vector_store.add_documents([{"id": "docA", "text": "Project A spec"}], [emb_a], project_id="proj_A")
        tmp_vector_store.add_documents([{"id": "docB", "text": "Project B spec"}], [emb_b], project_id="proj_B")

        res_a = tmp_vector_store.search(emb_a, project_id="proj_A")
        res_b = tmp_vector_store.search(emb_a, project_id="proj_B")

        assert len(res_a) == 1
        assert res_a[0]["id"] == "docA"
        assert len(res_b) == 1
        assert res_b[0]["id"] == "docB"

    def test_query_analyzer(self):
        analysis = global_query_analyzer.analyze_query("How to setup JWT auth in FastAPI?", agent_name="backend")
        assert analysis["intent"] == "authentication"
        assert "fastapi" in analysis["technologies"] or "jwt" in analysis["technologies"]
        assert "SECURITY" in analysis["document_types"] or "FRAMEWORK" in analysis["document_types"]

    def test_generated_code_indexing(self, tmp_vector_store):
        files_map = {
            "backend/app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health(): return {'status': 'ok'}",
            "frontend/src/App.jsx": "export default function App() { return <div>AIForge</div>; }"
        }

        indexed = index_generated_code("proj_code", files_map)
        assert indexed >= 2

        stats = global_vector_store.get_stats(project_id="proj_code")
        assert stats["total_chunks"] >= 2

    def test_context_builder_rag_integration(self):
        global_rag_pipeline.process_and_index_document(
            filepath="c:/Users/Shashank/OneDrive/Documents/CODEFORGE AI/backend/memory/architectures.json",
            project_id="proj_rag_builder"
        )

        ctx = build_agent_context(
            project_id="proj_rag_builder",
            agent_name="architect",
            prompt="Which framework should we use?"
        )
        assert "architect" in ctx.lower() or "RAG" in ctx

    def test_rag_debug_api_endpoint(self, app_client):
        res = app_client.post("/api/rag/debug", json={"project_id": "proj_dbg", "agent": "backend", "query": "FastAPI auth"})
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "success"
        assert "analysis" in body
        assert "results" in body

    def test_rag_eval_dataset_metrics(self):
        eval_cases = [
            {"query": "JWT auth setup", "expected_type": "authentication", "doc": "authentication.md"},
            {"query": "PostgreSQL database schema", "expected_type": "database", "doc": "schema.sql"},
            {"query": "React navbar UI component", "expected_type": "frontend_ui", "doc": "Navbar.jsx"}
        ]

        hits = 0
        for case in eval_cases:
            analysis = global_query_analyzer.analyze_query(case["query"])
            if analysis["intent"] == case["expected_type"]:
                hits += 1

        accuracy = hits / len(eval_cases)
        assert accuracy >= 0.90
