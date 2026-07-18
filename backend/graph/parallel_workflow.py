import logging
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
from backend.utils.timer import Timer
from backend.graph.profiler import workflow_profiler
from backend.utils.cache import get_cache_stats
from backend.utils.retry import get_retry_stats

_logger = logging.getLogger("aiforge.performance")

# Re-use existing agents (no recreation)
planner = PlannerAgent()
architect = ArchitectAgent()
frontend_agent = FrontendAgent()
backend_agent = BackendAgent()
database_agent = DatabaseAgent()
documentation_agent = DocumentationAgent()
testing_agent = TestingAgent()
reviewer_agent = ReviewerAgent()

# Globals to track overall execution duration
workflow_start_time = 0.0


# ---------------- Nodes ---------------- #

async def planner_node(state: ProjectState) -> dict:
    global workflow_start_time
    # Reset stats for the fresh execution run
    workflow_profiler.clear()
    workflow_start_time = perf_counter()

    _logger.info("INFO Planner Started")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    with Timer() as timer:
        plan = await planner.run_async(prompt)
    
    workflow_profiler.record_agent_time("planner", timer.elapsed)
    _logger.info("INFO Planner Finished")

    return {
        "plan": plan,
        "current_step": "planner",
    }


async def architect_node(state: ProjectState) -> dict:
    _logger.info("INFO Architect Started")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    architecture_input = f"""Project Request
{prompt}

Project Plan
{state.get('plan', '')}"""

    with Timer() as timer:
        architecture = await architect.run_async(architecture_input)

    workflow_profiler.record_agent_time("architect", timer.elapsed)
    _logger.info("INFO Architect Finished")

    return {
        "architecture": architecture,
        "current_step": "architect",
    }


async def frontend_node(state: ProjectState) -> dict:
    _logger.info("INFO Frontend Started")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    frontend_prompt = f"""Project Request
{prompt}

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

    with Timer() as timer:
        frontend = await frontend_agent.run_async(frontend_prompt)

    workflow_profiler.record_agent_time("frontend", timer.elapsed)
    _logger.info("INFO Frontend Finished")

    return {
        "frontend": frontend,
        "current_step": "frontend",
    }


async def backend_node(state: ProjectState) -> dict:
    _logger.info("INFO Backend Started")
    state_copy = dict(state)
    with Timer() as timer:
        result_state = await backend_agent.run_async(state_copy)

    workflow_profiler.record_agent_time("backend", timer.elapsed)
    _logger.info("INFO Backend Finished")

    return {
        "backend": result_state.get("backend", ""),
        "current_step": "backend",
    }


async def database_node(state: ProjectState) -> dict:
    _logger.info("INFO Database Started")
    state_copy = dict(state)
    with Timer() as timer:
        result_state = await database_agent.run_async(state_copy)

    workflow_profiler.record_agent_time("database", timer.elapsed)
    _logger.info("INFO Database Finished")

    return {
        "database": result_state.get("database", ""),
        "current_step": "database",
    }


async def testing_node(state: ProjectState) -> dict:
    _logger.info("INFO Testing Started")
    code_to_test = f"""Frontend
{state.get('frontend', '')}

Backend
{state.get('backend', '')}

Database
{state.get('database', '')}"""

    with Timer() as timer:
        tests = await testing_agent.run_async(code_to_test)

    workflow_profiler.record_agent_time("testing", timer.elapsed)
    _logger.info("INFO Testing Finished")

    return {
        "tests": tests,
        "current_step": "testing",
    }


async def documentation_node(state: ProjectState) -> dict:
    _logger.info("INFO Documentation Started")
    state_copy = dict(state)
    with Timer() as timer:
        result_state = await documentation_agent.run_async(state_copy)

    workflow_profiler.record_agent_time("documentation", timer.elapsed)
    _logger.info("INFO Documentation Finished")

    return {
        "documentation": result_state.get("documentation", ""),
        "current_step": "documentation",
    }


async def reviewer_node(state: ProjectState) -> dict:
    _logger.info("INFO Reviewer Started")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    previous_output = f"""Frontend
{state.get('frontend', '')}

Backend
{state.get('backend', '')}

Database
{state.get('database', '')}"""

    with Timer() as timer:
        review = await reviewer_agent.run_async(
            prompt,
            previous_output=previous_output,
        )

    workflow_profiler.record_agent_time("reviewer", timer.elapsed)
    _logger.info("INFO Reviewer Finished")

    # Workflow ends at Reviewer node. Compute total time and print report.
    total_workflow_time = perf_counter() - workflow_start_time
    workflow_profiler.set_total_time(total_workflow_time)

    # Gather cache and retry stats
    cache_stats = get_cache_stats()
    hits = cache_stats.get("hits", 0)
    misses = cache_stats.get("misses", 0)
    ratio = cache_stats.get("hit_ratio", 0.0)
    retries = get_retry_stats()
    llm_calls = hits + misses

    avg_time = workflow_profiler.get_average_agent_time()
    slowest_name, slowest_time = workflow_profiler.get_slowest_agent()

    # Log Execution report to output
    print("\n" + workflow_profiler.format_report() + "\n")

    report = f"""==============================
AIForge Execution Report
==============================
Planner PASS
Architect PASS
Frontend PASS
Backend PASS
Database PASS
Testing PASS
Documentation PASS
Reviewer PASS

Execution Time: {total_workflow_time:.1f} s
Average Agent Time: {avg_time:.1f} s
Slowest Agent: {slowest_name} ({slowest_time:.1f} s)
LLM Calls: {llm_calls}
Cache Hits: {hits}
Cache Misses: {misses}
Cache Hit Ratio: {ratio:.2f}
Retries Used: {retries}
==============================\n"""
    print(report)
    _logger.info("INFO Workflow Completed")

    return {
        "review": review,
        "current_step": "reviewer",
    }


# ---------------- Graph ---------------- #

builder = StateGraph(ProjectState)

builder.add_node("planner", planner_node)
builder.add_node("architect", architect_node)
builder.add_node("frontend", frontend_node)
builder.add_node("backend", backend_node)
builder.add_node("database", database_node)
builder.add_node("testing", testing_node)
builder.add_node("documentation", documentation_node)
builder.add_node("reviewer", reviewer_node)

builder.set_entry_point("planner")

builder.add_edge("planner", "architect")

# Parallel Execution fan-out
builder.add_edge("architect", "frontend")
builder.add_edge("architect", "backend")
builder.add_edge("architect", "database")

# Parallel Execution fan-in
builder.add_edge("frontend", "testing")
builder.add_edge("backend", "testing")
builder.add_edge("database", "testing")

builder.add_edge("testing", "documentation")
builder.add_edge("documentation", "reviewer")
builder.add_edge("reviewer", END)

parallel_graph = builder.compile()
