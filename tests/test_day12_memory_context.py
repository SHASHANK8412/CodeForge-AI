"""
tests/test_day12_memory_context.py
====================================
Comprehensive tests for Day 12 Persistent Agent Memory & Context Management.
"""

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.memory.models import ProjectMemory, DecisionRecord, MemoryType, ImportanceLevel
from backend.memory.short_term import global_short_term_memory
from backend.memory.long_term import global_long_term_memory, LongTermMemory
from backend.memory.memory_manager import global_memory_manager, MemoryManager
from backend.services.context_builder import build_agent_context, global_agent_context_builder
from backend.memory.retrieval import retrieve_relevant_memory, global_memory_retriever


@pytest.fixture()
def memory_inst(tmp_path):
    """Isolated LongTermMemory instance."""
    store_file = tmp_path / "test_memory.json"
    lt = LongTermMemory(storage_file=store_file)
    mm = MemoryManager()
    mm.long_term = lt
    return mm


@pytest.fixture()
def app_client():
    from backend.main import app
    return TestClient(app, raise_server_exceptions=True)


class TestDay12Memory:

    def test_memory_save(self, memory_inst):
        mem = memory_inst.save(
            project_id="proj_1",
            memory_type=MemoryType.REQUIREMENT,
            key="auth_spec",
            value="OAuth2 with JWT tokens",
            source_agent="planner",
            importance=ImportanceLevel.HIGH
        )
        assert mem.id.startswith("mem_")
        assert mem.project_id == "proj_1"
        assert mem.key == "auth_spec"
        assert mem.value == "OAuth2 with JWT tokens"
        assert mem.importance == ImportanceLevel.HIGH

    def test_memory_retrieve(self, memory_inst):
        memory_inst.save("proj_2", MemoryType.REQUIREMENT, "req1", "Feature A", "planner")
        memory_inst.save_decision("proj_2", "Use FastAPI framework", "High performance async REST routes", "architect")

        res = memory_inst.retrieve(project_id="proj_2", query="FastAPI", agent_name="backend")
        assert res["project_id"] == "proj_2"
        assert len(res["decisions"]) >= 1
        assert "FastAPI" in res["context_string"]

    def test_memory_update(self, memory_inst):
        mem = memory_inst.save("proj_3", MemoryType.TECHNOLOGY, "backend", "Flask", "architect")
        updated = memory_inst.update("proj_3", mem.id, {"value": "FastAPI"})
        assert updated is not None
        assert updated.value == "FastAPI"

    def test_memory_delete(self, memory_inst):
        mem = memory_inst.save("proj_4", MemoryType.FILE, "main.py", "print('hello')", "backend")
        assert memory_inst.delete("proj_4", mem.id) is True
        assert memory_inst.long_term.get_memory("proj_4", mem.id) is None

    def test_memory_search(self, memory_inst):
        memory_inst.save("proj_5", MemoryType.REQUIREMENT, "payment", "Stripe Checkout", "planner")
        memory_inst.save("proj_5", MemoryType.REQUIREMENT, "search", "ElasticSearch cluster", "planner")

        found = memory_inst.search("proj_5", "Stripe payment", top_k=2)
        assert len(found) >= 1
        assert found[0].key == "payment"

    def test_memory_importance(self, memory_inst):
        memory_inst.save("proj_6", MemoryType.FILE, "tmp.log", "debug log", "backend", importance=ImportanceLevel.LOW)
        memory_inst.save("proj_6", MemoryType.DECISION, "db_engine", "PostgreSQL", "architect", importance=ImportanceLevel.CRITICAL)

        mems = memory_inst.long_term.search_memories("proj_6", "db", top_k=5)
        assert len(mems) >= 1
        assert mems[0].importance == ImportanceLevel.CRITICAL

    def test_project_memory_isolation(self, memory_inst):
        memory_inst.save("proj_A", MemoryType.REQUIREMENT, "reqA", "Only for A", "planner")
        memory_inst.save("proj_B", MemoryType.REQUIREMENT, "reqB", "Only for B", "planner")

        mems_a = memory_inst.long_term.get_memories("proj_A")
        mems_b = memory_inst.long_term.get_memories("proj_B")

        assert len(mems_a) == 1
        assert len(mems_b) == 1
        assert mems_a[0].key == "reqA"
        assert mems_b[0].key == "reqB"

    def test_agent_context_builder(self):
        ctx_fe = build_agent_context(
            project_id="proj_ctx",
            agent_name="frontend",
            prompt="Build React UI Components",
            state={"plan": {"functional_requirements": ["FR-1: Responsive navbar"]}, "architecture": {"components": ["Navbar", "Sidebar"]}}
        )
        assert "Frontend Focus" in ctx_fe or "Navbar" in ctx_fe

        ctx_be = build_agent_context(
            project_id="proj_ctx",
            agent_name="backend",
            prompt="Build REST API",
            state={"architecture": {"routes": ["GET /api/users"]}, "database": "CREATE TABLE users (id SERIAL PRIMARY KEY);"}
        )
        assert "API Specs" in ctx_be or "users" in ctx_be

    def test_context_size_limit(self):
        big_query = "x" * 10000
        res = retrieve_relevant_memory(project_id="proj_limit", query=big_query, agent_name="frontend", max_tokens=500)
        assert res["token_count"] <= 1500  # Enforces reasonable context token budget

    def test_memory_summarization(self, memory_inst):
        for i in range(40):
            imp = ImportanceLevel.CRITICAL if i < 5 else (ImportanceLevel.HIGH if i < 10 else ImportanceLevel.LOW)
            memory_inst.save("proj_sum", MemoryType.REQUIREMENT, f"key_{i}", f"val_{i}", "planner", importance=imp)

        purged = memory_inst.summarize("proj_sum", max_items=20)
        assert purged > 0
        remaining = memory_inst.long_term.get_memories("proj_sum")
        assert len(remaining) <= 20
        # Verify CRITICAL items were preserved
        criticals = [m for m in remaining if m.importance == ImportanceLevel.CRITICAL]
        assert len(criticals) == 5

    def test_cross_generation_memory(self, memory_inst):
        # Gen 1 stores architectural choice
        memory_inst.save("proj_cg", MemoryType.DECISION, "db", "PostgreSQL", "architect", generation_id="gen_1")
        memory_inst.save_decision("proj_cg", "Use PostgreSQL", "Relational ordering", "architect", generation_id="gen_1")

        # Gen 2 retrieves project memory from Gen 1
        res = memory_inst.retrieve("proj_cg", query="database", agent_name="backend", generation_id="gen_2")
        assert any("PostgreSQL" in d["decision"] for d in res["decisions"])

    def test_secret_sanitization(self, memory_inst):
        mem = memory_inst.save("proj_sec", MemoryType.USER_PREFERENCE, "db_pass", {"password": "super_secret_123", "theme": "dark"}, "user")
        assert mem.value["password"] == "[REDACTED_SECRET]"
        assert mem.value["theme"] == "dark"

    def test_decision_explainability(self, memory_inst):
        memory_inst.save_decision("proj_exp", "Use PostgreSQL database engine", "High relational consistency and 3NF schema support", "Architect Agent")
        explanation = memory_inst.explain_decision("proj_exp", "PostgreSQL")
        assert "Architect Agent" in explanation["explanation"]
        assert "relational consistency" in explanation["explanation"]

    def test_memory_api_endpoints(self, app_client):
        # Create memory via manager first
        global_memory_manager.save("proj_api", MemoryType.REQUIREMENT, "api_req", "JWT Auth Required", "planner")
        global_memory_manager.save_decision("proj_api", "Use FastAPI", "High async performance", "architect")

        res = app_client.get("/api/projects/proj_api/memory")
        assert res.status_code == 200
        body = res.json()
        assert body["memories_count"] >= 1
        assert body["decisions_count"] >= 1

        search_res = app_client.post("/api/projects/proj_api/memory/search", json={"query": "FastAPI", "top_k": 5})
        assert search_res.status_code == 200
        assert search_res.json()["status"] == "success"

        exp_res = app_client.get("/api/projects/proj_api/explain?topic=FastAPI")
        assert exp_res.status_code == 200
        assert "FastAPI" in exp_res.json()["explanation"]
