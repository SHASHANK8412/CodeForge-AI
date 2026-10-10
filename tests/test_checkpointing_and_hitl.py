"""
test_checkpointing_and_hitl.py
===============================
Comprehensive test suite for AIForge Human-in-the-Loop (HITL) and Checkpointing Architecture:
- PersistentCheckpointSaver storage, persistence across process restarts, and recovery
- LangGraph interruption at Checkpoint 1 (Architecture Review)
- Human approval & seamless pipeline resumption
- Human rejection with revision feedback incorporation
- Checkpoint 2 (Final Quality & Export Review)
- GenerationManager HITL orchestration
- FastAPI REST endpoints (/api/projects/{id}/approve, /reject, /status)
- Database checkpoint schema models
"""

import os
import shutil
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.graph.project_state import ProjectState
from backend.graph.persistent_checkpointer import PersistentCheckpointSaver
from backend.graph.parallel_workflow import (
    parallel_graph,
    human_approval_node,
    final_approval_node,
    route_after_architecture_approval,
    route_after_final_approval,
    route_after_testing,
    architect_node,
)
from backend.generation.manager import GenerationManager, _store
from backend.database.models import WorkflowSessionModel, WorkflowCheckpointModel
from backend.database.connection import init_db
from backend.main import app


# ---------------------------------------------------------------------------
# Test 1: PersistentCheckpointSaver Storage & Cross-Session Recovery
# ---------------------------------------------------------------------------

def test_persistent_checkpoint_saver_persistence_and_recovery():
    """Verify that checkpoint state persists to disk and recovers cleanly in new instances."""
    temp_dir = tempfile.mkdtemp(prefix="aiforge_chkpt_test_")
    try:
        saver1 = PersistentCheckpointSaver(storage_dir=temp_dir)
        thread_id = "test-proj-session-101"
        config = {"configurable": {"thread_id": thread_id}}

        checkpoint_data = {
            "v": 1,
            "id": "chk-001",
            "ts": "2026-08-17T12:00:00Z",
            "channel_values": {
                "project_id": "test_project",
                "status": "WAITING_FOR_APPROVAL",
                "approval_required": True,
                "approval_stage": "architecture",
                "current_agent": "architect",
                "workflow_progress": 25,
            },
            "channel_versions": {"project_id": 1, "status": 1},
            "versions_seen": {},
        }
        metadata = {"source": "architect", "step": 2}

        # Put checkpoint
        saved_config = saver1.put(config, checkpoint_data, metadata, new_versions={"project_id": 1, "status": 1})
        assert saved_config["configurable"]["thread_id"] == thread_id

        # Put pending writes
        saver1.put_writes(saved_config, [("channel_val", "update_1")], task_id="task_001")

        # Verify in memory
        loaded_tuple = saver1.get_tuple(config)
        assert loaded_tuple is not None
        assert loaded_tuple.checkpoint["channel_values"]["project_id"] == "test_project"
        assert loaded_tuple.checkpoint["channel_values"]["status"] == "WAITING_FOR_APPROVAL"

        # Simulate fresh Python process restart by instantiating new saver with same directory
        saver2 = PersistentCheckpointSaver(storage_dir=temp_dir)
        recovered_tuple = saver2.get_tuple(config)

        assert recovered_tuple is not None
        assert recovered_tuple.checkpoint["id"] == "chk-001"
        assert recovered_tuple.checkpoint["channel_values"]["project_id"] == "test_project"
        assert recovered_tuple.checkpoint["channel_values"]["status"] == "WAITING_FOR_APPROVAL"


        # Test listing checkpoints
        checkpoints_list = list(saver2.list(config))
        assert len(checkpoints_list) >= 1
        assert checkpoints_list[0].checkpoint["id"] == "chk-001"

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test 2: Architecture Human Approval Checkpoint & Interruption
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_human_approval_node_formats_request():
    """Verify human_approval_node constructs comprehensive approval payload."""
    state: ProjectState = {
        "project_id": "FinTechApp",
        "project_name": "FinTechApp",
        "session_id": "fintech-123",
        "architecture": {
            "frontend": "React + Vite + Tailwind",
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "authentication": "JWT Bearer",
            "components": ["Auth Module", "Trading Dashboard", "Ledger DB Schema"],
            "files": ["backend/main.py", "backend/models.py", "frontend/src/App.jsx"],
            "risks": ["Validate database credentials before running migrations"]
        },
        "approval_status": "pending",
    }

    result = await human_approval_node(state)

    assert result["approval_required"] is True
    assert result["approval_stage"] == "architecture"
    assert result["status"] == "WAITING_FOR_APPROVAL"
    assert result["workflow_progress"] == 25

    req = result["approval_request"]
    assert req["stage"] == "architecture"
    assert req["tech_stack"]["backend"] == "FastAPI"
    assert req["tech_stack"]["database"] == "PostgreSQL"
    assert "Auth Module" in req["components"]
    assert "Frontend Agent" in req["agents_ready"]
    assert len(req["expected_files"]) >= 3


def test_route_after_architecture_approval():
    """Verify routing decisions based on human approval/rejection."""
    # Approved -> dispatch_parallel
    assert route_after_architecture_approval({"approval_status": "approved"}) == "dispatch_parallel"
    assert route_after_architecture_approval({"approval_status": "APPROVED"}) == "dispatch_parallel"

    # Rejected -> architect
    assert route_after_architecture_approval({"approval_status": "rejected"}) == "architect"
    assert route_after_architecture_approval({"approval_status": "REJECTED"}) == "architect"

    # Pending -> human_approval
    assert route_after_architecture_approval({"approval_status": "pending"}) == "human_approval"
    assert route_after_architecture_approval({}) == "human_approval"


# ---------------------------------------------------------------------------
# Test 3: Human Rejection with Feedback Incorporation
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_architect_incorporates_rejection_feedback(monkeypatch):
    """Verify architect_node strictly incorporates user feedback upon rejection."""
    from backend.graph import parallel_workflow
    from unittest.mock import AsyncMock

    captured_prompts = []

    async def mock_architect_run(prompt):
        captured_prompts.append(prompt)
        return '{"frontend": "React", "backend": "FastAPI", "database": "PostgreSQL", "components": ["Auth"]}'

    monkeypatch.setattr(parallel_workflow.architect, "run_async", mock_architect_run)

    state_with_feedback: ProjectState = {
        "plan": {"project_name": "TestApp"},
        "user_feedback": "Reject. Use PostgreSQL and FastAPI instead of MongoDB and Express.",
        "session_id": "test_sess_fb",
    }

    res = await architect_node(state_with_feedback)

    assert len(captured_prompts) == 1
    assert "CRITICAL HUMAN REVISION FEEDBACK" in captured_prompts[0]
    assert "Use PostgreSQL and FastAPI instead of MongoDB and Express" in captured_prompts[0]
    assert res["approval_required"] is True
    assert res["approval_stage"] == "architecture"


# ---------------------------------------------------------------------------
# Test 4: Final Quality & Project Export Review Checkpoint
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_final_approval_node_formats_request():
    """Verify final_approval_node constructs comprehensive test & quality review payload."""
    state: ProjectState = {
        "project_id": "ECommercePro",
        "project_name": "ECommercePro",
        "files": {
            "frontend/src/App.jsx": "...",
            "backend/main.py": "...",
            "backend/models.py": "...",
        },
        "test_results": {
            "passed": 12,
            "failed": 0,
            "success": True,
            "failures": []
        },
        "quality_score": 98.5,
        "fixes": [{"file": "backend/main.py", "reason": "CORS fix"}],
        "approval_status": "pending",
    }

    result = await final_approval_node(state)

    assert result["approval_required"] is True
    assert result["approval_stage"] == "final"
    assert result["status"] == "WAITING_FOR_APPROVAL"
    assert result["workflow_progress"] == 85

    req = result["approval_request"]
    assert req["stage"] == "final"
    assert req["files_count"] == 3
    assert req["tests_passed"] == 12
    assert req["tests_failed"] == 0
    assert req["test_success"] is True
    assert req["quality_score"] == 98.5
    assert req["fixes_applied"] == 1


def test_route_after_final_approval():
    """Verify routing decisions at final approval checkpoint."""
    # Approved -> packaging
    assert route_after_final_approval({"approval_status": "approved", "approval_stage": "final"}) == "packaging"

    # Rejected -> debug
    assert route_after_final_approval({"approval_status": "rejected", "approval_stage": "final"}) == "debug"

    # Pending -> final_approval
    assert route_after_final_approval({"approval_status": "pending", "approval_stage": "final"}) == "final_approval"


# ---------------------------------------------------------------------------
# Test 5: Self-Correction Loop & MAX_RETRIES = 3 Routing
# ---------------------------------------------------------------------------

def test_route_after_testing_bounds_retries():
    """Verify that route_after_testing routes to debug on fail and stops at max retries."""
    # Pass -> final_approval
    pass_state: ProjectState = {
        "execution_results": {"exit_code": 0},
        "test_results": {"success": True},
    }
    assert route_after_testing(pass_state) == "final_approval"

    # Fail on attempt 1 -> debug
    fail_state_1: ProjectState = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False},
        "repair_attempt": 1,
        "max_repair_attempts": 3,
    }
    assert route_after_testing(fail_state_1) == "debug"

    # Fail on attempt 3 (max reached) -> final_approval for human escalation
    fail_state_max: ProjectState = {
        "execution_results": {"exit_code": 1},
        "test_results": {"success": False},
        "repair_attempt": 3,
        "max_repair_attempts": 3,
    }
    assert route_after_testing(fail_state_max) == "final_approval"


# ---------------------------------------------------------------------------
# Test 6: GenerationManager HITL Approval, Rejection, and Status
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_generation_manager_approve_and_reject_flow():
    """Verify GenerationManager approve_generation and reject_generation methods."""
    mgr = GenerationManager()
    gen_id = "test-gen-hitl-001"

    # Register mock generation in store
    _store.create(project_id="CRMApp", user_id="tester", prompt="Build a CRM", gen_id=gen_id)
    _store.update_status(gen_id, "waiting_for_approval")

    # Seed LangGraph checkpointer for this thread
    config = {"configurable": {"thread_id": gen_id}}
    initial_state: ProjectState = {
        "project_id": "CRMApp",
        "session_id": gen_id,
        "approval_stage": "architecture",
        "approval_status": "pending",
        "approval_required": True,
        "approval_request": {"stage": "architecture", "title": "CRM Review"},
        "status": "WAITING_FOR_APPROVAL",
    }
    parallel_graph.update_state(config, initial_state, as_node="human_approval")

    # 1. Test get_status
    status_data = mgr.get_status(gen_id)
    assert status_data["generation_id"] == gen_id
    assert status_data["approval_stage"] == "architecture"

    # 2. Test reject with empty feedback raises ValueError
    with pytest.raises(ValueError, match="Rejection feedback cannot be empty"):
        await mgr.reject_generation(gen_id, "")

    # 3. Test reject with valid feedback
    with patch.object(mgr, "_run_pipeline", new=AsyncMock()):
        rej_res = await mgr.reject_generation(gen_id, "Please add PostgreSQL schema with roles.")
        assert rej_res["status"] == "success"
        assert rej_res["stage"] == "architecture"

    # 4. Test approve
    with patch.object(mgr, "_run_pipeline", new=AsyncMock()):
        appr_res = await mgr.approve_generation(gen_id, notes="Approved for parallel generation.")
        assert appr_res["status"] == "success"
        assert appr_res["stage"] == "architecture"


# ---------------------------------------------------------------------------
# Test 7: FastAPI REST Endpoints Integration
# ---------------------------------------------------------------------------

def test_fastapi_hitl_rest_endpoints():
    """Verify /api/projects/{id}/status, /approve, /reject REST endpoints."""
    client = TestClient(app)
    proj_id = "test-proj-rest-002"

    _store.create(project_id=proj_id, user_id="tester", prompt="Build a Blog", gen_id=proj_id)
    _store.update_status(proj_id, "waiting_for_approval")

    config = {"configurable": {"thread_id": proj_id}}
    parallel_graph.update_state(config, {
        "project_id": proj_id,
        "approval_stage": "architecture",
        "approval_status": "pending",
        "approval_required": True,
        "approval_request": {"stage": "architecture", "title": "Blog Review"},
        "status": "WAITING_FOR_APPROVAL",
    }, as_node="human_approval")

    # 1. GET /api/projects/{project_id}/status
    resp = client.get(f"/api/projects/{proj_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["generation_id"] == proj_id

    # 2. POST /api/projects/{project_id}/reject with empty feedback -> 400
    rej_bad = client.post(f"/api/projects/{proj_id}/reject", json={"feedback": ""})
    assert rej_bad.status_code == 400

    # 3. POST /api/projects/{project_id}/reject with feedback -> 200
    with patch("backend.generation.manager.global_generation_manager._run_pipeline", new=AsyncMock()):
        rej_good = client.post(f"/api/projects/{proj_id}/reject", json={"feedback": "Add tag support."})
        assert rej_good.status_code == 200
        assert rej_good.json()["status"] == "success"

    # 4. POST /api/projects/{project_id}/approve -> 200
    with patch("backend.generation.manager.global_generation_manager._run_pipeline", new=AsyncMock()):
        appr_good = client.post(f"/api/projects/{proj_id}/approve", json={"notes": "All good."})
        assert appr_good.status_code == 200
        assert appr_good.json()["status"] == "success"


# ---------------------------------------------------------------------------
# Test 8: Database Checkpoint Schema Models
# ---------------------------------------------------------------------------

def test_database_models_and_init():
    """Verify database checkpoint tables and schema creation."""
    init_db()
    sess = WorkflowSessionModel(
        id="sess_1",
        project_id="P1",
        thread_id="G1",
        status="WAITING_FOR_APPROVAL",
        approval_stage="architecture",
        approval_status="pending",
    )
    assert sess.project_id == "P1"
    assert sess.thread_id == "G1"
    assert sess.approval_stage == "architecture"

    chk = WorkflowCheckpointModel(
        id="chk_rec_1",
        thread_id="G1",
        checkpoint_id="chk_1",
        parent_id="chk_0",
        checkpoint_data="{}",
        metadata_data="{}",
    )
    assert chk.checkpoint_id == "chk_1"
    assert chk.thread_id == "G1"

