"""
Regression tests for deterministic intent routing.

These prompts used to reach the right agent only when the Ollama classifier happened to be
running; offline they fell through to UNKNOWN. They must be decided by the rules alone.
"""
import pytest

from backend.agents.router_agent import global_router_agent


@pytest.fixture(autouse=True)
def no_llm_classifier(monkeypatch):
    def fail(*_a, **_k):
        raise AssertionError("routing fell through to the LLM classifier")
    monkeypatch.setattr(global_router_agent, "_apply_llm_classification", fail)


@pytest.mark.parametrize("prompt,intent", [
    ("Fix previous bug", "DEBUGGING"),
    ("Fix the bug in the login handler", "DEBUGGING"),
    ("Improve my resume for backend roles", "RESUME"),
    ("Generate Resume", "RESUME"),
    ("Review my CV please", "RESUME"),
    ("Explain debugging", "EXPLANATION"),
    ("Explain what a resume is", "EXPLANATION"),
    ("Build a resume builder app with React", "PROJECT_GENERATION"),
])
def test_rules_decide_without_the_llm(prompt, intent):
    assert global_router_agent.classify_intent(prompt)["intent"] == intent


def test_resume_meaning_continue_is_not_a_cv_request():
    # Not confidently classifiable on its own; it must not be routed to the resume writer.
    rule = global_router_agent._apply_deterministic_rules("Resume the build", "resume the build")
    assert rule["intent"] != "RESUME"


def test_follow_up_inherits_previous_turn_intent():
    from backend.context.models import ConversationMessage
    from types import SimpleNamespace
    ctx = SimpleNamespace(is_follow_up=True, resolved_prompt="Continue", selected_messages=[
        ConversationMessage(id="1", role="user", content="Write a date parser"),
        ConversationMessage(id="2", role="assistant", content="def parse(): ...", metadata={"intent": "CODING"}),
    ])
    res = global_router_agent.classify_intent("Continue", context_result=ctx)
    assert res["intent"] == "CODING" and res["classification_source"] == "context"

    # An explicit request still wins over the previous turn.
    ctx.resolved_prompt = "Fix the bug in it"
    assert global_router_agent.classify_intent("Fix the bug in it", context_result=ctx)["intent"] == "DEBUGGING"


def test_follow_up_after_unclear_turn_is_not_guessed():
    from backend.context.models import ConversationMessage
    from types import SimpleNamespace
    ctx = SimpleNamespace(is_follow_up=True, resolved_prompt="Continue", selected_messages=[
        ConversationMessage(id="2", role="assistant", content="Could you clarify?", metadata={"intent": "UNKNOWN"}),
    ])
    assert global_router_agent._previous_turn_intent(ctx) is None
