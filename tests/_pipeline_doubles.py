"""
Test doubles for the canonical generation pipeline (backend.services.generation_service).

The Day 11/13/14 tests were written against a since-removed router graph in
backend/graph/workflow.py. Routing now lives in the generation pipeline: intent classification,
complexity/strategy selection, agent dispatch and the review policy. These doubles replace only
the model-calling agents, so the real routing, validation and review decisions still run.
"""
import asyncio
from types import SimpleNamespace

EXPLANATION = (
    "MVC splits an application into three parts. The Model owns the data and business rules, "
    "the View renders that data for the user, and the Controller receives input, updates the "
    "Model and chooses which View to show. Keeping them apart makes each part easier to test."
)
DEBUG = (
    "The error comes from a missing import: `FastAPI` is used before it is imported.\n\n"
    "```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n```\n\n"
    "Add the import at the top of `main.py` and restart the server."
)
RESUME = (
    "# Jane Doe\n\n## Professional Summary\nBackend engineer with 4 years building FastAPI and "
    "PostgreSQL services.\n\n## Skills\n- Python, FastAPI, SQLAlchemy\n- Docker, CI/CD\n\n"
    "## Experience\n**Software Engineer, Acme** (2021-2025)\n- Built REST APIs serving 2M requests/day\n"
    "- Cut p95 latency by 40%\n\n## Education\nB.Tech Computer Science\n"
)


class PipelineDoubles:
    """Records which agents the pipeline dispatched to."""

    def __init__(self, monkeypatch, project_result=None):
        from backend.agents import resume_agent
        from backend.agents.debug_agent import global_debug_agent
        from backend.orchestrator.autonomous_engineer import global_autonomous_engineer
        from backend.services import generation_service as gs

        self.calls = []
        self.prompts = {}
        self.project_result = project_result or {"project_name": "todo-app", "files": {"backend/main.py": "app = None\n"}}

        def recorder(name, output):
            def call(*args, **_kwargs):
                self.calls.append(name)
                prompt = next((a for a in args if isinstance(a, str)), "")
                self.prompts.setdefault(name, []).append(prompt)
                return output
            return call

        monkeypatch.setattr(gs.global_explanation_agent, "process_explanation_request",
                            recorder("explanation", {"response": EXPLANATION, "agent": "ExplanationAgent"}))
        monkeypatch.setattr(gs.global_coding_agent, "process_coding_request",
                            recorder("coding", {"response": "```python\ndef add(a, b):\n    return a + b\n```", "agent": "CodingAgent"}))
        monkeypatch.setattr(global_debug_agent, "process_debug_request", recorder("debug", {"response": DEBUG, "agent": "DebugAgent"}))
        monkeypatch.setattr(resume_agent.ResumeAgent, "run", lambda _self, prompt: recorder("resume", RESUME)(prompt))
        monkeypatch.setattr(global_autonomous_engineer, "run_autonomous_pipeline", recorder("project", self.project_result))
        monkeypatch.setattr(gs.global_llm_client, "generate", lambda prompt="", **_k: recorder("fast_explanation", EXPLANATION)(prompt))
        monkeypatch.setattr(gs.global_lightweight_planner, "build_plan", recorder("planner", None))
        monkeypatch.setattr(gs.global_response_critic, "critique",
                            recorder("reviewer", SimpleNamespace(needs_revision=False, issues=[])))
        self._pipeline = gs.global_generation_pipeline

    def run(self, prompt, **kwargs):
        return asyncio.run(self._pipeline.generate(prompt, **kwargs))
