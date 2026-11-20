"""The preferred local model (AIFORGE_LOCAL_MODEL, default Qwen 3.5 9B) and how Qwen 3.x thinking is handled."""

import pytest

from backend.models import model_router
from backend.services import llm

INSTALLED = ["qwen2.5-coder:latest", "qwen2.5:latest", "qwen3.5:9b", "llama3.1:8b"]


@pytest.fixture
def installed(monkeypatch):
    def use(models):
        monkeypatch.setattr(model_router, "discover_installed_models", lambda force_refresh=False: list(models))
    use(INSTALLED)
    monkeypatch.delenv("AIFORGE_LOCAL_MODEL", raising=False)
    for var in ("AIFORGE_GENERAL_MODEL", "AIFORGE_CODING_MODEL", "AIFORGE_DEBUG_MODEL"):
        monkeypatch.delenv(var, raising=False)
    return use


@pytest.mark.parametrize("task,agent", [("CODING", "coding"), ("general", "general"), ("DEBUGGING", "debug"),
                                        ("PROJECT_GENERATION", "planner"), ("PROJECT_GENERATION", "reviewer"),
                                        ("RAG", "rag")])
def test_qwen_3_5_answers_every_task_when_installed(installed, task, agent):
    sel = model_router.ModelRouter().select(task, agent_name=agent)
    assert sel.selected_model == "qwen3.5:9b" and "AIFORGE_LOCAL_MODEL" in sel.reason
    assert "qwen2.5-coder:latest" in sel.fallback_models, "the older models stay as fallbacks"


def test_without_qwen_3_5_the_per_task_choice_is_unchanged(installed):
    installed(["qwen2.5:latest", "qwen2.5-coder:latest"])
    assert model_router.ModelRouter().select("CODING", agent_name="coding").selected_model == "qwen2.5-coder:latest"
    assert model_router.ModelRouter().select("general", agent_name="general").selected_model == "qwen2.5:latest"


def test_explicit_choices_still_win(installed, monkeypatch):
    router = model_router.ModelRouter()
    assert router.select("CODING", agent_name="coding", user_override="llama3.1").selected_model == "llama3.1:8b"
    monkeypatch.setenv("AIFORGE_CODING_MODEL", "qwen2.5-coder")
    assert router.select("CODING", agent_name="coding").selected_model == "qwen2.5-coder:latest"
    monkeypatch.delenv("AIFORGE_CODING_MODEL")
    monkeypatch.setenv("AIFORGE_LOCAL_MODEL", "auto")
    assert router.select("CODING", agent_name="coding").selected_model == "qwen2.5-coder:latest"


def test_qwen_3_thinking_is_off_by_default_and_never_reaches_the_answer(monkeypatch):
    monkeypatch.delenv("AIFORGE_LOCAL_THINKING", raising=False)
    assert llm._thinking_kwargs("qwen3.5:9b") == {"think": False}
    assert llm._thinking_kwargs("qwen2.5-coder:latest") == {}, "older models get no thinking setting"
    monkeypatch.setenv("AIFORGE_LOCAL_THINKING", "on")
    assert llm._thinking_kwargs("qwen3.5:9b") == {"think": True}
    assert llm._strip_thinking("<think>plan the API...</think>\ndef add(a, b):\n    return a + b") == \
        "def add(a, b):\n    return a + b"


def test_the_thinking_setting_is_sent_to_ollama(monkeypatch):
    sent = {}

    class Client:
        def chat(self, **kwargs):
            sent.update(kwargs)
            return {"message": {"content": "ok"}}
    monkeypatch.setattr(llm, "_ollama_client", Client())
    llm._chat_completion("qwen3.5:9b", [{"role": "user", "content": "hi"}])
    assert sent["think"] is False and sent["model"] == "qwen3.5:9b"
