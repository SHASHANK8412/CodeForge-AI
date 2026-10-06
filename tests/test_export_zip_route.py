import io
import zipfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.routes.export as export


@pytest.fixture
def client(tmp_path, monkeypatch):
    root = (tmp_path / "generated_projects").resolve()
    root.mkdir()
    monkeypatch.setattr(export, "GENERATED_ROOT", root)
    records = {}
    monkeypatch.setattr(export, "_generation_record", lambda pid: records.get(pid))
    app = FastAPI()
    app.include_router(export.router)
    return TestClient(app), root, records


def _zip_names(content: bytes):
    return sorted(zipfile.ZipFile(io.BytesIO(content)).namelist())


def test_exports_only_the_requested_projects_files(client):
    c, root, _ = client
    (root / "todo_app" / "backend").mkdir(parents=True)
    (root / "todo_app" / "backend" / "main.py").write_text("app = 1\n", encoding="utf-8")
    (root / "todo_app" / "node_modules").mkdir()
    (root / "todo_app" / "node_modules" / "dep.js").write_text("x", encoding="utf-8")
    (root / "other_app").mkdir()
    (root / "other_app" / "secret.py").write_text("y", encoding="utf-8")

    res = c.get("/api/export/zip/todo_app")

    assert res.status_code == 200
    names = _zip_names(res.content)
    assert any(n.endswith("backend/main.py") for n in names)
    assert not any("node_modules" in n or "secret.py" in n for n in names)


def test_unknown_project_is_404_not_a_fabricated_stub(client):
    c, _, _ = client
    assert c.get("/api/export/zip/does_not_exist").status_code == 404


def test_unfinished_generation_cannot_be_exported(client):
    c, _, records = client
    records["gen_running"] = {"status": "running", "project_path": ""}
    assert c.get("/api/export/zip/gen_running").status_code == 409


def test_completed_generation_exports_from_its_recorded_path(client):
    c, root, records = client
    (root / "gen_output").mkdir()
    (root / "gen_output" / "README.md").write_text("# real output\n", encoding="utf-8")
    records["gen_done"] = {"status": "completed", "project_path": str(root / "gen_output")}

    res = c.get("/api/export/zip/gen_done")

    assert res.status_code == 200
    assert any(n.endswith("README.md") for n in _zip_names(res.content))


@pytest.mark.parametrize("hostile", ["..", "..\\..\\Windows", "../../etc"])
def test_paths_outside_generated_projects_are_refused(client, tmp_path, hostile):
    c, _, records = client
    records["gen_evil"] = {"status": "completed", "project_path": hostile}
    assert c.get("/api/export/zip/gen_evil").status_code == 404
    assert export._safe_project_dir(hostile) is None
