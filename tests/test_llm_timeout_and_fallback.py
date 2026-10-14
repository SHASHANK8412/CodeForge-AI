import asyncio

import pytest

import backend.services.llm as llm
from backend.utils.retry import LLMDeadlineExceeded


class _NotFound(Exception):
    status_code = 404


@pytest.fixture(autouse=True)
def _clean_blacklist():
    llm._unavailable_models.clear()
    yield
    llm._unavailable_models.clear()


def test_missing_model_is_detected_but_timeouts_are_not():
    assert llm._is_missing_model_error(_NotFound("model 'x' not found"))
    assert not llm._is_missing_model_error(TimeoutError("timed out"))
    assert not llm._is_missing_model_error(ConnectionError("connection refused"))
    # The old heuristic blacklisted any error mentioning "model".
    assert not llm._is_missing_model_error(RuntimeError("model is busy, try again"))


def test_slow_model_raises_deadline_without_blacklisting(monkeypatch):
    calls = []

    async def slow_completion(model, messages, stream=False, options=None):
        calls.append(model)
        await asyncio.sleep(5)

    monkeypatch.setattr(llm, "_chat_completion_async", slow_completion)
    monkeypatch.setattr(llm, "LLM_TIMEOUT_SECONDS", 0.05)

    with pytest.raises(LLMDeadlineExceeded):
        asyncio.run(llm._chat_completion_with_fallback_async([], "llama3.2:3b"))

    assert calls == ["llama3.2:3b"], "a deadline must not be retried or cascade through fallbacks"
    assert "llama3.2:3b" not in llm._unavailable_models


def test_missing_model_falls_back_to_next_candidate(monkeypatch):
    async def completion(model, messages, stream=False, options=None):
        if model == "ghost-model:latest":
            raise _NotFound("model 'ghost-model:latest' not found")
        return {"message": {"content": f"ok from {model}"}}

    monkeypatch.setattr(llm, "_chat_completion_async", completion)

    result = asyncio.run(llm._chat_completion_with_fallback_async([], "ghost-model:latest"))

    assert result["message"]["content"] == f"ok from {llm.DEFAULT_OLLAMA_MODEL}"
    assert "ghost-model:latest" in llm._unavailable_models
