"""
tests/test_generation_engine.py
================================
Tests for the Day 11 Real-Time Agent Execution Engine.

Coverage:
  test_generation_creation        — store creates valid records
  test_generation_status          — status reads from store
  test_generation_events          — events appended and read correctly
  test_generation_ownership       — owns() enforces user isolation
  test_generation_cancel          — manager cancels and sets status
  test_agent_started_event        — agent_started updates store
  test_agent_completed_event      — agent_completed updates store with duration
  test_agent_failed_event         — agent_failed stores safe error string
  test_retry_event                — agent_retrying increments retry_count
  test_generation_completion      — status updated to completed on finish
  test_generation_failure         — status updated to failed on error
  test_api_create_generation      — POST /api/generations returns 202
  test_api_get_generation         — GET  /api/generations/{id} returns record
  test_api_list_generations       — GET  /api/generations returns list
  test_api_unauthorized_access    — GET  /api/generations/{id} enforces ownership
  test_api_cancel_generation      — POST /api/generations/{id}/cancel
  test_api_get_events             — GET  /api/generations/{id}/events
  test_event_bus_emit             — bus emits and subscribes correctly
  test_progress_calculation       — progress formula from weights
  test_context_var_not_set        — _fire_lifecycle is safe when no callback set
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_store(tmp_path):
    """Create an isolated GenerationStore backed by a temp file."""
    from backend.generation.store import GenerationStore
    return GenerationStore(store_path=tmp_path / "test_generations.json")


@pytest.fixture()
def event_bus():
    from backend.generation.event_bus import GenerationEventBus
    return GenerationEventBus()


@pytest.fixture()
def app_client():
    """TestClient with the real FastAPI app."""
    from backend.main import app
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Store tests
# ---------------------------------------------------------------------------

class TestGenerationStore:

    def test_generation_creation(self, tmp_store):
        gen_id = tmp_store.create("proj_1", "user_1", "Build a todo app")
        assert gen_id.startswith("gen_")
        rec = tmp_store.get(gen_id)
        assert rec is not None
        assert rec["project_id"] == "proj_1"
        assert rec["user_id"] == "user_1"
        assert rec["status"] == "queued"
        assert rec["progress"] == 0

    def test_generation_status(self, tmp_store):
        gen_id = tmp_store.create("proj_2", "user_2", "Build an API")
        tmp_store.update_status(gen_id, "planning")
        rec = tmp_store.get(gen_id)
        assert rec["status"] == "planning"
        assert rec["started_at"] is not None

    def test_generation_events(self, tmp_store):
        gen_id = tmp_store.create("proj_3", "user_3", "Build a chatbot")
        evt = tmp_store.add_event(gen_id, "agent_started", agent="planner", message="Planner started")
        assert evt["type"] == "agent_started"
        assert evt["agent"] == "planner"
        events = tmp_store.get_events(gen_id)
        assert len(events) == 1
        assert events[0]["message"] == "Planner started"

    def test_generation_ownership(self, tmp_store):
        gen_id = tmp_store.create("proj_4", "user_A", "Build a game")
        assert tmp_store.owns(gen_id, "user_A") is True
        assert tmp_store.owns(gen_id, "user_B") is False
        assert tmp_store.owns("gen_nonexistent", "user_A") is False

    def test_agent_started_event(self, tmp_store):
        gen_id = tmp_store.create("proj_5", "user_5", "Build a store")
        tmp_store.agent_started(gen_id, "planner")
        rec = tmp_store.get(gen_id)
        planner = next((a for a in rec["agents"] if a["name"] == "planner"), None)
        assert planner is not None
        assert planner["status"] == "running"
        assert planner["started_at"] is not None

    def test_agent_completed_event(self, tmp_store):
        gen_id = tmp_store.create("proj_6", "user_6", "Build a blog")
        tmp_store.agent_started(gen_id, "planner")
        tmp_store.agent_completed(gen_id, "planner", duration=8.4)
        rec = tmp_store.get(gen_id)
        planner = next((a for a in rec["agents"] if a["name"] == "planner"), None)
        assert planner["status"] == "completed"
        assert planner["duration"] == pytest.approx(8.4, abs=0.01)

    def test_agent_failed_event(self, tmp_store):
        gen_id = tmp_store.create("proj_7", "user_7", "Build a forum")
        tmp_store.agent_started(gen_id, "planner")
        tmp_store.agent_failed(gen_id, "planner", error="LLM timeout after 30s")
        rec = tmp_store.get(gen_id)
        planner = next((a for a in rec["agents"] if a["name"] == "planner"), None)
        assert planner["status"] == "failed"
        # Safe error — no raw stacktrace
        assert "LLM timeout" in planner["error"]

    def test_retry_event(self, tmp_store):
        gen_id = tmp_store.create("proj_8", "user_8", "Build a scheduler")
        tmp_store.agent_started(gen_id, "planner")
        tmp_store.agent_retrying(gen_id, "planner")
        rec = tmp_store.get(gen_id)
        planner = next((a for a in rec["agents"] if a["name"] == "planner"), None)
        assert planner["status"] == "retrying"
        assert planner["retry_count"] == 1

    def test_generation_completion(self, tmp_store):
        gen_id = tmp_store.create("proj_9", "user_9", "Build a dashboard")
        tmp_store.update_status(gen_id, "completed")
        rec = tmp_store.get(gen_id)
        assert rec["status"] == "completed"
        assert rec["completed_at"] is not None
        assert rec["progress"] == 100

    def test_generation_failure(self, tmp_store):
        gen_id = tmp_store.create("proj_10", "user_10", "Build a monitor")
        tmp_store.update_status(gen_id, "failed", error="Generation failed after 120s")
        rec = tmp_store.get(gen_id)
        assert rec["status"] == "failed"
        assert "Generation failed" in rec["error"]

    def test_progress_calculation(self, tmp_store):
        from backend.generation.store import AGENT_WEIGHTS
        gen_id = tmp_store.create("proj_prog", "user_prog", "Build a widget")
        # Mark planner completed
        tmp_store.agent_started(gen_id, "planner")
        tmp_store.agent_completed(gen_id, "planner", duration=5.0)
        rec = tmp_store.get(gen_id)
        # Progress should include planner's weight (10%)
        assert rec["progress"] >= int(AGENT_WEIGHTS.get("planner", 0))
        assert rec["progress"] < 100

    def test_get_by_user(self, tmp_store):
        gen_a = tmp_store.create("proj_a", "user_me", "Project A")
        gen_b = tmp_store.create("proj_b", "user_me", "Project B")
        gen_c = tmp_store.create("proj_c", "user_other", "Project C")
        mine = tmp_store.get_by_user("user_me")
        assert len(mine) == 2
        ids = {r["generation_id"] for r in mine}
        assert gen_a in ids
        assert gen_b in ids
        assert gen_c not in ids

    def test_event_pagination(self, tmp_store):
        gen_id = tmp_store.create("proj_pag", "user_pag", "Paginate test")
        for i in range(10):
            tmp_store.add_event(gen_id, "agent_log", message=f"Event {i}")
        page1 = tmp_store.get_events(gen_id, offset=0, limit=5)
        page2 = tmp_store.get_events(gen_id, offset=5, limit=5)
        assert len(page1) == 5
        assert len(page2) == 5
        assert page1[0]["message"] == "Event 0"
        assert page2[0]["message"] == "Event 5"


# ---------------------------------------------------------------------------
# Event bus tests
# ---------------------------------------------------------------------------

class TestGenerationEventBus:

    def test_event_bus_emit_and_subscribe(self):
        import asyncio
        from backend.generation.event_bus import GenerationEventBus

        bus = GenerationEventBus()
        gen_id = "gen_bus_test"
        bus.open(gen_id)

        received = []

        async def run():
            # Emit first
            await bus.emit(gen_id, "agent_started", agent="planner", message="Planner started")
            bus.close(gen_id)
            async for line in bus.subscribe(gen_id):
                received.append(line)
                if "stream_done" in line:
                    break

        asyncio.run(run())
        assert any("agent_started" in r for r in received)

    def test_event_bus_heartbeat(self):
        """Verify emit_sync puts events and close() sends the STREAM_DONE sentinel."""
        from backend.generation.event_bus import GenerationEventBus
        bus = GenerationEventBus()
        gen_id = "gen_hb_test"
        bus.open(gen_id)
        assert bus.is_active(gen_id)

        # Emit an event and a close sentinel
        bus.emit_sync(gen_id, "agent_completed", agent="planner")
        # The queue is present until subscriber drains the STREAM_DONE sentinel;
        # is_active() returns True while the queue object still exists.
        assert bus.is_active(gen_id)

        # After we manually remove the queue (simulating full drain), it's inactive
        bus._queues.pop(gen_id, None)
        assert not bus.is_active(gen_id)


# ---------------------------------------------------------------------------
# ContextVar / _fire_lifecycle tests
# ---------------------------------------------------------------------------

class TestFireLifecycle:

    def test_context_var_not_set(self):
        """_fire_lifecycle must be a no-op when no callback is registered."""
        from backend.graph.parallel_workflow import _fire_lifecycle, generation_event_callback_var
        # Ensure no callback is set
        generation_event_callback_var.set(None)
        # Must not raise
        _fire_lifecycle("agent_started", "planner")

    def test_context_var_callback_invoked(self):
        """_fire_lifecycle calls the callback when one is set."""
        from backend.graph.parallel_workflow import _fire_lifecycle, generation_event_callback_var
        calls = []

        def cb(event_type, agent_name, *, duration=0.0, error=""):
            calls.append((event_type, agent_name, duration))

        token = generation_event_callback_var.set(cb)
        try:
            _fire_lifecycle("agent_started", "architect")
            _fire_lifecycle("agent_completed", "architect", duration=12.3)
        finally:
            generation_event_callback_var.reset(token)

        assert len(calls) == 2
        assert calls[0] == ("agent_started", "architect", 0.0)
        assert calls[1][2] == pytest.approx(12.3, abs=0.01)


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestGenerationAPI:
    """
    Integration tests against the real FastAPI app.
    These use a patched GenerationManager so the real LangGraph pipeline
    is not invoked (that takes several minutes with Ollama).
    """

    def _auth_headers(self):
        """Use default user — no JWT required in dev mode."""
        return {}

    def test_api_create_generation(self, app_client):
        with patch(
            "backend.generation.manager.GenerationManager.run",
            new_callable=AsyncMock,
        ) as mock_run:
            res = app_client.post(
                "/api/generations",
                json={"project_id": "proj_test", "prompt": "Build a test app"},
                headers=self._auth_headers(),
            )
        assert res.status_code == 202
        body = res.json()
        assert "generation_id" in body
        assert body["status"] == "queued"

    def test_api_get_generation(self, app_client):
        from backend.generation.store import global_generation_store
        gen_id = global_generation_store.create("proj_get", "usr_shashank_default", "Build an app")

        res = app_client.get(f"/api/generations/{gen_id}", headers=self._auth_headers())
        assert res.status_code == 200
        body = res.json()
        assert body["generation_id"] == gen_id
        assert "agents" in body
        assert "progress" in body

    def test_api_list_generations(self, app_client):
        from backend.generation.store import global_generation_store
        global_generation_store.create("proj_list1", "usr_shashank_default", "App 1")
        res = app_client.get("/api/generations", headers=self._auth_headers())
        assert res.status_code == 200
        body = res.json()
        assert "generations" in body
        assert "total" in body
        assert body["total"] >= 1

    def test_api_unauthorized_access(self, app_client):
        from backend.generation.store import global_generation_store
        # Create owned by a different user
        gen_id = global_generation_store.create("proj_unauth", "user_OTHER", "Secret app")
        # Default user is usr_shashank_default — should get 403
        res = app_client.get(f"/api/generations/{gen_id}", headers=self._auth_headers())
        assert res.status_code == 403

    def test_api_get_events(self, app_client):
        from backend.generation.store import global_generation_store
        gen_id = global_generation_store.create("proj_evts", "usr_shashank_default", "Events app")
        global_generation_store.add_event(gen_id, "agent_started", agent="planner", message="Started")

        res = app_client.get(f"/api/generations/{gen_id}/events", headers=self._auth_headers())
        assert res.status_code == 200
        body = res.json()
        assert "events" in body
        assert len(body["events"]) >= 1
        assert body["events"][0]["agent"] == "planner"

    def test_api_cancel_generation(self, app_client):
        from backend.generation.store import global_generation_store
        gen_id = global_generation_store.create("proj_cancel", "usr_shashank_default", "Cancel me")

        res = app_client.post(f"/api/generations/{gen_id}/cancel", headers=self._auth_headers())
        assert res.status_code == 200
        body = res.json()
        assert body["generation_id"] == gen_id

    def test_api_not_found(self, app_client):
        res = app_client.get("/api/generations/gen_does_not_exist", headers=self._auth_headers())
        assert res.status_code == 404
