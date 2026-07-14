from backend.agents import testing_agent as testing_agent_module


def test_testing_agent_process_delegates_to_run(monkeypatch):
    agent = testing_agent_module.TestingAgent()
    captured = {}

    def fake_run(user_prompt, memory_context="", previous_output=""):
        captured["user_prompt"] = user_prompt
        captured["memory_context"] = memory_context
        captured["previous_output"] = previous_output
        return "testing report"

    monkeypatch.setattr(agent, "run", fake_run)

    result = agent.process("def add(a, b):\n    return a + b")

    assert result == "testing report"
    assert "def add(a, b)" in captured["user_prompt"]


def test_testing_agent_run_uses_base_agent(monkeypatch):
    agent = testing_agent_module.TestingAgent()
    captured = {}

    def fake_base_run(self, user_prompt, memory_context="", previous_output=""):
        captured["user_prompt"] = user_prompt
        captured["memory_context"] = memory_context
        captured["previous_output"] = previous_output
        return "analysis"

    monkeypatch.setattr("backend.agents.base_agent.BaseAgent.run", fake_base_run)

    result = agent.run("def add(a, b):\n    return a + b", "ctx", "prev")

    assert result == "analysis"
    assert "Code to Analyze" in captured["user_prompt"]
    assert "def add(a, b)" in captured["user_prompt"]
    assert captured["memory_context"] == "ctx"
    assert captured["previous_output"] == "prev"