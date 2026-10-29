"""
Path-traversal regression tests for the file write, delete and read routes (audit S2, S6).

Each attack runs against a scratch tree: a fake repository root holding canary files, with
generated_projects/ and uploads/ inside it. Every rejected request must answer 4xx and leave
every file in that tree exactly as it was.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.routes.export as export
import backend.routes.upload as upload
import backend.routes.workspace_ide_routes as ide
from backend.ai_core.tool_registry import global_tool_registry
from backend.auth.dependencies import get_current_user
from backend.generation.store import global_generation_store
from backend.routes.ai_core_routes import router as ai_core_router


class _StubVectorDB:
    def clear(self):
        pass


class _StubRag:
    vectordb = _StubVectorDB()

    def process_and_index_document(self, path):
        return {"chunks_count": 1}


@pytest.fixture
def tree(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    gen_root = repo / "generated_projects"
    uploads = repo / "uploads"
    for folder in ("gen_mine", "gen_theirs", "gen_running"):
        (gen_root / folder / "backend").mkdir(parents=True)
        (gen_root / folder / "backend" / "app.py").write_text(f"# {folder} app\n", encoding="utf-8")
    (gen_root / "gen_mine" / ".env").write_text("PROJECT_SECRET=mine\n", encoding="utf-8")
    uploads.mkdir()
    (uploads / "notes.md").write_text("# notes\n", encoding="utf-8")
    # Canaries outside both folders, at the "repository root".
    (repo / "main.py").write_text("print('repo main')\n", encoding="utf-8")
    (repo / ".env").write_text("SECRET_KEY=canary\n", encoding="utf-8")
    (repo / "canary_delete.txt").write_text("keep me\n", encoding="utf-8")

    records = {
        gid: {"generation_id": gid, "user_id": owner, "status": state, "project_path": str(gen_root / gid)}
        for gid, owner, state in (("gen_mine", "alice", "completed"), ("gen_theirs", "bob", "completed"),
                                  ("gen_running", "alice", "running"))
    }
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(export, "GENERATED_ROOT", gen_root.resolve())
    monkeypatch.setattr(ide, "GENERATED_PROJECTS_DIR", gen_root)
    monkeypatch.setattr(upload, "UPLOADS_DIR", uploads)
    monkeypatch.setattr(upload, "global_rag_pipeline", _StubRag())
    return repo


@pytest.fixture
def client(tree):
    app = FastAPI()
    app.include_router(ide.router)
    app.include_router(upload.router)
    app.include_router(ai_core_router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "alice"}
    return TestClient(app)


def _snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


BAD_PROJECT_IDS = [
    "..", "%2E%2E", ".", "..%5C..", "%2E%2E%5C%2E%2E", "..%2F..", "C:%5CWindows", "C:", "%2Fetc", "%5C%5Cserver%5Cshare",
    "gen_mine%5C..%5C..", "missing_project",
]
BAD_FILE_PATHS = [
    "../main.py", "../../main.py", "..\\main.py", "backend/../../main.py", "backend\\..\\..\\main.py",
    "/etc/passwd", "\\main.py", "C:\\Windows\\win.ini", "C:/Windows/win.ini", "C:main.py", "\\\\server\\share\\x.py",
    "~/x.py", ".env", "backend/.env.local", "keys/server.pem", "data/app.db", "",
]


# --- PUT /api/project/{project_id}/file (S6 write) -------------------------------------------------

@pytest.mark.parametrize("project_id", BAD_PROJECT_IDS)
def test_save_rejects_unsafe_project_ids(client, tree, project_id):
    before = _snapshot(tree)
    resp = client.put(f"/api/project/{project_id}/file", json={"path": "main.py", "content": "pwned = True\n"})
    assert 400 <= resp.status_code < 500, resp.text
    assert _snapshot(tree) == before


@pytest.mark.parametrize("path", BAD_FILE_PATHS)
def test_save_rejects_paths_outside_the_project(client, tree, path):
    before = _snapshot(tree)
    resp = client.put("/api/project/gen_mine/file", json={"path": path, "content": "pwned = True\n"})
    assert 400 <= resp.status_code < 500, resp.text
    assert _snapshot(tree) == before


def test_save_rejects_another_users_project(client, tree):
    before = _snapshot(tree)
    resp = client.put("/api/project/gen_theirs/file", json={"path": "backend/app.py", "content": "pwned = True\n"})
    assert resp.status_code == 403
    assert _snapshot(tree) == before


def test_save_rejects_a_generation_that_is_still_running(client, tree):
    before = _snapshot(tree)
    resp = client.put("/api/project/gen_running/file", json={"path": "backend/app.py", "content": "x = 1\n"})
    assert resp.status_code == 409
    assert _snapshot(tree) == before


def test_save_writes_only_the_target_inside_the_users_project(client, tree):
    before = _snapshot(tree)
    resp = client.put("/api/project/gen_mine/file", json={"path": "backend/app.py", "content": "x = 1\n"})
    assert resp.status_code == 200, resp.text
    after = _snapshot(tree)
    assert after.pop("generated_projects/gen_mine/backend/app.py").replace(b"\r\n", b"\n") == b"x = 1\n"
    before.pop("generated_projects/gen_mine/backend/app.py")
    assert after == before


def test_save_does_not_follow_a_symlink_out_of_the_project(client, tree):
    link = tree / "generated_projects" / "gen_mine" / "escape"
    try:
        link.symlink_to(tree, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks need extra privileges on this machine")
    before = _snapshot(tree / "generated_projects" / "gen_theirs")
    resp = client.put("/api/project/gen_mine/file", json={"path": "escape/main.py", "content": "pwned = True\n"})
    assert 400 <= resp.status_code < 500
    assert (tree / "main.py").read_text(encoding="utf-8") == "print('repo main')\n"
    assert _snapshot(tree / "generated_projects" / "gen_theirs") == before


@pytest.mark.parametrize("project_id", ["..", "%2E%2E", "..%5C.."])
def test_workspace_reads_reject_unsafe_project_ids(client, project_id):
    # GET routes share the files map, which used to read the repository root for "..".
    assert 400 <= client.get(f"/api/project/{project_id}/files").status_code < 500
    assert 400 <= client.get(f"/api/project/{project_id}/file", params={"path": "main.py"}).status_code < 500


# --- DELETE /api/documents/{filename} (S6 delete) ------------------------------------------------

@pytest.mark.parametrize("filename", [
    "..%5Ccanary_delete.txt", "..%5C..%5Crepo%5Ccanary_delete.txt", "..%2Fcanary_delete.txt", "%2E%2E", "..",
    "C:%5Ccanary_delete.txt", "C:canary_delete.txt", "%5Ccanary_delete.txt", ".env", "notes.md%00.txt",
    "missing.md",
])
def test_delete_rejects_names_outside_uploads(client, tree, filename):
    before = _snapshot(tree)
    resp = client.delete(f"/api/documents/{filename}")
    assert 400 <= resp.status_code < 500, resp.text
    assert _snapshot(tree) == before


def test_delete_removes_only_the_named_upload(client, tree):
    before = _snapshot(tree)
    resp = client.delete("/api/documents/notes.md")
    assert resp.status_code == 200, resp.text
    before.pop("uploads/notes.md")
    assert _snapshot(tree) == before


# --- POST /api/ai-core/tools/execute file_reader / file_search (S2 read) -------------------------

def _read(client, path, project_id="gen_mine"):
    body = {"tool_name": "file_reader", "arguments": {"path": path}}
    if project_id is not None:
        body["project_id"] = project_id
    return client.post("/api/ai-core/tools/execute", json=body)


def test_file_reader_reads_inside_the_users_project(client):
    resp = _read(client, "backend/app.py")
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"]["content"] == "# gen_mine app\n"


@pytest.mark.parametrize("path", [p for p in BAD_FILE_PATHS if p])
def test_file_reader_denies_paths_outside_the_project_and_secrets(client, path):
    resp = _read(client, path)
    assert resp.status_code == 403, resp.text
    assert "canary" not in resp.text and "PROJECT_SECRET" not in resp.text


@pytest.mark.parametrize("project_id", ["..", ".", "..\\..", "C:\\", "/", "gen_mine/../..", "missing_project"])
def test_file_reader_rejects_unsafe_project_ids(client, project_id):
    resp = _read(client, ".env", project_id=project_id)
    assert 400 <= resp.status_code < 500
    assert "canary" not in resp.text


def test_file_reader_rejects_another_users_project(client):
    resp = _read(client, "backend/app.py", project_id="gen_theirs")
    assert resp.status_code == 403
    assert "gen_theirs app" not in resp.text


def test_file_reader_needs_a_project(client):
    assert _read(client, "README.md", project_id=None).status_code == 400
    # Called directly without a workspace, the registry refuses instead of reading the repository.
    res = global_tool_registry.execute_tool("file_reader", {"path": "README.md"}, user_confirmed=True)
    assert res["success"] is False and res["status"] == "DENIED"


def test_file_search_stays_inside_the_project_and_skips_secrets(client):
    resp = client.post("/api/ai-core/tools/execute", json={
        "tool_name": "file_search", "arguments": {"pattern": "="}, "project_id": "gen_mine"})
    assert resp.status_code == 200, resp.text
    assert "PROJECT_SECRET" not in resp.text and "canary" not in resp.text
    resp = client.post("/api/ai-core/tools/execute", json={
        "tool_name": "file_search", "arguments": {"pattern": "app"}, "project_id": "gen_mine"})
    assert [m["file"] for m in resp.json()["result"]["matches"]] == ["backend/app.py"]


# --- Authentication -------------------------------------------------------------------------------

def test_all_three_routes_require_auth_when_enforced(tree, monkeypatch):
    monkeypatch.setenv("AIFORGE_REQUIRE_AUTH", "1")
    app = FastAPI()
    app.include_router(ide.router)
    app.include_router(upload.router)
    app.include_router(ai_core_router)
    anon = TestClient(app)
    before = _snapshot(tree)
    assert anon.put("/api/project/gen_mine/file", json={"path": "backend/app.py", "content": "x"}).status_code == 401
    assert anon.delete("/api/documents/notes.md").status_code == 401
    assert _read(anon, "backend/app.py").status_code == 401
    assert _snapshot(tree) == before
