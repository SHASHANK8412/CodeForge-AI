"""
Exported project ZIPs never contain secrets, virtualenvs, caches or local data, and every export
path (pipeline packaging, download route, packaging agent) applies the same policy.
"""
import io
import zipfile

import pytest

from backend.agents.project_packaging_agent import ProjectPackagingAgent
from backend.exporter.zipper import export_exclusion_reason, global_project_zipper
from backend.services.project_exporter import ProjectExporter

PROJECT = {
    "backend/main.py": "app = None\n",
    "frontend/package.json": "{}\n",
    ".env.example": "DATABASE_URL=\n",
    ".env": "DATABASE_URL=postgres://user:hunter2@db/app\n",
    "backend/.env.production": "SECRET_KEY=abc\n",
    "certs/server.key": "-----BEGIN PRIVATE KEY-----\n",
    "deploy/.npmrc": "//registry.npmjs.org/:_authToken=npm_secret\n",
    "backend/app.db": "sqlite bytes",
    ".venv/lib/site.py": "x",
    "backend/__pycache__/main.cpython-313.pyc": "x",
    "frontend/node_modules/react/index.js": "x",
    "../outside.txt": "x",
}
EXPECTED = {"backend/main.py", "frontend/package.json", ".env.example"}


def _names(zip_bytes, root):
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        return {n[len(root) + 1:] if root else n for n in zf.namelist()}


@pytest.mark.parametrize("path,excluded", [
    ("backend/main.py", False), (".env.example", False), (".env.sample", False),
    (".env", True), ("backend/.env.local", True), ("keys/id_rsa", True), ("a/b.pem", True),
    ("data/app.sqlite3", True), (".venv/x.py", True), ("node_modules/x.js", True),
    ("../x", True), ("/etc/passwd", True), ("C:/Windows/x", True),
])
def test_exclusion_policy(path, excluded):
    assert (export_exclusion_reason(path) is not None) is excluded


def test_zip_route_zipper_excludes_secrets_and_caches():
    assert _names(global_project_zipper.create_zip_bytes(PROJECT, root_folder="app"), "app") == EXPECTED


def test_pipeline_exporter_uses_the_same_policy(tmp_path):
    zip_path = ProjectExporter().export_project("Demo App", PROJECT, base_dir=str(tmp_path))
    assert _names(zip_path.read_bytes(), "Demo_App") == EXPECTED


def test_packaging_agent_uses_the_same_policy():
    assert _names(ProjectPackagingAgent().create_zip_bytes(PROJECT), "") == EXPECTED


def test_download_route_skips_secret_files_on_disk(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.routes import export as export_routes
    root = tmp_path / "generated"
    for rel, content in PROJECT.items():
        if rel.startswith(".."):
            continue
        p = root / "demo" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    monkeypatch.setattr(export_routes, "GENERATED_ROOT", root.resolve())
    monkeypatch.setattr(export_routes, "_generation_record", lambda _pid: None)

    res = TestClient(app).get("/api/export/zip/demo")
    assert res.status_code == 200, res.text
    names = _names(res.content, "demo")
    assert names == EXPECTED
    assert b"hunter2" not in res.content
