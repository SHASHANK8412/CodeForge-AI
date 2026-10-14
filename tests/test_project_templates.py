"""
Project templates (FastAPI + React, MERN, Next.js): chosen at creation, carried through the
pipeline into the prompts, scaffolded at assembly without overwriting generated files, and
checked for required files at the final review.
"""
import asyncio

from fastapi.testclient import TestClient

from backend.generation.templates import TEMPLATES, apply_scaffold, missing_required_files
from backend.main import app
from backend.services.prompt_builder import global_prompt_builder

CONTRACT = {"routes": ["GET /items", "POST /items"], "models": ["Item"], "components": ["ItemList"]}


def test_templates_endpoint_lists_the_three_stacks():
    body = TestClient(app).get("/api/generations/templates").json()
    assert body["default"] == "fastapi-react"
    assert {t["id"] for t in body["templates"]} == {"fastapi-react", "mern", "nextjs"}
    assert all(t["required_files"] and t["stack"] for t in body["templates"])


def test_unknown_template_is_rejected_and_known_one_is_recorded(monkeypatch):
    from backend.generation import routes as gen_routes
    from backend.generation.store import global_generation_store
    started = []

    async def no_run(gen_id):
        started.append(gen_id)
    monkeypatch.setattr(gen_routes._manager, "run", no_run)
    client = TestClient(app)
    bad = client.post("/api/generations", json={"project_id": "p", "prompt": "Build a store", "template": "rails"})
    assert bad.status_code == 400 and "fastapi-react" in bad.json()["detail"]
    ok = client.post("/api/generations", json={"project_id": "p", "prompt": "Build a store", "template": "mern"})
    assert ok.status_code == 202
    assert global_generation_store.get(ok.json()["generation_id"])["template"] == "mern" and started


def test_prompts_follow_the_template():
    fastapi = global_prompt_builder.build_backend_prompt(CONTRACT, {"project_name": "Shop"}, "fastapi-react")
    mern = global_prompt_builder.build_backend_prompt(CONTRACT, {"project_name": "Shop"}, "mern")
    nextjs = global_prompt_builder.build_backend_prompt(CONTRACT, {"project_name": "Shop"}, "nextjs")
    assert "backend/main.py defines `app = FastAPI" in fastapi
    assert "backend/src/app.js" in mern and "Express" in mern and "FastAPI" not in mern
    assert "app/api/<name>/route.js" in nextjs
    for prompt in (fastapi, mern, nextjs):
        assert "GET /items" in prompt and "### backend/main.py" in prompt  # same output format everywhere
    tests = global_prompt_builder.build_testing_prompt("", "", files={"backend/src/app.js": "export default app"},
                                                       template="mern")
    assert "node:test" in tests and "backend/src/app.js" in tests
    db = global_prompt_builder.build_database_prompt(CONTRACT, {}, "mern")
    assert "database/schema.md" in db and "CREATE TABLE" not in db


def test_scaffold_never_overwrites_and_missing_files_are_reported():
    files = {".gitignore": "custom\n", "backend/package.json": "{}"}
    scaffold = apply_scaffold("mern", files)
    assert ".gitignore" not in scaffold and ".env.example" in scaffold
    assert "MONGODB_URI" in scaffold[".env.example"]
    assert missing_required_files("mern", files) == ["backend/src/app.js", "backend/src/server.js",
                                                     "frontend/package.json", "frontend/src/App.jsx"]
    assert missing_required_files(None, {p: "" for p in TEMPLATES["fastapi-react"]["required_files"]}) == []


def test_assembly_applies_the_template(tmp_path, monkeypatch):
    from backend.graph import parallel_workflow as wf
    monkeypatch.chdir(tmp_path)
    state = {"template": "nextjs", "plan": {"project_name": "Board"},
             "backend": {"package.json": "{}", "app/api/health/route.js": "export function GET() {}"},
             "frontend": {"app/page.js": "export default function Page() { return null }"}}
    out = asyncio.run(wf.assembly_node(state))
    check = out["template_check"]
    assert check["template"] == "nextjs" and ".env.example" in check["scaffolded"]
    assert check["missing_required"] == ["app/layout.js"]
    assert (tmp_path / "generated_projects" / "Board" / ".gitignore").is_file()
