"""Scripted stand-in for Ollama, used to drive the real LangGraph pipeline end to end."""
import json

BUGGY_MAIN = '''from fastapi import FastAPI, HTTPException
app = FastAPI()
TODOS = {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/todos")
def list_todos():
    return list(TODOS.values())

@app.post("/todos", status_code=201)
def create_todo(todo: dict):
    tid = len(TODOS) + 1
    TODOS[tid] = {"id": tid, **todo}
    return TODOS[tid]

@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    return TODOS.get(todo_id, {})          # BUG: should 404

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, todo: dict):
    TODOS[todo_id] = {"id": todo_id, **todo}
    return TODOS[todo_id]

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    TODOS.pop(todo_id, None)
    return {"deleted": todo_id}
'''
FIXED_MAIN = BUGGY_MAIN.replace(
    "    return TODOS.get(todo_id, {})          # BUG: should 404",
    "    if todo_id not in TODOS:\n        raise HTTPException(status_code=404)\n    return TODOS[todo_id]")

# A "fix" that leaves the bug in place and deletes /health: a regression the
# loop must detect and roll back.
REGRESSING_MAIN = BUGGY_MAIN.replace(
    '@app.get("/health")\ndef health():\n    return {"status": "ok"}\n', "")
# A "fix" that changes nothing observable: no effect, also rolled back.
NO_EFFECT_MAIN = BUGGY_MAIN.replace("app = FastAPI()", "app = FastAPI(title='todo')")

TESTS = '''from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").status_code == 200

def test_create_and_get():
    created = client.post("/todos", json={"title": "write eval"}).json()
    assert client.get(f"/todos/{created['id']}").json()["title"] == "write eval"

def test_missing_todo_is_404():
    assert client.get("/todos/9999").status_code == 404
'''

def _fence(src: str) -> str:
    return "```python\n# filepath: backend/main.py\n" + src + "```\n"


def reply_for(system: str, user: str, repair_queue=None) -> str:
    s = system
    if "Chief Software Architect of AIForge — a Senior" in s:
        return json.dumps({"project_name": "todo-basic", "domain": "productivity",
                           "executive_summary": "Todo API", "functional_requirements": ["CRUD todos"],
                           "non_functional_requirements": [], "user_stories": [], "assumptions": [],
                           "constraints": [], "tech_stack": {"frontend": "React", "backend": "FastAPI",
                           "database": "SQLite", "auth": "none", "infra": "Docker"}})
    if "continuing the technical design" in s:
        return json.dumps({"components": ["TodoList"], "routes": ["GET /todos"], "models": ["Todo"],
                           "dependencies": ["fastapi"], "folder_structure": {"backend": ["main.py"]}})
    if "React Frontend Engineer" in s:
        return "```jsx\n// filepath: frontend/src/App.jsx\nexport default function App() { return <h1>Todos</h1>; }\n```"
    if "FastAPI Backend Engineer" in s:
        return "Here is the backend.\n\n```python\n# filepath: backend/main.py\n" + BUGGY_MAIN + "```\n"
    if "Database Engineer" in s:
        return "```sql\nCREATE TABLE todos (id INTEGER PRIMARY KEY, title TEXT);\n```"
    if "Software Testing Engineer" in s:
        return "## Integration Tests\n```python\n# filepath: tests/test_todos.py\n" + TESTS + "```\n"
    if "code review" in s.lower():
        return json.dumps({"status": "FAIL", "score": 70, "summary": "missing 404",
                           "issues": [{"file": "backend/main.py", "severity": "major",
                                       "problem": "GET /todos/{id} returns 200 with {} for unknown ids instead of 404",
                                       "fix": "raise HTTPException(404)"}]})
    if "fixing a FastAPI project" in s:
        if repair_queue:
            return _fence(repair_queue.pop(0))
        return _fence(FIXED_MAIN)
    if "Technical Writer" in s:
        return "# todo-basic\n\nA todo API."
    return "ok"


class FakeResponse(dict):
    pass


def install(monkey_target):
    calls = []

    async def fake_chat_async(model, messages, stream=False, options=None):
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        user = messages[-1]["content"]
        text = reply_for(system, user)
        calls.append(system[:40])
        return FakeResponse(message={"content": text}, prompt_eval_count=len(user) // 4 + 7,
                            eval_count=len(text) // 4 + 3)

    monkey_target._chat_completion_async = fake_chat_async
    return calls


def install_on(monkeypatch, llm_module, repair_sequence=None):
    """pytest variant: patches via monkeypatch and records (system, user) per call.

    ``repair_sequence`` lists the backend sources the repair step returns, in
    order (then FIXED_MAIN). Default: fix on the first try.
    """
    calls = []
    queue = list(repair_sequence or [])

    async def fake_chat_async(model, messages, stream=False, options=None):
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        user = messages[-1]["content"]
        text = reply_for(system, user, queue)
        calls.append((system, user))
        return FakeResponse(message={"content": text}, prompt_eval_count=len(user) // 4 + 7,
                            eval_count=len(text) // 4 + 3)

    monkeypatch.setattr(llm_module, "_chat_completion_async", fake_chat_async)
    return calls
