"""
Cross-file import validation, the shadowed-module repair, and safe patch application.

The import defects are the ones a real end-to-end run produced (qwen2.5-coder / llama3.2):
main.py imported models.session and models.item that were never written, `get_db` from a
package that did not define it, and models.py sat next to a models/ package that shadowed it.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

from backend.agents.repair_strategies import fix_shadowed_module, propose_repairs
from backend.repository.patch_engine import global_patch_engine
from backend.repository.scanner import global_repository_scanner
from backend.validation.import_check import local_import_issues
from backend.validation.quality_gate import run_quality_gate


def _write(root, files):
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


BROKEN = {
    "main.py": "from models import get_db\nfrom models.user import User\nfrom models.session import Session\n",
    "models.py": "def get_db():\n    return None\n",
    "models/__init__.py": "",
    "models/user.py": "class User:\n    pass\n",
}


def _messages(issues):
    return {(i["file"], i["code"]) for i in issues}


def test_reports_missing_modules_names_and_shadowed_module(tmp_path):
    _write(tmp_path, BROKEN)
    found = _messages(local_import_issues(tmp_path))
    assert found == {
        ("models.py", "AIF-shadowed-module"),
        ("main.py", "AIF-missing-name"),          # get_db is not in models/__init__.py
        ("main.py", "AIF-unresolved-import"),     # models.session does not exist
    }


def test_clean_project_and_third_party_imports_pass(tmp_path):
    _write(tmp_path, {
        "backend/__init__.py": "",
        "backend/main.py": "import os\nfrom fastapi import FastAPI\nfrom backend.db import get_db\nfrom . import db\n",
        "backend/db.py": "def get_db():\n    return None\n",
        "backend/routes/__init__.py": "",
        "backend/routes/items.py": "from ..db import get_db\nfrom backend.routes import items\n",
        # A non-Python folder named like a library must not turn `import redis` into a project import.
        "redis/redis.conf": "port 6379\n",
        "worker.py": "import redis\nimport requests\n",
    })
    assert local_import_issues(tmp_path) == []


def test_backend_folder_is_an_import_root(tmp_path):
    # Started with `cd backend && uvicorn main:app`: `from routes import router` is valid.
    _write(tmp_path, {"backend/main.py": "from routes import router\n", "backend/routes.py": "router = None\n"})
    assert local_import_issues(tmp_path) == []
    _write(tmp_path, {"backend/main.py": "from routes import router, missing\n"})
    assert _messages(local_import_issues(tmp_path)) == {("backend/main.py", "AIF-missing-name")}


def test_quality_gate_blocks_on_import_errors(tmp_path):
    _write(tmp_path, BROKEN)
    gate = run_quality_gate(tmp_path)
    assert gate["passed"] is False
    assert {e["code"] for e in gate["errors"]} >= {"AIF-shadowed-module", "AIF-missing-name", "AIF-unresolved-import"}


def test_shadowed_module_is_merged_into_empty_package_init():
    errors = [{"file": "models.py", "code": "AIF-shadowed-module"}]
    assert fix_shadowed_module(BROKEN, errors) == {"models/__init__.py": BROKEN["models.py"], "models.py": None}
    # Both files have code: merging needs judgement, so no deterministic fix.
    both = {**BROKEN, "models/__init__.py": "Base = object()\n"}
    assert fix_shadowed_module(both, errors) == {}
    strategy, changes = propose_repairs(BROKEN, "", errors)
    assert strategy == "merge_shadowed_module" and changes["models.py"] is None


def test_patch_node_applies_deletion_and_fixes_the_import(tmp_path):
    from backend.graph import parallel_workflow as wf
    _write(tmp_path, BROKEN)
    state = {
        "project_path": str(tmp_path), "files": dict(BROKEN), "project_name": "shadow-demo",
        "fixes": [{"changes": {"models/__init__.py": BROKEN["models.py"], "models.py": None}, "root_cause": "shadowed"}],
    }
    out = asyncio.run(wf.patch_node(state))
    assert not (tmp_path / "models.py").exists()
    assert (tmp_path / "models" / "__init__.py").read_text(encoding="utf-8") == BROKEN["models.py"]
    assert "models.py" not in out["files"] and set(out["files_modified"]) == {"models.py", "models/__init__.py"}
    # get_db is importable now; only the genuinely missing module remains.
    assert _messages(local_import_issues(tmp_path)) == {("main.py", "AIF-unresolved-import")}


def test_patch_rejects_sibling_with_shared_prefix(tmp_path):
    root = tmp_path / "proj"
    sibling = tmp_path / "proj-evil"
    root.mkdir()
    sibling.mkdir()
    with pytest.raises(PermissionError):
        global_repository_scanner.validate_path_safety(str(root), "../proj-evil/x.py")
    paths, ok = global_patch_engine.apply_changes(str(root), {"ok.py": "x = 1\n", "../proj-evil/x.py": "pwned\n"})
    assert ok is False and paths == []
    assert not (sibling / "x.py").exists()
    assert not (root / "ok.py").exists(), "all-or-nothing: the safe file is rolled back too"


def test_file_route_does_not_read_other_projects(tmp_path, monkeypatch):
    from backend.generators import project_generator
    from backend.main import app
    base = tmp_path / "generated"
    _write(base, {"alpha/app.py": "print('alpha')\n", "alpha-secret/keys.txt": "secret\n"})
    monkeypatch.setattr(project_generator, "GENERATED_PROJECTS_DIR", base)
    client = TestClient(app)
    ok = client.get("/project/alpha/file", params={"path": "app.py"})
    assert ok.status_code == 200 and "alpha" in ok.text
    for path in ("../alpha-secret/keys.txt", "../../etc/passwd"):
        assert client.get("/project/alpha/file", params={"path": path}).status_code == 400
