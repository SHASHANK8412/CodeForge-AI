"""
Editing an existing project: only the needed files change, tests run before and after, and a
change that makes things worse is rolled back. The model is replaced by fixed replies.
"""
from pathlib import Path

from fastapi.testclient import TestClient

from backend.generation.project_editor import edit_project, relevant_files

MAIN = '''from fastapi import FastAPI

app = FastAPI()
_items = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/items")
def create_item(name: str):
    _items[len(_items) + 1] = name
    return {"id": len(_items), "name": name}
'''

TESTS = '''from fastapi.testclient import TestClient
from backend.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}
'''

OTHER = "# unrelated module\nVALUE = 1\n"


def _project(root: Path) -> Path:
    for rel, content in {"backend/__init__.py": "", "backend/main.py": MAIN, "backend/other.py": OTHER,
                         "tests/test_api.py": TESTS}.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


GOOD_EDIT = "### backend/main.py\n```python\n" + MAIN + '''

@app.get("/items/count")
def count_items():
    return {"count": len(_items)}
```

### tests/test_count.py
```python
from fastapi.testclient import TestClient
from backend.main import app


def test_count_starts_at_zero():
    assert TestClient(app).get("/items/count").json() == {"count": 0}
```
'''


def test_edit_changes_only_the_needed_files_and_runs_tests(tmp_path):
    project = _project(tmp_path / "shop")
    seen = {}

    def model(system, prompt):
        seen["prompt"] = prompt
        return GOOD_EDIT

    result = edit_project(project, "Add an endpoint that returns the number of items", "shop", generate=model)
    assert result.status == "applied", result.reason
    assert sorted(result.changed_files) == ["backend/main.py", "tests/test_count.py"]
    assert "backend/main.py" in result.context_files and "def create_item" in seen["prompt"]
    assert (project / "backend" / "other.py").read_text(encoding="utf-8") == OTHER, "unrelated file untouched"
    assert result.before["tests_status"] == "PASS" and result.after["tests_status"] == "PASS"
    assert result.after["tests_passed"] == result.before["tests_passed"] + 1


def test_edit_that_breaks_the_app_is_rolled_back(tmp_path):
    project = _project(tmp_path / "shop")
    broken = "### backend/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\nvalue = undefined_name\n```"
    result = edit_project(project, "Refactor the main module", "shop", generate=lambda s, p: broken)
    assert result.status == "rolled_back" and "quality-gate" in result.reason
    assert (project / "backend" / "main.py").read_text(encoding="utf-8") == MAIN


def test_unsafe_paths_are_rejected(tmp_path):
    project = _project(tmp_path / "shop")
    reply = ("### ../outside.py\n```python\nx = 1\n```\n### config/.env.local\n```\nSECRET=1\n```\n")
    result = edit_project(project, "Add configuration", "shop", generate=lambda s, p: reply)
    assert result.status == "no_changes" and set(result.rejected_paths) == {"../outside.py", "config/.env.local"}
    assert not (project / "config" / ".env.local").exists()
    assert not (tmp_path / "outside.py").exists() and not (project / ".env").exists()


def test_relevant_files_prefers_files_matching_the_request(tmp_path):
    project = _project(tmp_path / "shop")
    files = {p.relative_to(project).as_posix(): p.read_text(encoding="utf-8") for p in project.rglob("*.py")}
    assert relevant_files(project, "change create_item to validate the name", files)[0] == "backend/main.py"


def test_edit_route(tmp_path, monkeypatch):
    from backend.main import app
    from backend.routes import export as export_routes
    root = tmp_path / "generated"
    _project(root / "shop")
    monkeypatch.setattr(export_routes, "GENERATED_ROOT", root.resolve())
    monkeypatch.setattr(export_routes, "_generation_record", lambda _pid: None)
    monkeypatch.setattr("backend.services.llm.generate_text", lambda *a, **k: GOOD_EDIT)
    client = TestClient(app)
    res = client.post("/api/projects/shop/edit", json={"request": "Add an item count endpoint"})
    assert res.status_code == 200 and res.json()["status"] == "applied"
    assert client.post("/api/projects/missing/edit", json={"request": "Add an item count"}).status_code == 404
