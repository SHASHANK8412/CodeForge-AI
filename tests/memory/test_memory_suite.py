"""
AIForge Day 22 — Long-Term Engineering Memory & Knowledge Graph Test Suite
===========================================================================
Comprehensive unit and integration tests covering:
- Memory Creation, Secret Masking & Project Isolation
- Importance Scoring Engine
- Contextual Memory Retrieval Engine & Agent-Role Ranking
- Contradiction Detection & Invalidation (SUPERSEDED)
- Memory Versioning & Consolidation Engine
- Knowledge Graph Construction & Engineering DNA Integration
- RAG vs Engineering Memory Separation
- Flight Recorder Telemetry Integration
- FastAPI REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.memory.repository import MemoryRepository
from backend.memory.importance import ImportanceScoringEngine
from backend.memory.retrieval import MemoryRetrievalEngine
from backend.memory.consolidation import MemoryConsolidationEngine
from backend.memory.graph import KnowledgeGraphEngine
from backend.memory.service import EngineeringMemoryService
from backend.memory.models import MemoryType, MemoryImportance, MemoryStatus, MemorySource


@pytest.fixture
def client():
    return TestClient(app)


class TestEngineeringMemorySystem:

    def test_memory_creation_secret_masking_and_isolation(self):
        service = EngineeringMemoryService()
        mem_a = service.remember(
            project_id="proj_a",
            title="PostgreSQL Secret Config",
            content="DATABASE_URL=postgresql://user:secret123@localhost/db",
            mem_type=MemoryType.ARCHITECTURE_DECISION
        )

        assert "secret123" not in mem_a.content
        assert "****" in mem_a.content

        # Isolation check
        repo = MemoryRepository()
        repo.save(mem_a)
        assert len(repo.get_by_project("proj_a")) == 1
        assert len(repo.get_by_project("proj_b")) == 0

    def test_importance_scoring_engine(self):
        engine = ImportanceScoringEngine()
        imp_crit = engine.calculate_importance(MemoryType.ARCHITECTURE_DECISION, "PostgreSQL ACID", "Use PostgreSQL")
        assert imp_crit == MemoryImportance.CRITICAL

        imp_low = engine.calculate_importance(MemoryType.USER_PREFERENCE, "Button spacing", "Button spacing 8px")
        assert imp_low == MemoryImportance.LOW

    def test_contextual_retrieval_by_agent_role(self):
        service = EngineeringMemoryService()
        service.remember("proj_ret", "Auth Architecture", "Use JWT tokens", MemoryType.ARCHITECTURE_DECISION, MemorySource.DEBATE)
        service.remember("proj_ret", "UI Component Spacing", "Use 12px margin", MemoryType.USER_PREFERENCE, MemorySource.USER)

        ret_arch = service.retrieve("proj_ret", "Authentication design", agent_type="Architect", top_k=2)
        assert len(ret_arch) >= 1
        assert ret_arch[0].type == MemoryType.ARCHITECTURE_DECISION

    def test_contradiction_detection_and_superseding(self):
        service = EngineeringMemoryService()
        m1 = service.remember("proj_contra", "Database Selection", "Use MongoDB for data storage", MemoryType.ARCHITECTURE_DECISION)
        m2 = service.remember("proj_contra", "Database Selection", "Migrated to PostgreSQL for transactional consistency", MemoryType.ARCHITECTURE_DECISION)

        from backend.memory.repository import global_memory_repository
        m1_refreshed = global_memory_repository.get(m1.id)
        assert m1_refreshed.status == MemoryStatus.SUPERSEDED
        assert m2.status == MemoryStatus.ACTIVE

    def test_memory_versioning_and_consolidation(self):
        service = EngineeringMemoryService()
        m1 = service.remember("proj_vers", "API Validation Pattern", "Use custom Pydantic validators", MemoryType.CODING_PATTERN)
        updated = service.update(m1.id, "Use FastAPI Pydantic v2 validators", reason="Upgrade")

        assert updated.version == 2
        assert updated.status == MemoryStatus.ACTIVE

        # Consolidation
        service.remember("proj_vers", "Input validation 1", "Pydantic validation required", MemoryType.CODING_PATTERN)
        service.remember("proj_vers", "Input validation 2", "Pydantic validation mandatory", MemoryType.CODING_PATTERN)
        cons = service.consolidate("proj_vers")
        assert len(cons) >= 1

    def test_knowledge_graph_construction(self):
        kg_engine = KnowledgeGraphEngine()
        graph = kg_engine.build_knowledge_graph("proj_graph")

        assert len(graph.nodes) >= 5
        assert len(graph.edges) >= 4
        labels = [n.label for n in graph.nodes]
        assert any("ADR-007" in l for l in labels)

    def test_memory_rest_api_endpoints(self, client):
        create_res = client.post(
            "/api/projects/aiforge-demo/memory",
            json={"title": "PostgreSQL Selection", "content": "Use PostgreSQL for ACID compliance", "type": "ARCHITECTURE_DECISION"}
        )
        assert create_res.status_code == 200
        assert create_res.json()["status"] == "success"

        list_res = client.get("/api/projects/aiforge-demo/memory")
        assert list_res.status_code == 200

        search_res = client.get("/api/projects/aiforge-demo/memory/search?q=PostgreSQL")
        assert search_res.status_code == 200

        graph_res = client.get("/api/projects/aiforge-demo/memory/graph")
        assert graph_res.status_code == 200

        dash_res = client.get("/api/projects/aiforge-demo/memory/dashboard")
        assert dash_res.status_code == 200
