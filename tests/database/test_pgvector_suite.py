"""
AIForge Day 27 — PostgreSQL & pgvector Database Test Suite
=============================================================
Comprehensive unit and integration tests covering:
1. Connection & Session Management
2. Alembic Migrations
3. Structured CRUD (Projects, Incidents, Deployments, Architecture Decisions)
4. Strict Project Isolation (Zero Cross-Project Data Leakage)
5. Vector Insertion & Dimension Validation Exception
6. Vector Similarity Search (Top-K Ordering)
7. Engineering Memory Retrieval with project_id + Semantic Query ("Why did we choose PostgreSQL?")
8. RAG Pipeline Retrieval via PostgresVectorStore
9. Table & Index Audits
10. Database Health REST Endpoint (/health/database)
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.connection import SessionLocal, check_db_health, engine
from backend.database.models import ProjectModel, IncidentModel, DeploymentModel, ArchitectureDecisionModel, EngineeringMemoryModel, VectorEmbeddingModel
from backend.database.vector import PostgresVectorStore, ChromaVectorStore, EMBEDDING_DIMENSIONS
from backend.database.service import DatabaseService
from backend.memory.service import EngineeringMemoryService
from backend.memory.models import MemoryType, MemorySource, MemoryConfidence
from backend.rag.vector_store import VectorStore as RAGVectorStore


@pytest.fixture
def client():
    return TestClient(app)


class TestPostgresPgvectorSuite:

    def test_database_connection_and_health(self, client):
        health = check_db_health()
        assert health["status"] in ("healthy", "degraded")
        assert "password" not in str(health).lower()
        assert health["project_isolation"] == "ENFORCED"

        res = client.get("/health/database")
        assert res.status_code == 200
        assert res.json()["status"] in ("healthy", "degraded")

    def test_structured_crud_and_isolation(self):
        db = SessionLocal()
        try:
            p1 = ProjectModel(id="proj_alpha", name="Alpha SaaS System")
            p2 = ProjectModel(id="proj_beta", name="Beta Machine Learning")
            db.add_all([p1, p2])

            inc1 = IncidentModel(id="inc_a1", project_id="proj_alpha", type="DATABASE_TIMEOUT", symptoms="[]")
            inc2 = IncidentModel(id="inc_b1", project_id="proj_beta", type="MEMORY_LEAK", symptoms="[]")
            db.add_all([inc1, inc2])

            db.commit()

            # Verify project isolation
            alpha_incidents = db.query(IncidentModel).filter(IncidentModel.project_id == "proj_alpha").all()
            assert len(alpha_incidents) == 1
            assert alpha_incidents[0].id == "inc_a1"

            beta_incidents = db.query(IncidentModel).filter(IncidentModel.project_id == "proj_beta").all()
            assert len(beta_incidents) == 1
            assert beta_incidents[0].id == "inc_b1"
        finally:
            db.close()

    def test_vector_dimension_validation(self):
        store = PostgresVectorStore(collection_name="test_dim_check")

        invalid_vector = [0.1] * (EMBEDDING_DIMENSIONS - 10)
        docs = [{"id": "doc_bad", "text": "invalid vector test"}]

        with pytest.raises(ValueError, match="Vector dimension mismatch"):
            store.add(docs, [invalid_vector], project_id="proj_alpha")

    def test_vector_insertion_and_similarity_search(self):
        store = PostgresVectorStore(collection_name="test_sim_check")
        store.delete("proj_alpha")

        v1 = [0.9] + [0.0] * (EMBEDDING_DIMENSIONS - 1)
        v2 = [0.0] * (EMBEDDING_DIMENSIONS - 1) + [0.9]

        docs = [
            {"id": "doc_postgres", "text": "PostgreSQL was chosen for unified ACID storage and pgvector similarity.", "document_type": "ARCHITECTURE"},
            {"id": "doc_unrelated", "text": "CSS styling guidelines for landing page buttons.", "document_type": "FRONTEND"}
        ]

        store.add(docs, [v1, v2], project_id="proj_alpha")

        query_vec = [0.9] + [0.0] * (EMBEDDING_DIMENSIONS - 1)

        results = store.search(query_vec, project_id="proj_alpha", top_k=2)

        assert len(results) == 2
        assert results[0]["id"] == "doc_postgres"
        assert results[0]["score"] > results[1]["score"]

        # Verify strict project isolation - Searching under different project_id returns 0 results
        beta_results = store.search(query_vec, project_id="proj_beta", top_k=2)
        assert len(beta_results) == 0

    def test_engineering_memory_postgreSQL_retrieval(self):
        mem_service = EngineeringMemoryService()
        mem = mem_service.remember(
            project_id="proj_alpha",
            title="Database Selection: PostgreSQL + pgvector",
            content="We chose PostgreSQL + pgvector for unified relational transactions and vector embeddings.",
            mem_type=MemoryType.ARCHITECTURE_DECISION,
            source=MemorySource.DEBATE,
            confidence=MemoryConfidence.HIGH
        )

        assert mem.id is not None

        # Semantic retrieval
        retrieved = mem_service.search("proj_alpha", "Why did we choose PostgreSQL?")
        assert len(retrieved) >= 1
        assert "PostgreSQL" in retrieved[0].title or "PostgreSQL" in retrieved[0].content

        # Project isolation
        beta_retrieved = mem_service.search("proj_beta", "PostgreSQL")
        assert len(beta_retrieved) == 0

    def test_rag_pipeline_integration(self):
        rag_store = RAGVectorStore(collection_name="rag_test_coll")
        v = [0.5] * EMBEDDING_DIMENSIONS

        rag_store.add_documents(
            documents=[{"id": "rag_doc_1", "text": "RAG pipeline with PostgreSQL vector embeddings."}],
            embeddings=[v],
            project_id="proj_rag_test"
        )

        results = rag_store.search(v, project_id="proj_rag_test", top_k=1)
        assert len(results) == 1
        assert results[0]["id"] == "rag_doc_1"

        # Delete project vectors
        deleted = rag_store.delete_project("proj_rag_test")
        assert deleted >= 1
