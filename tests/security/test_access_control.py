"""
Access control on the real app (backend.main.app) with authentication enforced the way production runs it.

Everything on disk is a scratch tree: users, generations and project folders are redirected to tmp_path, and the
real repository files touched by an attack (backend/main.py) are hashed before and after.
"""

import hashlib
import zipfile
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import backend.auth.service as auth_service
import backend.generators.project_generator as project_generator
import backend.routes.export as export
import backend.routes.workspace_ide_routes as ide
from backend.auth.gate import is_public
from backend.auth.security import create_access_token, hash_password
from backend.generation.store import global_generation_store
from backend.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]


def _token(uid, **kw):
    return {"Authorization": f"Bearer {create_access_token({'sub': uid}, **kw)}"}


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.fixture
def world(tmp_path, monkeypatch):
    """Two users with one finished generation each, in a scratch generated_projects/ folder."""
    monkeypatch.delenv("AIFORGE_AUTH_MODE", raising=False)  # tests/conftest.py turns local-dev on for other suites
    monkeypatch.delenv("AIFORGE_REQUIRE_AUTH", raising=False)
    monkeypatch.delenv("AIFORGE_ENV", raising=False)

    users = {uid: {"id": uid, "name": uid, "email": f"{uid}@example.test", "password_hash": hash_password("pw-" + uid),
                   "created_at": "2026-01-01"} for uid in ("alice", "bob")}
    users[auth_service.DEFAULT_USER_ID] = dict(auth_service.DEFAULT_USER)
    monkeypatch.setattr(auth_service, "USERS_DB", users)
    monkeypatch.setattr(auth_service, "USERS_FILE", tmp_path / "users.json")

    gen_root = tmp_path / "generated_projects"
    records = {}
    for gid, owner, folder in (("gen_alice", "alice", "alice_shop"), ("gen_bob", "bob", "bob_blog")):
        proj = gen_root / folder
        (proj / "backend").mkdir(parents=True)
        (proj / "backend" / "main.py").write_text(f"# {owner}'s app\n", encoding="utf-8")
        (proj / ".env").write_text(f"SECRET={owner}-secret\n", encoding="utf-8")
        records[gid] = {"id": gid, "generation_id": gid, "user_id": owner, "status": "completed",
                        "project_path": str(proj), "project_id": folder}
    monkeypatch.setattr(global_generation_store, "get", lambda gid, default=None: records.get(gid, default))
    monkeypatch.setattr(global_generation_store, "list_all", lambda: list(records.values()))
    monkeypatch.setattr(export, "GENERATED_ROOT", gen_root.resolve())
    monkeypatch.setattr(ide, "GENERATED_PROJECTS_DIR", gen_root)
    monkeypatch.setattr(project_generator, "GENERATED_PROJECTS_DIR", gen_root)
    return tmp_path


@pytest.fixture
def client(world):
    return TestClient(app)


# --- Authentication --------------------------------------------------------------------------------------------

def _all_routes():
    from backend.auth.gate import AuthGateMiddleware  # noqa: F401  (the gate is what is under test)

    def visit(routes, prefix=""):
        for r in routes:
            if type(r).__name__ == "_IncludedRouter":
                yield from visit(r.original_router.routes, prefix + (r.include_context.prefix or ""))
            elif isinstance(r, APIRoute):
                for m in r.methods:
                    yield m, prefix + r.path
    return sorted(set(visit(app.routes)))


def test_every_non_public_route_rejects_anonymous_requests(client):
    routes = [(m, p) for m, p in _all_routes() if not is_public(m, p)]
    assert len(routes) > 800, "the inventory should cover the whole app"
    leaks = []
    for method, path in routes:
        url = path.replace("{", "").replace("}", "")  # every path parameter gets its own name as a value
        resp = client.request(method, url, json={})
        if resp.status_code != 401:
            leaks.append((method, path, resp.status_code))
    assert leaks == []


def test_public_routes_are_only_liveness_and_sign_in(client):
    public = sorted(p for m, p in _all_routes() if is_public(m, p))
    assert set(public) <= {"/", "/health", "/api/health", "/api/auth/login", "/api/auth/register", "/api/auth/logout",
                           "/api/auth/forgot-password", "/api/auth/reset-password"}
    assert client.get("/api/health").status_code == 200


@pytest.mark.parametrize("headers", [
    {"Authorization": "Bearer not-a-jwt"},
    {"Authorization": "Bearer a.b.c"},
    {"Cookie": "aiforge_token=forged"},
    "expired",
    "unknown-user",
    "tampered",
])
def test_invalid_credentials_get_401(client, headers):
    if headers == "expired":
        headers = _token("alice", expires_delta_seconds=-60)
    elif headers == "unknown-user":
        headers = _token("mallory")
    elif headers == "tampered":
        token = create_access_token({"sub": "bob"})
        head, payload, sig = token.split(".")
        headers = {"Authorization": f"Bearer {head}.{create_access_token({'sub': 'alice'}).split('.')[1]}.{sig}"}
    assert client.get("/api/generations", headers=headers).status_code == 401


def test_default_user_cannot_sign_in_with_the_old_published_password(client):
    resp = client.post("/api/auth/login", json={"email": "user@example.com", "password": "password123"})
    assert resp.status_code == 401


def test_stored_default_user_with_the_old_password_is_switched_off(tmp_path, monkeypatch):
    import json
    users_file = tmp_path / "users.json"
    old = dict(auth_service.DEFAULT_USER, password_hash=hash_password("password123"))
    users_file.write_text(json.dumps([old]), encoding="utf-8")
    monkeypatch.setattr(auth_service, "USERS_FILE", users_file)
    monkeypatch.setattr(auth_service, "USERS_DB", {})
    auth_service._load_users()
    assert auth_service.authenticate_user("user@example.com", "password123") is None
    assert "password123" not in users_file.read_text(encoding="utf-8")


def test_local_dev_mode_needs_explicit_opt_in_and_is_refused_in_production(client, monkeypatch):
    assert client.get("/api/generations").status_code == 401  # nothing set: auth required
    monkeypatch.setenv("AIFORGE_AUTH_MODE", "local-dev")
    assert client.get("/api/generations").status_code == 200
    monkeypatch.setenv("AIFORGE_ENV", "production")
    assert client.get("/api/generations").status_code == 401
    monkeypatch.delenv("AIFORGE_ENV")
    monkeypatch.setenv("AIFORGE_REQUIRE_AUTH", "1")
    assert client.get("/api/generations").status_code == 401


def test_local_dev_mode_only_trusts_this_machine(world, monkeypatch):
    monkeypatch.setenv("AIFORGE_AUTH_MODE", "local-dev")
    remote = TestClient(app, client=("203.0.113.7", 40000))
    assert remote.get("/api/generations").status_code == 401
    assert TestClient(app, client=("127.0.0.1", 40000)).get("/api/generations").status_code == 200
    # An invalid token is never downgraded to the default user, even locally.
    assert TestClient(app, client=("127.0.0.1", 40000)).get(
        "/api/generations", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_docs_are_not_public_in_production(client, monkeypatch):
    assert client.get("/openapi.json").status_code == 200
    monkeypatch.setenv("AIFORGE_ENV", "production")
    assert client.get("/openapi.json").status_code == 401


# --- Ownership -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("method,url,body", [
    ("GET", "/api/generations/gen_alice", None),
    ("PUT", "/api/project/gen_alice/file", {"path": "backend/main.py", "content": "pwned = 1\n"}),
    ("GET", "/api/project/gen_alice/files", None),
    ("GET", "/api/projects/gen_alice/deployment", None),
    ("POST", "/api/projects/gen_alice/deployment/start", {}),
    ("GET", "/api/export/zip/gen_alice", None),
    ("GET", "/project/alice_shop/files", None),                    # folder name instead of generation id
    ("GET", "/project/alice_shop/file?path=backend/main.py", None),
    ("GET", "/download/alice_shop", None),
    ("GET", "/api/github/git-status?project_id=gen_alice", None),  # query string
    ("POST", "/api/github/git-init", {"project_id": "gen_alice"}),  # JSON body
    ("POST", "/api/github/push", {"project_id": "alice_shop", "remote_url": "https://github.com/bob/x"}),
    ("POST", "/api/project/validate", {"project_id": "gen_alice"}),
    ("POST", "/api/github/publish", {"project_id": "gen_alice", "repo_name": "stolen"}),  # server token + alice's files
    ("POST", "/api/github/sync", {"project_id": "alice_shop", "commit_message": "x"}),
    ("POST", "/api/ai-core/tools/execute", {"tool_name": "file_reader", "arguments": {"path": "backend/main.py"},
                                            "project_id": "gen_alice"}),
])
def test_another_users_project_is_forbidden(client, world, method, url, body):
    before = _snapshot(world)
    resp = client.request(method, url, json=body, headers=_token("bob"))
    assert resp.status_code in (403, 404), (resp.status_code, resp.text[:200])
    assert "alice's app" not in resp.text and "alice-secret" not in resp.text
    assert _snapshot(world) == before


def test_owner_can_read_and_write_inside_their_project(client, world):
    target = world / "generated_projects" / "alice_shop" / "backend" / "main.py"
    resp = client.put("/api/project/gen_alice/file", json={"path": "backend/main.py", "content": "x = 1\n"},
                      headers=_token("alice"))
    assert resp.status_code == 200, resp.text
    assert target.read_text(encoding="utf-8") == "x = 1\n"
    assert not [p for p in target.parent.iterdir() if p.name.endswith(".tmp")], "the atomic write cleans up"
    read = client.post("/api/ai-core/tools/execute", headers=_token("alice"), json={
        "tool_name": "file_reader", "arguments": {"path": "backend/main.py"}, "project_id": "gen_alice"})
    assert read.status_code == 200 and read.json()["result"]["content"] == "x = 1\n"
    assert client.get("/project/alice_shop/file?path=backend/main.py", headers=_token("alice")).status_code == 200


def test_secret_files_stay_secret_even_for_the_owner(client):
    alice = _token("alice")
    assert client.get("/project/alice_shop/file?path=.env", headers=alice).status_code == 400
    resp = client.post("/api/ai-core/tools/execute", headers=alice, json={
        "tool_name": "file_reader", "arguments": {"path": ".env"}, "project_id": "gen_alice"})
    assert resp.status_code == 403 and "alice-secret" not in resp.text


# --- Traversal -------------------------------------------------------------------------------------------------

TRAVERSAL_IDS = ["..", "%2E%2E", "..%5C..", "%2E%2E%5Cbackend", "C:%5CWindows", "%5C%5Cserver%5Cshare", "...."]


@pytest.mark.parametrize("project_id", TRAVERSAL_IDS)
def test_project_ids_never_act_as_paths(client, world, project_id):
    alice = _token("alice")
    main_py = REPO_ROOT / "backend" / "main.py"
    before_repo, before_world = _hash(main_py), _snapshot(world)
    for method, url, body in (
        ("PUT", f"/api/project/{project_id}/file", {"path": "backend/main.py", "content": "pwned = 1\n"}),
        ("GET", f"/api/project/{project_id}/files", None),
        ("GET", f"/project/{project_id}/file?path=backend/main.py", None),
        ("GET", f"/api/projects/{project_id}/deployment", None),
        ("POST", f"/api/projects/{project_id}/deployment/start", {}),
        ("GET", f"/api/export/zip/{project_id}", None),
        ("GET", f"/api/github/git-status?project_id={project_id}", None),
    ):
        resp = client.request(method, url, json=body, headers=alice)
        assert 400 <= resp.status_code < 500, (method, url, resp.status_code)
    for body in ({"project_id": ".."}, {"project_id": "../.."}, {"project_id": "C:\\"}, {"project_id": "/etc"}):
        assert 400 <= client.post("/api/github/git-init", json=body, headers=alice).status_code < 500
        assert 400 <= client.post("/api/github/commit", json=dict(body, message="x"), headers=alice).status_code < 500
    assert _hash(main_py) == before_repo, "backend source must never be overwritten"
    assert _snapshot(world) == before_world
    assert not (world / ".gitignore").exists() and not (world / ".git").exists()


@pytest.mark.parametrize("remote", ["file:///tmp/x", "https://evil.example/a/b", "https://github.com.evil.example/a/b",
                                    "https://user:token@github.com/a/b", "ssh://github.com/a/b", "https://github.com/../b",
                                    "--upload-pack=touch /tmp/pwned"])
def test_push_only_goes_to_github_repositories(client, world, remote):
    (world / "generated_projects" / "alice_shop" / ".git").mkdir()
    resp = client.post("/api/github/push", json={"project_id": "gen_alice", "remote_url": remote}, headers=_token("alice"))
    assert resp.status_code == 400
    assert not (world / "generated_projects" / "alice_shop" / ".git" / "config").exists()


def test_publishing_with_the_server_token_needs_an_owned_project(client, world):
    # Client-supplied files without the caller's own token would go out under the server's GITHUB_TOKEN.
    resp = client.post("/api/github/publish", headers=_token("bob"),
                       json={"project_id": "not_a_project", "files": {"main.py": "print(1)\n"}})
    assert resp.status_code == 404


# --- Archives --------------------------------------------------------------------------------------------------

def test_project_zip_leaves_out_secrets_and_symlinks(tmp_path):
    from backend.services.zip_service import ZipService
    proj = tmp_path / "proj"
    (proj / "src").mkdir(parents=True)
    (proj / "src" / "app.py").write_text("print(1)\n", encoding="utf-8")
    (proj / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (proj / "keys").mkdir()
    (proj / "keys" / "server.pem").write_text("-----BEGIN-----\n", encoding="utf-8")
    outside = tmp_path / "host_secret.txt"
    outside.write_text("host secret\n", encoding="utf-8")
    try:
        (proj / "src" / "link.txt").symlink_to(outside)
    except OSError:
        pass  # no symlink privilege on this machine; the secret-file checks still run
    out = ZipService().zip_project(proj, tmp_path / "out.zip")
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
        assert names == {"src/app.py"}
        assert all(b"host secret" not in zf.read(n) for n in names)


def test_export_zip_drops_zip_slip_entries():
    from backend.exporter.zipper import global_project_zipper
    import io
    data = global_project_zipper.create_zip_bytes({"ok.py": "1", "../evil.py": "2", "/abs.py": "3", "C:/x.py": "4",
                                                   "a/../../b.py": "5", ".env": "SECRET=1"})
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert names == ["project/ok.py"]
