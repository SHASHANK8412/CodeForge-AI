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
