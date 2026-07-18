"""
End-to-end "Project Generation" pipeline.

This is a SEPARATE workflow from `backend/graph/workflow.py` (the existing
chat/coding workflow). It does not modify or replace that workflow — it
reuses the same already-implemented agent classes to run one autonomous
pipeline that turns a single prompt (e.g. "Build an E-Commerce Website")
into a full project: plan, architecture, frontend, backend, database
schema, documentation, tests, review and GitHub metadata.

Pipeline (Frontend/Backend/Database run CONCURRENTLY for speed):

    User Prompt
        -> Planner Agent
        -> Architect Agent
        -> [ Frontend Agent | Backend Agent | Database Agent ]  (parallel)
        -> Documentation Agent
        -> Testing Agent
        -> Reviewer Agent
        -> GitHub Agent
        -> Final ProjectState

Every stage is an async node. The underlying agents run asynchronously via
their `run_async` methods. LangGraph's fan-out and fan-in edges execute
Frontend, Backend, and Database concurrently in the async event loop.
"""

import asyncio
from time import perf_counter

from langgraph.graph import StateGraph, END

from backend.graph.project_state import ProjectState
from backend.agents.planner_agent import PlannerAgent
from backend.agents.architect_agent import ArchitectAgent
from backend.agents.frontend_agent import FrontendAgent
from backend.agents.backend_agent import BackendAgent
from backend.agents.database_agent import DatabaseAgent
from backend.agents.documentation import DocumentationAgent
from backend.agents.testing_agent import TestingAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.github_agent import GitHubAgent
from backend.services.llm import stream_queue_var


# ---------------- Agents (reused, not rebuilt) ---------------- #

planner = PlannerAgent()
architect = ArchitectAgent()
frontend_agent = FrontendAgent()
backend_agent = BackendAgent()
database_agent = DatabaseAgent()
documentation_agent = DocumentationAgent()
testing_agent = TestingAgent()
reviewer_agent = ReviewerAgent()
github_agent = GitHubAgent()


def log_stage(message: str) -> None:
    print(message)


def log_stage_duration(stage: str, started_at: float) -> float:
    elapsed_ms = (perf_counter() - started_at) * 1000
    print(f"{stage} Completed in {elapsed_ms:.1f}ms")
    return elapsed_ms


async def _run_stage_async(stage_name: str, task_key: str, coro) -> dict:
    """
    Shared async wrapper for every node in the async project graph.
    Runs the agent's async work, logs timing metrics, and pushes stage-completed
    metadata into the streaming queue if it's active.
    """
    log_stage(f"{stage_name} Started")
    started_at = perf_counter()

    try:
        update = await coro
    except Exception as exc:  # noqa: BLE001
        log_stage(f"{stage_name} Failed: {exc}")
        log_stage_duration(stage_name, started_at)
        err_msg = f"{stage_name} failed: {exc}"
        update = {"error": err_msg}
        
        # Emit completion with error to the queue
        queue = stream_queue_var.get()
        if queue is not None:
            await queue.put(("completed", task_key, update))
        return update

    log_stage(f"{stage_name} Completed")
    log_stage_duration(stage_name, started_at)

    queue = stream_queue_var.get()
    if queue is not None:
        await queue.put(("completed", task_key, update))

    return update


# ---------------- Nodes ---------------- #

async def planner_node(state: ProjectState) -> dict:
    async def work():
        return {"plan": await planner.run_async(state.get("user_prompt", ""))}
    return await _run_stage_async("Planner", "planner", work())


async def architect_node(state: ProjectState) -> dict:
    async def work():
        architecture_input = f"""Project Request
{state.get('user_prompt', '')}

Project Plan
{state.get('plan', '')}"""
        return {"architecture": await architect.run_async(architecture_input)}
    return await _run_stage_async("Architect", "architect", work())


async def frontend_node(state: ProjectState) -> dict:
    async def work():
        frontend_prompt = f"""Project Request
{state.get('user_prompt', '')}

Project Plan
{state.get('plan', '')}

System Architecture
{state.get('architecture', '')}

For THIS project-scaffolding stage only, respond with ONLY:
- Components
- Folder Structure
- Routing

Do NOT generate full source code here. Keep it concise (bullet points,
no more than ~500 words)."""
        return {"frontend": await frontend_agent.run_async(frontend_prompt)}
    return await _run_stage_async("Frontend", "frontend", work())


async def backend_node(state: ProjectState) -> dict:
    async def work():
        state_copy = dict(state)
        result_state = await backend_agent.run_async(state_copy)
        return {"backend": result_state.get("backend", "")}
    return await _run_stage_async("Backend", "backend", work())


async def database_node(state: ProjectState) -> dict:
    async def work():
        state_copy = dict(state)
        result_state = await database_agent.run_async(state_copy)
        return {"database": result_state.get("database", "")}
    return await _run_stage_async("Database", "database", work())


async def documentation_node(state: ProjectState) -> dict:
    async def work():
        state_copy = dict(state)
        result_state = await documentation_agent.run_async(state_copy)
        return {"documentation": result_state.get("documentation", "")}
    return await _run_stage_async("Documentation", "documentation", work())


async def testing_node(state: ProjectState) -> dict:
    async def work():
        code_to_test = f"""Frontend
{state.get('frontend', '')}

Backend
{state.get('backend', '')}

Database
{state.get('database', '')}"""
        return {"tests": await testing_agent.run_async(code_to_test)}
    return await _run_stage_async("Testing", "testing", work())


async def reviewer_node(state: ProjectState) -> dict:
    async def work():
        previous_output = f"""Frontend
{state.get('frontend', '')}

Backend
{state.get('backend', '')}

Database
{state.get('database', '')}"""
        review = await reviewer_agent.run_async(
            state.get("user_prompt", ""),
            previous_output=previous_output,
        )
        return {"review": review}
    return await _run_stage_async("Reviewer", "reviewer", work())


async def github_node(state: ProjectState) -> dict:
    async def work():
        state_copy = dict(state)
        result_state = await github_agent.run_async(state_copy)
        return {"github": result_state.get("github", "")}
    return await _run_stage_async("GitHub", "github", work())


# ---------------- Graph ---------------- #

builder = StateGraph(ProjectState)

builder.add_node("planner", planner_node)
builder.add_node("architect", architect_node)
builder.add_node("frontend", frontend_node)
builder.add_node("backend", backend_node)
builder.add_node("database", database_node)
builder.add_node("documentation", documentation_node)
builder.add_node("testing", testing_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("github", github_node)

builder.set_entry_point("planner")

builder.add_edge("planner", "architect")

# Fan-out: Frontend, Backend and Database all start as soon as Architect
# finishes, and run concurrently.
builder.add_edge("architect", "frontend")
builder.add_edge("architect", "backend")
builder.add_edge("architect", "database")

# Fan-in: Documentation only starts once ALL THREE have completed.
builder.add_edge("frontend", "documentation")
builder.add_edge("backend", "documentation")
builder.add_edge("database", "documentation")

builder.add_edge("documentation", "testing")
builder.add_edge("testing", "reviewer")
builder.add_edge("reviewer", "github")
builder.add_edge("github", END)

project_graph = builder.compile()


