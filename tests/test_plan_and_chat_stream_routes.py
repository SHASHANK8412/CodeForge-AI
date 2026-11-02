"""
Regression tests for /plan and /chat/stream.

/plan used to run the whole project-generation graph just to return a plan and architecture;
/chat/stream used to run that graph for every chat message. Both now reuse the smaller paths.
"""
import json

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_plan_runs_only_planner_and_architect(monkeypatch):
    from backend.graph import parallel_workflow as wf
    calls = []

    async def planner(state):
        calls.append("planner")
        assert state["prompt"] == "Build a todo API"
        return {"plan": "1. models\n2. routes"}

    async def architect(state):
        calls.append("architect")
        assert state["plan"] == "1. models\n2. routes", "architect must see the planner's output"
        return {"architecture": "## High-Level Architecture\nFastAPI"}

    def must_not_run(*_a, **_k):
        raise AssertionError("/plan must not run the build stages")

    monkeypatch.setattr(wf, "planner_node", planner)
    monkeypatch.setattr(wf, "architect_node", architect)
    monkeypatch.setattr(wf, "backend_node", must_not_run, raising=False)
    monkeypatch.setattr(wf, "testing_node", must_not_run, raising=False)

    res = client.post("/plan", json={"message": "Build a todo API", "session_id": "s1"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert calls == ["planner", "architect"]
    assert body["plan"] == "1. models\n2. routes"
    assert body["architecture"].startswith("## High-Level Architecture")
    assert body["session_id"] == "s1"
    assert isinstance(body["elapsed_ms"], float)


def test_chat_stream_emits_the_chat_message_payload(monkeypatch):
    import backend.routes.chat as chat_routes
    seen = {}

    async def fake_chat_message(request):
        seen["message"] = request.message
        return {"success": True, "response": "hello", "intent": "EXPLANATION"}

    monkeypatch.setattr(chat_routes, "chat_message", fake_chat_message)
    res = client.post("/chat/stream", json={"message": "What is REST?"})
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/event-stream")

    events = [json.loads(chunk[len("data: "):]) for chunk in res.text.split("\n\n") if chunk.startswith("data: ")]
    assert seen["message"] == "What is REST?"
    assert [e["type"] for e in events] == ["message", "timing"]
    assert events[0]["response"] == "hello" and events[0]["intent"] == "EXPLANATION"
    assert events[1]["route"] == "chat_stream" and events[1]["elapsed_ms"] >= 0


def test_architecture_check_reports_missing_sections():
    from backend.graph.architecture_check import REQUIRED_SECTIONS, enforce_architecture_sections, validate_architecture_sections
    full = "\n".join(f"## {i}. {s}\ntext" for i, s in enumerate(REQUIRED_SECTIONS, 1))
    assert validate_architecture_sections(full) == (True, [])
    assert enforce_architecture_sections(full) == full

    partial = "# High-Level Architecture\n## database schema\n"
    complete, missing = validate_architecture_sections(partial)
    assert complete is False and "High-Level Architecture" not in missing and "Database Schema" not in missing
    assert missing == REQUIRED_SECTIONS[2:]
    # A section named only in body text (not a heading) does not count.
    assert "API Specifications" in validate_architecture_sections("We list API Specifications later.")[1]
    assert "Status: Incomplete" in enforce_architecture_sections(partial)
