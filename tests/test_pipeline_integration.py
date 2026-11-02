"""
End-to-end run of the real generation graph (backend/graph/parallel_workflow.py):

    planner -> architect -> [architecture approval] -> frontend | backend | database -> assembly
    -> reviewer -> documentation -> quality gate -> dependencies -> security -> performance
    -> execution check -> tests -> [final approval] -> packaging (ZIP) -> deployment -> GitHub
    -> CI check -> live deploy -> health check

Only the language-model calls are replaced, by replies shaped like real model output
(Markdown architecture, fenced multi-file code). Everything else runs: extraction, assembly to
disk, the import/lint gate, the generated tests (pytest), the approval checkpoints with the
GenerationManager's resume mechanics, ZIP export and the deploy steps. Docker previews are off
(conftest), so the deploy steps must report "not deployed" instead of claiming a running app.
"""
import asyncio
import json
import zipfile
from types import SimpleNamespace

import pytest
from langgraph.checkpoint.memory import MemorySaver

from backend.graph import parallel_workflow as wf

PLAN = {
    "project_name": "Notes Board",
    "executive_summary": "Users write short notes and read them back.",
    "functional_requirements": ["Create a note", "Read a note by id", "List notes"],
    "features": ["Notes CRUD"],
    "frontend": "React", "backend": "FastAPI", "database": "SQLite",
}

ARCHITECTURE = """## 10. High-Level Architecture
React SPA -> FastAPI -> SQLite.

## 11. Database Schema
- **notes**: id (int, PK), text (str)

## 12. API Specifications
- `GET /health` - liveness
- `POST /notes` - create a note
- `GET /notes/{note_id}` - read a note
- `GET /notes` - list notes

## 13. Folder Structure
backend/main.py, frontend/src/App.jsx, frontend/src/components/NoteList.jsx

## 17. Risk Analysis
- In-memory storage loses notes on restart — Medium — move to SQLite in M2
"""

BACKEND = '''Here is the backend.

### backend/__init__.py
```python
```

### backend/main.py
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Notes Board")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
_notes: dict = {}


class NoteIn(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/notes", status_code=201)
def create_note(note: NoteIn):
    note_id = len(_notes) + 1
    _notes[note_id] = note.text
    return {"id": note_id, "text": note.text}


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"id": note_id, "text": _notes[note_id]}


@app.get("/notes")
def list_notes():
    return [{"id": i, "text": t} for i, t in _notes.items()]
```

### requirements.txt
```text
fastapi
uvicorn
httpx
```

### backend/.env
```text
SECRET_KEY=local-dev-only-value
```
'''

FRONTEND = '''### frontend/package.json
```json
{"name": "notes-board", "private": true, "scripts": {"dev": "vite", "build": "vite build"},
 "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"}, "devDependencies": {"vite": "^5.4.0"}}
```

### frontend/src/App.jsx
```jsx
import React from "react";

export default function App() {
  return <h1>Notes Board</h1>;
}
```
'''

DATABASE = '''### database/schema.sql
```sql
CREATE TABLE notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL);
```
'''

TESTS = '''## API Tests
```python
# filepath: tests/test_api.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_read_note():
    created = client.post("/notes", json={"text": "hello"})
    assert created.status_code == 201
    note_id = created.json()["id"]
    assert client.get(f"/notes/{note_id}").json() == {"id": note_id, "text": "hello"}


def test_missing_note_is_404():
    assert client.get("/notes/9999").status_code == 404
```
'''


def _reply(text):
    async def run_async(*_args, **_kwargs):
        return text
    return run_async


class _Memory:
    """In-memory stand-in for the memory manager, so the run does not touch real project memory."""

    def __init__(self):
        self.outputs = {}

    def save_agent_output(self, session_id, agent, output):
        self.outputs[(session_id, agent)] = output

    def get_agent_output(self, session_id, agent):
        return self.outputs.get((session_id, agent))

    def save(self, *args, **kwargs):
        return None

    def save_decision(self, *args, **kwargs):
        return None


@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)                                # generated_projects/ goes under tmp_path
    monkeypatch.delenv("AIFORGE_AUTO_PUBLISH_GITHUB", raising=False)
    prompts = {}

    def recording(name, text):
        async def run_async(prompt="", *_a, **_k):
            prompts[name] = prompt
            return text
        return run_async

    monkeypatch.setattr(wf.planner, "run_async", _reply("```json\n" + json.dumps(PLAN) + "\n```"))
    monkeypatch.setattr(wf.architect, "run_async", recording("architect", ARCHITECTURE))
    monkeypatch.setattr(wf.backend_agent, "run_async", recording("backend", BACKEND))
    monkeypatch.setattr(wf.frontend_agent, "run_async", recording("frontend", FRONTEND))
    monkeypatch.setattr(wf.database_agent, "run_async", recording("database", DATABASE))
    monkeypatch.setattr(wf.reviewer_agent, "run_async", _reply("No [Critical] issues. Looks consistent."))
    monkeypatch.setattr(wf.testing_agent, "run_async", recording("testing", TESTS))
    monkeypatch.setattr(wf.documentation_agent, "run_async", _reply("# Notes Board\n\nRun `uvicorn backend.main:app`.\n"))
    monkeypatch.setattr(wf.global_cache_service, "get", lambda *a, **k: None)
    monkeypatch.setattr(wf.global_cache_service, "set", lambda *a, **k: None)
    monkeypatch.setattr(wf, "memory_manager", _Memory())

    def no_model(*_a, **_k):
        raise RuntimeError("no model in tests")
    # The repair loop's diagnosis uses its deterministic fallback, not a live Ollama call.
    monkeypatch.setattr(wf.global_diagnostic_agent, "generate", no_model)
    # Dependencies: the generated tests use fastapi/httpx, already in AIForge's interpreter, so the
    # per-project venv install (network) is skipped; pip-audit (network) likewise.
    monkeypatch.setattr("backend.execution.project_env.ensure_project_env", lambda *_a, **_k: {"ok": True})
    monkeypatch.setattr("backend.validation.quality_gate._dependency_findings", lambda *_a, **_k: [])
    graph = wf.compile_parallel_graph(MemorySaver())
    return SimpleNamespace(graph=graph, prompts=prompts, root=tmp_path)


def _resume(graph, config, payload):
    """What GenerationManager.approve_generation / reject_generation do."""
    snapshot = graph.get_state(config)
    graph.update_state(config, payload, as_node=snapshot.next[0])
    return asyncio.run(graph.ainvoke(None, config=config))


def test_prompt_to_zip_through_both_approvals(pipeline):
    graph = pipeline.graph
    config = {"configurable": {"thread_id": "gen_integration_1"}}
    asyncio.run(graph.ainvoke({
        "prompt": "Build a notes board", "user_prompt": "Build a notes board", "project_id": "notes_board",
        "generation_id": "gen_integration_1", "session_id": "gen_integration_1",
        "files": {}, "fixes": [], "retry_count": 0, "max_iterations": 3,
    }, config=config))

    # --- Checkpoint 1: the approval node ran and shows the real architecture ---------------
    snapshot = graph.get_state(config)
    assert snapshot.next == ("human_approval",)
    request = snapshot.values["approval_request"]
    assert request["routes"] == ["GET /health", "POST /notes", "GET /notes/{note_id}", "GET /notes"]
    assert request["models"] == ["notes"]
    assert request["tech_stack"] == {"frontend": "React", "backend": "FastAPI", "database": "SQLite"}
    assert request["risks"] and "In-memory storage" in request["risks"][0]
    assert "Session" not in json.dumps(request) and "LoginForm" not in json.dumps(request)
    assert snapshot.values["session_id"] == "gen_integration_1", "declared state keys survive the graph"
    # The architect was asked for concrete sections; no code is generated before approval.
    assert "METHOD /path" in pipeline.prompts["architect"] and "Notes Board" in pipeline.prompts["architect"]
    assert not {"backend", "frontend", "database", "testing"} & set(pipeline.prompts)

    # --- Approve: code generation, assembly, gates and tests --------------------------------
    final = _resume(graph, config, {"approval_status": "approved", "approval_required": False,
                                    "status": "RUNNING", "current_step": "dispatch_parallel"})
    assert "POST /notes" in pipeline.prompts["backend"] and "Create a note" in pipeline.prompts["backend"]
    assert "backend/main.py" in pipeline.prompts["testing"] and "def get_note" in pipeline.prompts["testing"]

    snapshot = graph.get_state(config)
    assert snapshot.next == ("final_approval",)
    values = snapshot.values
    project = pipeline.root / "generated_projects" / "Notes_Board"
    assert values["project_path"] and (project / "backend" / "main.py").is_file()
    assert {"backend/main.py", "frontend/src/App.jsx", "database/schema.sql", "tests/test_api.py"} <= set(values["files"])
    assert values["quality_gate"]["passed"] is True, values["quality_gate"]["errors"]
    tests = values["test_results"]
    assert tests["success"] is True and tests["passed"] == 3 and tests["total"] == 3, tests
    request = values["approval_request"]
    assert request["stage"] == "final" and values["human_intervention_required"] is False
    assert request["tests_passed"] == 3
    report = request["quality_report"]
    assert report["checks"]["code_quality_gate"] == "passed"
    assert report["release_recommendation"] in ("ready", "review_required"), report

    # --- Approve: packaging, deploy steps ----------------------------------------------------
    final = _resume(graph, config, {"approval_status": "approved", "approval_required": False,
                                    "status": "RUNNING", "current_step": "packaging"})
    assert graph.get_state(config).next == ()
    zip_path = final["zip_path"]
    with zipfile.ZipFile(zip_path) as zf:
        names = {n.split("/", 1)[1] for n in zf.namelist()}
    assert {"backend/main.py", "tests/test_api.py", "frontend/package.json", "database/schema.sql"} <= names
    assert "backend/.env" not in names, "secrets never leave in an export"

    assert final["github"]["status"] == "NOT_PUBLISHED"
    assert final["deployment_status"] == "FAILED" and final["health_status"] == "NOT_DEPLOYED"
    events = " ".join(final["stream_events"])
    assert "Services running" not in events and "HEALTHY" not in events
    # The health check did not "repair" or roll back a project that was never deployed.
    assert (project / "backend" / "main.py").read_text(encoding="utf-8").count("def create_note") == 1


def test_failing_tests_escalate_after_bounded_repairs(pipeline, monkeypatch):
    """Tests that keep failing go through debug -> patch at most max_iterations times, then the
    final checkpoint is a human escalation (it used to be shown as an ordinary final review)."""
    broken_tests = TESTS.replace('{"status": "ok"}', '{"status": "broken"}')
    monkeypatch.setattr(wf.testing_agent, "run_async", _reply(broken_tests))
    graph = pipeline.graph
    config = {"configurable": {"thread_id": "gen_integration_2"}}
    asyncio.run(graph.ainvoke({"prompt": "Build a notes board", "user_prompt": "Build a notes board",
                               "project_id": "notes_board_2", "generation_id": "gen_integration_2",
                               "files": {}, "fixes": [], "retry_count": 0, "max_iterations": 2}, config=config))
    _resume(graph, config, {"approval_status": "approved", "current_step": "dispatch_parallel"})

    values = graph.get_state(config).values
    assert graph.get_state(config).next == ("final_approval",)
    assert values["test_results"]["success"] is False
    assert values["human_intervention_required"] is True
    assert values["approval_request"]["stage"] == "debug_escalation"
    assert values["repair_status"] in ("STOPPED_MAX_ATTEMPTS", "STOPPED_REPEATED_FAILURE")
    assert 1 <= len(values.get("fix_history") or []) <= 2


# --- Model outage: a failed or timed-out model call fails its step; nothing stands in for it ----------------------

# What the removed llm.py fallback used to return in place of model output.
CANNED = ("AIForge App", "assert 1 + 1 == 2", "zero critical flaws", "CREATE TABLE IF NOT EXISTS users",
          "Task completed successfully", "AIForge Software Application")


def _model_down(monkeypatch, timeout=False):
    """The model transport fails: every call raises (Ollama not running) or never answers (timeout)."""
    import backend.services.llm as llm
    calls = []

    async def down(model, messages, stream=False, options=None):
        calls.append(model)
        if timeout:
            await asyncio.sleep(5)
        raise ConnectionError("connection refused: Ollama is not running")

    def down_sync(model, messages, stream=False, options=None):
        calls.append(model)
        raise ConnectionError("connection refused: Ollama is not running")

    monkeypatch.setattr(llm, "_chat_completion_async", down)
    monkeypatch.setattr(llm, "_chat_completion", down_sync)
    monkeypatch.setattr(llm, "LLM_TIMEOUT_SECONDS", 0.05)
    llm.llm_cache.clear()
    return calls


def _real(monkeypatch, *agents):
    """Undo the fixture's scripted reply: these agents call the (failing) model for real."""
    for agent in agents:
        monkeypatch.setattr(agent, "run_async", type(agent).run_async.__get__(agent))


def _recorded_metrics(monkeypatch):
    seen = []
    monkeypatch.setattr(wf, "_record_metrics", lambda state, increment=None, **values: seen.append(values))
    return seen


def _no_canned_output(root):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix not in (".db", ".pkl", ".zip"):
            text = path.read_text(encoding="utf-8", errors="replace")
            assert not [c for c in CANNED if c in text], f"canned model text written to {path}"


def _assert_failed_run(values, agents):
    assert values["status"] == "FAILED" and values["execution_status"] == "FAILED"
    assert values["current_step"] == "generation_failed"
    assert {f["agent"] for f in values["agent_failures"]} == set(agents)
    assert all("ConnectionError" in f["error"] or "did not finish" in f["error"] for f in values["agent_failures"])
    assert values["approval_required"] is False and values.get("approval_stage") != "final"
    assert "quality_report" not in (values.get("approval_request") or {})
    assert values.get("human_intervention_required") is not True
    events = " ".join(values["stream_events"])
    assert "Generation failed: the language model produced no output" in events
    assert not [c for c in CANNED if c in json.dumps(values, default=str)], "no canned text anywhere in the state"


def test_planner_outage_stops_the_run_before_any_approval(pipeline, monkeypatch):
    calls = _model_down(monkeypatch)
    _real(monkeypatch, wf.planner)
    metrics = _recorded_metrics(monkeypatch)
    graph = pipeline.graph
    config = {"configurable": {"thread_id": "gen_outage_planner"}}
    asyncio.run(graph.ainvoke({"prompt": "Build a notes board", "user_prompt": "Build a notes board",
                               "project_id": "notes_outage", "generation_id": "gen_outage_planner",
                               "files": {}, "fixes": [], "retry_count": 0}, config=config))

    snapshot = graph.get_state(config)
    assert snapshot.next == (), "the run ends; it does not pause for an architecture approval"
    values = snapshot.values
    assert calls, "the model was called (and failed)"
    _assert_failed_run(values, ["planner"])
    assert "plan" not in values and "architecture" not in values
    assert "architect" not in pipeline.prompts, "nothing after the planner ran"
    assert not (pipeline.root / "generated_projects").exists()
    assert not [m for m in metrics if "release_recommendation" in m]
    _no_canned_output(pipeline.root)


def test_code_agents_timing_out_write_no_project_and_reach_no_release(pipeline, monkeypatch):
    """Every code agent times out (the audit's run where all agents timed out still reached approval as "ready")."""
    _model_down(monkeypatch, timeout=True)
    _real(monkeypatch, wf.frontend_agent, wf.backend_agent, wf.database_agent)
    metrics = _recorded_metrics(monkeypatch)
    graph = pipeline.graph
    config = {"configurable": {"thread_id": "gen_outage_code"}}
    asyncio.run(graph.ainvoke({"prompt": "Build a notes board", "user_prompt": "Build a notes board",
                               "project_id": "notes_outage_2", "generation_id": "gen_outage_code",
                               "files": {}, "fixes": [], "retry_count": 0}, config=config))
    assert graph.get_state(config).next == ("human_approval",)
    _resume(graph, config, {"approval_status": "approved", "approval_required": False,
                            "status": "RUNNING", "current_step": "dispatch_parallel"})

    snapshot = graph.get_state(config)
    assert snapshot.next == (), "no final approval: there is nothing to review"
    values = snapshot.values
    _assert_failed_run(values, ["frontend", "backend", "database"])
    assert all("did not finish" in f["error"] for f in values["agent_failures"])
    assert not {"frontend", "backend", "database", "review", "test_results", "project_path"} & set(values)
    assert not (pipeline.root / "generated_projects").exists(), "nothing assembled or written"
    assert "testing" not in pipeline.prompts
    assert not [m for m in metrics if "release_recommendation" in m]
    _no_canned_output(pipeline.root)


def test_reviewer_outage_does_not_mark_the_project_reviewed(pipeline, monkeypatch):
    _model_down(monkeypatch)
    _real(monkeypatch, wf.reviewer_agent)
    metrics = _recorded_metrics(monkeypatch)
    graph = pipeline.graph
    config = {"configurable": {"thread_id": "gen_outage_review"}}
    asyncio.run(graph.ainvoke({"prompt": "Build a notes board", "user_prompt": "Build a notes board",
                               "project_id": "notes_outage_3", "generation_id": "gen_outage_review",
                               "files": {}, "fixes": [], "retry_count": 0}, config=config))
    _resume(graph, config, {"approval_status": "approved", "approval_required": False,
                            "status": "RUNNING", "current_step": "dispatch_parallel"})

    snapshot = graph.get_state(config)
    assert snapshot.next == ()
    values = snapshot.values
    _assert_failed_run(values, ["reviewer"])
    assert "review" not in values, "no review score or text"
    assert "test_results" not in values and "testing" not in pipeline.prompts
    # The code agents' (scripted) output was assembled before the review; nothing canned was added to it.
    assert (pipeline.root / "generated_projects" / "Notes_Board" / "backend" / "main.py").is_file()
    assert not [m for m in metrics if "release_recommendation" in m]
    _no_canned_output(pipeline.root)


def test_generation_manager_records_an_outage_as_failed(pipeline, monkeypatch, tmp_path):
    from backend.generation import manager as mgr_mod
    from backend.generation.store import GenerationStore

    _model_down(monkeypatch)
    _real(monkeypatch, wf.planner)
    store = GenerationStore(store_path=tmp_path / "generations.json")
    monkeypatch.setattr(mgr_mod, "_store", store)
    monkeypatch.setattr(mgr_mod, "parallel_graph", pipeline.graph)
    monkeypatch.setattr(mgr_mod.global_version_manager, "get_latest_version", lambda *_a, **_k: None)
    gen_id = store.create("notes_outage_4", "tester", "Build a notes board", gen_id="gen_outage_manager")

    asyncio.run(mgr_mod.GenerationManager()._run_pipeline(gen_id, store.get(gen_id)))

    rec = store.get(gen_id)
    assert rec["status"] == "failed", rec["status"]
    assert "language model produced no output for planner" in rec["error"]
    kinds = [e["type"] for e in rec["events"]]
    assert "generation_failed" in kinds and "generation_completed" not in kinds
