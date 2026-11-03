"""
Per-user data and the AI Chat agent core.

- Chat conversations, canvases, tasks, agent runs, AI-core memories and uploaded documents belong to the user
  who created them: another user gets 404 and never sees them in a listing.
- The AI Chat agent answers with the local model's text; when the model fails the run fails (503), with no
  invented answer, and only installed Ollama models are offered.
- No built-in demo records (food-delivery canvases, tasks, memories, RFC documents, agent runs) are served.
"""

import json

import pytest
from fastapi.testclient import TestClient

import backend.ai_core.agent_runtime as agent_runtime
import backend.ai_core.model_provider as model_provider
import backend.auth.service as auth_service
import backend.routes.ai_core_routes as ai_core_routes
import backend.routes.canvas_routes as canvas_routes
import backend.routes.chat as chat_routes
import backend.routes.task_routes as task_routes
from backend.ai_core.agent_memory import AgentMemoryManager
from backend.ai_core.agent_runtime import AgentRuntime
from backend.ai_core.rag_engine import RAGEngine
from backend.auth.security import create_access_token, hash_password
from backend.canvas.canvas_service import CanvasService
from backend.main import app
from backend.memory.conversation_manager import ConversationManager
from backend.memory.crud import ConversationRepository
from backend.memory.database import ConversationDatabase
from backend.services.llm import LLMUnavailableError
from backend.tasks.task_management_service import TaskManagementService


def _auth(uid):
    return {"Authorization": f"Bearer {create_access_token({'sub': uid})}"}


ALICE, BOB = _auth("alice"), _auth("bob")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("AIFORGE_AUTH_MODE", raising=False)   # real authentication, not the local-dev default user
    monkeypatch.delenv("AIFORGE_REQUIRE_AUTH", raising=False)
    users = {uid: {"id": uid, "name": uid, "email": f"{uid}@example.test", "password_hash": hash_password("pw"),
                   "created_at": "2026-01-01"} for uid in ("alice", "bob")}
    monkeypatch.setattr(auth_service, "USERS_DB", users)
    monkeypatch.setattr(auth_service, "USERS_FILE", tmp_path / "users.json")

    monkeypatch.setattr(chat_routes, "conversation_manager",
                        ConversationManager(ConversationRepository(ConversationDatabase(tmp_path / "chat.db"))))
    monkeypatch.setattr(canvas_routes, "global_canvas_service", CanvasService(str(tmp_path / "canvas")))
    monkeypatch.setattr(task_routes, "global_task_service", TaskManagementService(str(tmp_path / "tasks")))
    memories, rag = AgentMemoryManager(str(tmp_path / "mem")), RAGEngine(str(tmp_path / "rag"))
    for module in (agent_runtime, ai_core_routes):
        monkeypatch.setattr(module, "global_memory_manager", memories)
        monkeypatch.setattr(module, "global_rag_engine", rag)
    monkeypatch.setattr(ai_core_routes, "global_agent_runtime", AgentRuntime(str(tmp_path / "runs")))
    return TestClient(app)


# --- Ownership ----------------------------------------------------------------------------------------------

def test_chat_conversations_belong_to_their_owner(client):
    conv = client.post("/chat/new", json={"title": "alice's chat"}, headers=ALICE).json()["conversation"]
    cid = conv["conversation_id"]
    assert [c["conversation_id"] for c in client.get("/chat/list", headers=ALICE).json()["conversations"]] == [cid]
    assert client.get("/chat/list", headers=BOB).json()["conversations"] == []
    assert client.get(f"/chat/history/{cid}", headers=BOB).status_code == 404
    assert client.put(f"/chat/title/{cid}", json={"title": "taken"}, headers=BOB).status_code == 404
    assert client.delete(f"/chat/{cid}", headers=BOB).status_code == 404
    assert client.get(f"/chat/history/{cid}", headers=ALICE).json()["conversation"]["title"] == "alice's chat"
    assert client.get("/chat/list").status_code == 401


def test_canvases_belong_to_their_owner_and_have_no_fake_ai(client):
    assert client.get("/api/canvas", headers=ALICE).json()["canvases"] == [], "no built-in demo canvases"
    canvas = client.post("/api/canvas", json={"title": "Plan", "canvas_type": "TABLE"}, headers=ALICE).json()["canvas"]
    cid = canvas["id"]
    assert client.get("/api/canvas", headers=BOB).json()["canvases"] == []
    for method, path in (("GET", f"/api/canvas/{cid}"), ("PUT", f"/api/canvas/{cid}"), ("DELETE", f"/api/canvas/{cid}"),
                         ("GET", f"/api/canvas/{cid}/versions")):
        assert client.request(method, path, json={}, headers=BOB).status_code == 404, (method, path)
    # the canvas type change is stored (it used to be dropped by the API)
    updated = client.put(f"/api/canvas/{cid}", json={"canvas_type": "DOCUMENT", "content": "# Plan"}, headers=ALICE).json()
    assert updated["canvas"]["canvas_type"] == "DOCUMENT"
    assert client.post(f"/api/canvas/{cid}/ai-transform", json={"instruction": "add pricing"},
                       headers=ALICE).status_code in (404, 405)


def test_tasks_belong_to_their_owner_and_goal_decomposition_is_gone(client):
    assert client.get("/api/tasks", headers=ALICE).json()["tasks"] == [], "no built-in demo tasks"
    task = client.post("/api/tasks", json={"title": "Write docs", "priority": "HIGH"}, headers=ALICE).json()["task"]
    assert client.get("/api/tasks", headers=BOB).json()["tasks"] == []
    assert client.put(f"/api/tasks/{task['id']}", json={"status": "DONE"}, headers=BOB).status_code == 404
    assert client.delete(f"/api/tasks/{task['id']}", headers=BOB).status_code == 404
    nba = client.get("/api/tasks/next-best-action", headers=ALICE).json()["action"]
    assert nba["task"]["id"] == task["id"]
    assert client.get("/api/tasks/next-best-action", headers=BOB).json()["action"]["task"] is None
    assert client.post("/api/tasks/decompose", json={"goal": "x"}, headers=ALICE).status_code in (404, 405)


# --- AI core -----------------------------------------------------------------------------------------------

def test_agent_run_returns_the_models_answer_and_cites_only_the_users_documents(client, monkeypatch):
    seen = {}

    def fake_generate(system, prompt, model=None, task="general"):
        seen.update(system=system, prompt=prompt, model=model)
        return "Use a queue per tenant."
    monkeypatch.setattr(model_provider, "generate_text", fake_generate)
    monkeypatch.setattr(model_provider, "_installed_ollama_models",
                        lambda: [{"name": "qwen2.5:latest", "size": 1}, {"name": "nomic-embed-text:latest", "size": 1}])

    client.post("/api/ai-core/rag/upload", json={"filename": "bob.md", "content": "queue secrets of bob"}, headers=BOB)
    client.post("/api/ai-core/rag/upload", json={"filename": "alice.md", "content": "our queue design"}, headers=ALICE)
    res = client.post("/api/ai-core/agents/run", json={"prompt": "how should the queue work", "model_id": "qwen2.5"},
                      headers=ALICE)
    assert res.status_code == 201
    run = res.json()["run"]
    assert run["status"] == "COMPLETED" and run["response_text"] == "Use a queue per tenant."
    assert run["model_id"] == "qwen2.5:latest" and seen["model"] == "qwen2.5:latest"
    assert [c["source"] for c in run["citations"]] == ["alice.md"]
    assert "bob" not in seen["system"]
    assert [r["id"] for r in client.get("/api/ai-core/agents/runs", headers=ALICE).json()["runs"]] == [run["id"]]
    assert client.get("/api/ai-core/agents/runs", headers=BOB).json()["runs"] == []
    assert client.get(f"/api/ai-core/agents/runs/{run['id']}", headers=BOB).status_code == 404

    models = client.get("/api/ai-core/models", headers=ALICE).json()["models"]
    assert {m["id"] for m in models} == {"qwen2.5:latest", "nomic-embed-text:latest"}
    assert all(m["provider"] == "ollama" for m in models)


def test_a_failed_model_call_fails_the_run_instead_of_inventing_an_answer(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise LLMUnavailableError("general", "qwen2.5", "connection refused")
    monkeypatch.setattr(model_provider, "generate_text", unavailable)
    monkeypatch.setattr(model_provider, "_installed_ollama_models", lambda: [])
    res = client.post("/api/ai-core/agents/run", json={"prompt": "hello"}, headers=ALICE)
    assert res.status_code == 503 and "did not answer" in res.json()["detail"]
    runs = client.get("/api/ai-core/agents/runs", headers=ALICE).json()["runs"]
    assert runs[0]["status"] == "FAILED" and runs[0]["response_text"] == ""


def test_an_unreachable_ollama_lists_no_models(monkeypatch):
    class Down:
        def __init__(self, *a, **k):
            pass

        def list(self):
            raise ConnectionError("refused")
    import ollama
    monkeypatch.setattr(ollama, "Client", Down)
    assert model_provider.global_model_provider.list_models() == []


def test_demo_records_from_earlier_versions_are_not_loaded(tmp_path):
    (tmp_path / "runs").mkdir()
    (tmp_path / "runs" / "runs.json").write_text(json.dumps([{"id": "run_demo_agent", "user_id": "user_default",
                                                              "prompt": "x", "response_text": "14/14 tests"}]))
    (tmp_path / "rag").mkdir()
    (tmp_path / "rag" / "documents.json").write_text(json.dumps([{"id": "doc_arch_spec", "filename": "RFC-104-Order-Pipeline.md",
                                                                  "content_type": "markdown", "user_id": "user_default"}]))
    (tmp_path / "rag" / "chunks.json").write_text(json.dumps([{"chunk_id": "c", "document_id": "doc_arch_spec",
                                                               "filename": "RFC-104-Order-Pipeline.md", "text": "Kafka",
                                                               "citation_ref": "RFC-104"}]))
    assert AgentRuntime(str(tmp_path / "runs")).list_runs("user_default") == []
    assert RAGEngine(str(tmp_path / "rag")).search("Kafka") == []


# --- Release recommendation and local test timeout ------------------------------------------------------------

@pytest.mark.parametrize("verification,tests_passed,expected", [
    ("VERIFIED", True, "ready"),
    ("VERIFIED_WITH_WARNINGS", True, "ready"),
    ("BLOCKED", True, "not_verified"),
    ("VERIFIED", False, "not_verified"),
    (None, None, "not_verified"),
])
def test_a_release_is_only_ready_when_tests_passed_and_the_guardian_verified_it(verification, tests_passed, expected):
    from backend.validation.quality_gate import apply_verification
    report = apply_verification({"release_recommendation": "ready"}, verification, tests_passed)
    assert report["release_recommendation"] == expected
    if expected == "not_verified":
        assert report["recommendation_reason"]
    assert apply_verification({"release_recommendation": "blocked"}, None, None)["release_recommendation"] == "blocked"


def test_local_project_tests_get_a_realistic_timeout(monkeypatch):
    from backend.execution.project_runner import ProjectRunner
    monkeypatch.delenv("AIFORGE_LOCAL_TEST_TIMEOUT", raising=False)
    assert ProjectRunner().limits.timeout_seconds == 120.0
    monkeypatch.setenv("AIFORGE_LOCAL_TEST_TIMEOUT", "300")
    assert ProjectRunner().limits.timeout_seconds == 300.0


def test_the_project_list_shows_only_the_users_own_projects(client, tmp_path, monkeypatch):
    import backend.routes.project_manager as project_manager
    from backend.generation.store import global_generation_store
    root = tmp_path / "generated_projects"
    for folder, owner in (("alice_app", "alice"), ("bob_app", "bob"), ("leftover", None)):
        (root / folder).mkdir(parents=True)
        if owner:
            gid = global_generation_store.create(folder, owner, f"{owner}'s app")
            global_generation_store.set_output(gid, str(root / folder), 1)
    monkeypatch.setattr(project_manager, "GENERATED_PROJECTS_DIR", root)
    names = lambda headers: sorted(p["generation_id"] for p in client.get("/api/projects", headers=headers).json()["projects"])  # noqa: E731
    assert names(ALICE) == ["alice_app"]
    assert names(BOB) == ["bob_app"]   # a folder no tracked generation produced has no owner and is not listed
