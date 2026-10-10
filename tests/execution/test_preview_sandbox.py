"""
Generated-app previews run only in hardened containers and report only verified status.

The container checks run a real preview (Docker is required for them, since there is no host
fallback by design); the rest check the commands and the API without starting containers.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.execution import preview_manager as pm
from backend.execution.docker_test_sandbox import docker_available

needs_docker = pytest.mark.skipif(not docker_available(), reason="Docker daemon not running")

PROBE_APP = '''import os
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    try:
        open("/usr/aiforge_probe", "w").write("x")
        root_writable = True
    except OSError:
        root_writable = False
    try:
        open("/app/backend/aiforge_probe", "w").write("x")
        host_copy_writable = True
    except OSError:
        host_copy_writable = False
    open("local.db", "w").write("ok")   # apps may write next to themselves
    return {"uid": os.getuid(), "root_writable": root_writable, "host_copy_writable": host_copy_writable}
'''


def _project(tmp_path, main=PROBE_APP):
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "main.py").write_text(main, encoding="utf-8")
    (tmp_path / "backend" / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    return tmp_path


def test_run_command_is_hardened(tmp_path):
    project = _project(tmp_path)
    cmds = pm.backend_commands(project, "abc", pm.backend_entry(project), ttl=60)
    run = cmds["run"]
    for flag in ("--read-only", "--cap-drop", "no-new-privileges", "--pids-limit", "--memory", "--cpus"):
        assert flag in run
    assert run[run.index("--user") + 1] == "1000:1000"
    assert run[run.index("-p") + 1] == "127.0.0.1::8000", "published on loopback only"
    assert f"{project}:/app:ro" in run
    assert "timeout 60 python -m uvicorn main:app" in run[-1]
    assert "--privileged" not in run and "host" not in run
    install = cmds["install"]
    assert "--cap-drop" in install and "uvicorn" in install[-1]


def test_entry_detection(tmp_path):
    assert pm.backend_entry(_project(tmp_path)) == {"workdir": "backend", "module": "main:app"}
    other = tmp_path / "other"
    other.mkdir()
    (other / "main.py").write_text("def handler():\n    pass\n", encoding="utf-8")
    assert pm.backend_entry(other) is None, "no `app` defined: nothing to serve"
    (other / "frontend").mkdir()
    (other / "frontend" / "package.json").write_text(json.dumps({"scripts": {"build": "vite build"}}), encoding="utf-8")
    assert pm.frontend_entry(other) == "frontend"


def test_no_docker_means_unavailable_never_host(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_PREVIEW", "docker")
    monkeypatch.setattr(pm, "docker_available", lambda: False)
    started = []
    monkeypatch.setattr(pm, "_docker", lambda *a, **k: started.append(a))
    preview = pm.start_preview("no-docker", _project(tmp_path), wait=True)
    assert preview.status == "unavailable" and "Docker is not running" in preview.reason
    assert preview.backend.url is None and started == []


@needs_docker
def test_preview_runs_unprivileged_with_read_only_root(tmp_path, monkeypatch):
    import httpx
    monkeypatch.setenv("AIFORGE_PREVIEW", "docker")
    preview = pm.start_preview("sandbox-probe", _project(tmp_path), wait=True)
    try:
        assert preview.backend.status == "running", (preview.backend.error, preview.backend.logs[-2000:])
        body = httpx.get(preview.backend.url + "/health", timeout=5).json()
        assert body == {"uid": 1000, "root_writable": False, "host_copy_writable": False}
        assert not (tmp_path / "backend" / "local.db").exists(), "the app wrote to its tmpfs copy, not the host"
    finally:
        pm.stop_preview("sandbox-probe")


@needs_docker
def test_crashing_app_is_reported_failed_with_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_PREVIEW", "docker")
    monkeypatch.setattr(pm, "STARTUP_TIMEOUT", 15)
    broken = 'from fastapi import FastAPI\nimport does_not_exist\napp = FastAPI()\n'
    preview = pm.start_preview("sandbox-crash", _project(tmp_path, broken), wait=True)
    try:
        assert preview.status == "failed" and preview.backend.status == "failed"
        assert preview.backend.url is None
        assert "does_not_exist" in preview.backend.logs
    finally:
        pm.stop_preview("sandbox-crash")


def test_preview_routes(tmp_path, monkeypatch):
    from backend.main import app
    from backend.routes import export as export_routes
    root = tmp_path / "generated"
    (root / "demo").mkdir(parents=True)
    _project(root / "demo")
    monkeypatch.setattr(export_routes, "GENERATED_ROOT", root.resolve())
    monkeypatch.setattr(export_routes, "_generation_record", lambda _pid: None)
    client = TestClient(app)

    assert client.get("/api/projects/demo/preview/status").json()["status"] == "not_started"
    started = client.post("/api/projects/demo/preview/start").json()   # AIFORGE_PREVIEW=off in tests
    assert started["status"] == "unavailable" and started["backend"]["url"] is None
    assert client.get("/api/projects/demo/preview/logs").json() == {"backend": "", "frontend": ""}
    assert client.post("/api/projects/demo/preview/stop").json()["stopped"] is True
    assert client.post("/api/projects/missing/preview/start").status_code == 404
    assert client.post("/api/projects/..%2F..%2Fetc/preview/start").status_code == 404


def test_backend_problem_and_imported_app(tmp_path):
    (tmp_path / "backend").mkdir()
    main = tmp_path / "backend" / "main.py"
    main.write_text("```python\nfrom fastapi import FastAPI\n", encoding="utf-8")
    assert pm.backend_entry(tmp_path) is None
    assert pm.backend_problem(tmp_path).startswith("backend/main.py has a syntax error (line 1)")
    main.write_text("from backend.routes import app\n", encoding="utf-8")
    assert pm.backend_entry(tmp_path) == {"workdir": "backend", "module": "main:app"}
    main.write_text("def handler():\n    pass\n", encoding="utf-8")
    assert pm.backend_problem(tmp_path) == "backend/main.py does not define `app`"


def test_docker_calls_can_find_the_credential_helper(monkeypatch):
    from backend.execution import docker_test_sandbox as sandbox
    monkeypatch.setattr(sandbox, "docker_exe", lambda: str(Path("C:/Docker/bin/docker.exe")))
    assert sandbox.docker_env()["PATH"].split(__import__("os").pathsep)[0] == str(Path("C:/Docker/bin"))
