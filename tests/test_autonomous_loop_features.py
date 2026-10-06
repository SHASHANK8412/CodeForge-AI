"""Token tracking, run metrics, the code-quality gate, security in the final approval, GitHub auto-publish."""
import asyncio

import pytest

from backend.generation.store import global_generation_store as store
from backend.telemetry.usage import current_generation_var, record_llm_call, token_counts
from backend.validation.quality_gate import run_quality_gate


def run(coro):
    return asyncio.run(coro)


# --- token usage --------------------------------------------------------------------------

def test_token_counts_read_ollama_fields():
    assert token_counts({"prompt_eval_count": 120, "eval_count": 45}) == (120, 45)

    class Chunk:
        prompt_eval_count = 7
        eval_count = 3
    assert token_counts(Chunk()) == (7, 3)
    assert token_counts({}) == (0, 0)


def test_llm_calls_are_attributed_to_the_running_generation(monkeypatch):
    gen_id = store.create("proj", "user", "build a todo app")
    token = current_generation_var.set(gen_id)
    try:
        record_llm_call("planner", "llama3.2:3b", 100, 40, 2.5)
        record_llm_call("backend", "qwen2.5-coder", 300, 200, 9.0)
        record_llm_call("backend", "qwen2.5-coder", 0, 0, 0.0, cached=True)
    finally:
        current_generation_var.reset(token)
    record_llm_call("chat", "llama3.2:3b", 999, 999, 1.0)  # outside a run: not attributed

    usage = store.get(gen_id)["usage"]
    assert usage["prompt_tokens"] == 400 and usage["completion_tokens"] == 240 and usage["total_tokens"] == 640
    assert usage["llm_calls"] == 3 and usage["cached_calls"] == 1
    assert usage["by_agent"]["backend"]["calls"] == 2
    assert usage["cost_usd"] == 0.0, "local models have no API cost unless rates are configured"


def test_cost_uses_configured_rates(monkeypatch):
    monkeypatch.setenv("AIFORGE_COST_PER_1K_PROMPT", "0.5")
    monkeypatch.setenv("AIFORGE_COST_PER_1K_COMPLETION", "1.5")
    gen_id = store.create("proj", "user", "x")
    token = current_generation_var.set(gen_id)
    try:
        record_llm_call("planner", "m", 1000, 2000, 1.0)
    finally:
        current_generation_var.reset(token)
    assert store.get(gen_id)["usage"]["cost_usd"] == 3.5


def test_metrics_set_and_increment():
    gen_id = store.create("proj", "user", "x")
    store.update_metrics(gen_id, tests_passed=4, tests_total=5)
    store.update_metrics(gen_id, increment={"auto_fixes": 1})
    store.update_metrics(gen_id, increment={"auto_fixes": 1})
    m = store.get(gen_id)["metrics"]
    assert m["tests_passed"] == 4 and m["tests_total"] == 5 and m["auto_fixes"] == 2


# --- code-quality gate --------------------------------------------------------------------

def test_quality_gate_blocks_real_defects_only(tmp_path):
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "main.py").write_text("import os\n\ndef handler(token=Depends(auth)):\n    return token\n", encoding="utf-8")
    (tmp_path / "backend" / "ok.py").write_text("import json\n", encoding="utf-8")  # unused import: not blocking
    gate = run_quality_gate(tmp_path)
    assert gate["passed"] is False
    assert {e["code"] for e in gate["errors"]} == {"F821"}
    assert all(e["file"] == "backend/main.py" for e in gate["errors"])


def test_quality_gate_passes_clean_code(tmp_path):
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    assert run_quality_gate(tmp_path)["passed"] is True


# --- security in the final approval --------------------------------------------------------

def test_final_approval_carries_security_findings():
    from backend.graph.parallel_workflow import final_approval_node
    state = {
        "project_id": "p", "files": {"a.py": "x"},
        "test_results": {"success": True, "passed": 3, "total": 3},
        "security_data": {"gate_status": "FAILED", "security_score": 60.0,
                          "findings": [{"severity": "CRITICAL", "category": "SECRET", "file": ".env", "line": 1, "description": "AWS key"}]},
        "quality_gate": {"passed": True, "error_count": 0, "warning_count": 2},
    }
    req = run(final_approval_node(state))["approval_request"]
    assert req["security"]["gate"] == "FAILED" and req["security"]["finding_count"] == 1
    assert req["deployment_readiness"] == "SECURITY REVIEW REQUIRED"
    assert req["quality_gate"]["warning_count"] == 2


# --- GitHub auto-publish -------------------------------------------------------------------

@pytest.fixture
def project_dir(tmp_path):
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")
    return tmp_path


def _sync(state):
    from backend.graph.parallel_workflow import github_sync_node
    return run(github_sync_node(state))["github"]


def test_github_publish_is_off_by_default(monkeypatch, project_dir):
    monkeypatch.delenv("AIFORGE_AUTO_PUBLISH_GITHUB", raising=False)
    gh = _sync({"project_id": "unpublished-xyz", "project_path": str(project_dir)})
    assert gh["status"] == "NOT_PUBLISHED" and "AIFORGE_AUTO_PUBLISH_GITHUB" in gh["reason"]


def test_github_publish_when_enabled(monkeypatch, project_dir):
    from backend.github import publisher
    monkeypatch.setenv("AIFORGE_AUTO_PUBLISH_GITHUB", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    calls = {}

    def fake_publish(**kwargs):
        calls.update(kwargs)
        return {"status": "published", "repository": {"url": "https://github.com/me/aiforge-todo"}}

    monkeypatch.setattr(publisher.global_github_publisher, "publish_project", fake_publish)
    gh = _sync({"project_id": "unpublished-xyz", "project_path": str(project_dir), "user_prompt": "todo app"})
    assert gh["status"] == "PUBLISHED" and gh["connected_repository"] == "https://github.com/me/aiforge-todo"
    assert calls["private"] is True and "main.py" in calls["files_manifest"]


def test_github_publish_blocked_by_secret_scan(monkeypatch, project_dir):
    from backend.github import publisher
    monkeypatch.setenv("AIFORGE_AUTO_PUBLISH_GITHUB", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")

    def blocked(**kwargs):
        raise publisher.SecurityViolationError("secret found", [{"file": ".env"}])

    monkeypatch.setattr(publisher.global_github_publisher, "publish_project", blocked)
    assert _sync({"project_id": "unpublished-xyz", "project_path": str(project_dir)})["status"] == "BLOCKED"
