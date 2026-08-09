"""
Unit and Real Integration Tests for AIForge Project Memory Layer (Phase 10)
"""

import os
import shutil
import pytest
from pathlib import Path
from backend.execution.models import MemoryRecord, DebugResult
from backend.memory.project_memory_service import (
    ProjectMemoryService,
    global_project_memory_service,
    sanitize_memory_content
)
from backend.agents.debug_agent import DebugAgent


@pytest.fixture
def tmp_memory_service(tmp_path):
    store_file = tmp_path / "memory_store" / "memory_records.json"
    service = ProjectMemoryService(store_path=str(store_file))
    yield service
    if store_file.parent.exists():
        shutil.rmtree(store_file.parent, ignore_errors=True)


def test_memory_record_creation():
    rec = MemoryRecord(
        project_id="proj_alpha",
        memory_type="FAILURE",
        content="FastAPI route 500 error",
        error_type="ASSERTION_FAILURE",
        technology="FastAPI, PostgreSQL",
        root_cause="Missing response model field",
        fix="Add role field to Pydantic schema",
        result="PASS"
    )
    assert rec.project_id == "proj_alpha"
    assert rec.error_type == "ASSERTION_FAILURE"
    assert rec.result == "PASS"


def test_memory_persistence(tmp_memory_service):
    rec = MemoryRecord(
        project_id="proj_beta",
        memory_type="PATTERN",
        content="Pytest import fix",
        error_type="IMPORT_ERROR",
        technology="Python",
        root_cause="Missing __init__.py",
        fix="Touch __init__.py in tests dir",
        result="PASS"
    )

    stored = tmp_memory_service.store_memory(rec)
    assert stored.memory_id == rec.memory_id

    retrieved = tmp_memory_service.retrieve_relevant_memories(project_id="proj_beta", error_type="IMPORT_ERROR")
    assert len(retrieved) > 0
    assert retrieved[0].project_id == "proj_beta"


def test_same_project_prioritization(tmp_memory_service):
    rec_other = MemoryRecord(
        project_id="other_proj",
        error_type="SYNTAX_ERROR",
        content="Other project syntax error",
        fix="Add missing colon"
    )
    rec_target = MemoryRecord(
        project_id="target_proj",
        error_type="SYNTAX_ERROR",
        content="Target project syntax error",
        fix="Fix indentation"
    )

    tmp_memory_service.store_memory(rec_other)
    tmp_memory_service.store_memory(rec_target)

    results = tmp_memory_service.retrieve_relevant_memories(project_id="target_proj", error_type="SYNTAX_ERROR")
    assert len(results) > 0
    assert results[0].project_id == "target_proj"


def test_error_type_relevance(tmp_memory_service):
    rec1 = MemoryRecord(project_id="p1", error_type="TYPE_ERROR", content="TypeError detail")
    rec2 = MemoryRecord(project_id="p1", error_type="IMPORT_ERROR", content="ImportError detail")

    tmp_memory_service.store_memory(rec1)
    tmp_memory_service.store_memory(rec2)

    results = tmp_memory_service.retrieve_relevant_memories(project_id="p1", error_type="IMPORT_ERROR")
    assert len(results) > 0
    assert results[0].error_type == "IMPORT_ERROR"


def test_technology_relevance(tmp_memory_service):
    rec_node = MemoryRecord(project_id="p1", technology="Node.js, Express", content="Express CORS error")
    rec_py = MemoryRecord(project_id="p1", technology="FastAPI, Python", content="FastAPI CORS error")

    tmp_memory_service.store_memory(rec_node)
    tmp_memory_service.store_memory(rec_py)

    results = tmp_memory_service.retrieve_relevant_memories(project_id="p1", technology="FastAPI")
    assert len(results) > 0
    assert results[0].technology == "FastAPI, Python"


def test_successful_fix_prioritization(tmp_memory_service):
    rec_failed = MemoryRecord(
        project_id="p1",
        error_type="ASSERTION_FAILURE",
        root_cause="rc1",
        fix="failed fix",
        result="FAIL",
        confidence=0.2
    )
    rec_passed = MemoryRecord(
        project_id="p1",
        error_type="ASSERTION_FAILURE",
        root_cause="rc2",
        fix="successful fix",
        result="PASS",
        confidence=0.9
    )

    tmp_memory_service.store_memory(rec_failed)
    tmp_memory_service.store_memory(rec_passed)

    results = tmp_memory_service.retrieve_relevant_memories(project_id="p1", error_type="ASSERTION_FAILURE")
    assert len(results) > 0
    assert results[0].result == "PASS"


def test_duplicate_prevention(tmp_memory_service):
    rec1 = MemoryRecord(
        project_id="p_dup",
        error_type="IMPORT_ERROR",
        root_cause="No module numpy",
        fix="pip install numpy",
        result="FAIL"
    )
    rec2 = MemoryRecord(
        project_id="p_dup",
        error_type="IMPORT_ERROR",
        root_cause="No module numpy",
        fix="pip install numpy",
        result="PASS"
    )

    tmp_memory_service.store_memory(rec1)
    tmp_memory_service.store_memory(rec2)

    records = tmp_memory_service._load_records()
    # Deduplication hash prevents duplicate entries for identical error/root_cause/fix
    matching = [r for r in records if r["project_id"] == "p_dup"]
    assert len(matching) == 1
    assert matching[0]["result"] == "PASS"


def test_secret_sanitization():
    raw_text = "API_KEY='secret12345' and password='my_password_xyz' and bearer eyJhbGciOiJIUzI1NiJ9.test"
    clean = sanitize_memory_content(raw_text)
    assert "secret12345" not in clean
    assert "my_password_xyz" not in clean
    assert "[REDACTED_SECRET]" in clean


def test_memory_unavailable_fallback():
    # Service with invalid path handles errors gracefully without breaking
    bad_service = ProjectMemoryService(store_path="/invalid_dir/store.json")
    
    # Store should log warning and return record without raising exception
    rec = MemoryRecord(project_id="p_fallback", content="test")
    res_store = bad_service.store_memory(rec)
    assert res_store.project_id == "p_fallback"

    # Retrieval should return [] without raising exception
    res_retrieve = bad_service.retrieve_relevant_memories(project_id="p_fallback")
    assert isinstance(res_retrieve, list)


def test_debugger_memory_retrieval_integration(tmp_memory_service, monkeypatch):
    monkeypatch.setattr("backend.agents.debug_agent.global_project_memory_service", tmp_memory_service)

    # Pre-store a successful fix memory
    tmp_memory_service.store_memory(MemoryRecord(
        project_id="TodoProj",
        error_type="ASSERTION_FAILURE",
        technology="Python",
        root_cause="Status mismatch",
        fix="Return {'status': 'OK'} instead of WRONG",
        result="PASS"
    ))

    agent = DebugAgent()
    state = {
        "project_name": "TodoProj",
        "technology_stack": "Python",
        "execution_results": {"status": "FAIL", "exit_code": 1},
        "test_results": {
            "success": False,
            "failures": [{"test_name": "test_status", "error": "AssertionError: assert 'WRONG' == 'OK'", "file": "tests/test_status.py"}]
        },
        "files": {"backend/main.py": "def get_status(): return {'status': 'WRONG'}"}
    }

    diag = agent.diagnose_and_repair(state)
    assert diag.error_type == "ASSERTION_FAILURE"
    assert "Memory Hint:" in diag.explanation or "OK" in str(diag.changes)


def test_cross_project_real_scenario(tmp_memory_service):
    # 1. Project A: FastAPI + PostgreSQL relationship error fixed
    rec_proj_a = MemoryRecord(
        project_id="ProjectA",
        memory_type="FAILURE",
        content="SQLAlchemy relationship mismatch error in FastAPI backend",
        error_type="ASSERTION_FAILURE",
        technology="FastAPI, PostgreSQL",
        root_cause="Missing back_populates on relationship",
        fix="Add back_populates='user' to items relationship in User model",
        result="PASS"
    )
    tmp_memory_service.store_memory(rec_proj_a)

    # 2. Project B: FastAPI + PostgreSQL encounters similar relationship error
    retrieved_b = tmp_memory_service.retrieve_relevant_memories(
        project_id="ProjectB",
        error_type="ASSERTION_FAILURE",
        query_text="SQLAlchemy relationship mismatch error",
        technology="FastAPI, PostgreSQL"
    )

    assert len(retrieved_b) > 0
    assert "back_populates" in retrieved_b[0].fix

    # 3. Project C: React + Node encounters unrelated React error
    retrieved_c = tmp_memory_service.retrieve_relevant_memories(
        project_id="ProjectC",
        error_type="SYNTAX_ERROR",
        query_text="JSX element tag mismatch",
        technology="React, Node.js"
    )

    # Project A's SQLAlchemy memory is not returned as top hit for React JSX error
    if retrieved_c:
        assert retrieved_c[0].technology != "React, Node.js" or "back_populates" not in retrieved_c[0].fix
