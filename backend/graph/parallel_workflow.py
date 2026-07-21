import logging
from time import perf_counter
from pathlib import Path

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
from backend.agents.deployment_agent import DeploymentAgent
from backend.generators.project_generator import ProjectGenerator
from backend.review.self_heal import SelfHealOrchestrator
from backend.validation.validator import ValidationOrchestrator
from backend.graph.reflection_node import reflection_node
from backend.utils.timer import Timer
from backend.graph.profiler import workflow_profiler
from backend.utils.cache import get_cache_stats
from backend.utils.retry import get_retry_stats
from backend.utils.summarizer import (
    summarize_plan,
    summarize_architecture,
    extract_ui_info,
    extract_backend_info,
    extract_file_list,
)

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
deployment_agent = DeploymentAgent()

project_generator = ProjectGenerator()
self_heal_orchestrator = SelfHealOrchestrator()
validation_orchestrator = ValidationOrchestrator()

# Globals to track overall execution duration
workflow_start_time = 0.0


# ---------------- Nodes ---------------- #

async def planner_node(state: ProjectState) -> dict:
    global workflow_start_time
    # Reset stats for the fresh execution run
    workflow_profiler.clear()
    workflow_start_time = perf_counter()

    prompt = state.get("prompt") or state.get("user_prompt", "")
    
    # Load lessons and optimize prompt automatically before Planner executes
    from backend.services.reflection_service import ReflectionService
    ref_service = ReflectionService()
    optimized_prompt = ref_service.optimize_prompt(prompt)
    
    with Timer() as timer:
        plan = await planner.run_async(optimized_prompt)
    
    workflow_profiler.record_agent_time("planner", timer.elapsed)
    _logger.info("INFO Planner Finished")

    return {
        "prompt": optimized_prompt,
        "plan": plan,
        "current_step": "planner",
    }


async def architect_node(state: ProjectState) -> dict:
    _logger.info("INFO Architect Started")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    plan = state.get("plan", "")
    summarized_plan = summarize_plan(plan)
    architecture_input = f"""Project Request
{prompt}

Project Plan Summary
{summarized_plan}"""

    with Timer() as timer:
        architecture = await architect.run_async(architecture_input)

    workflow_profiler.record_agent_time("architect", timer.elapsed)
    _logger.info("INFO Architect Finished")

    return {
        "architecture": architecture,
        "current_step": "architect",
    }


async def debate_node(state: ProjectState) -> dict:
    _logger.info("INFO Debate Started")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    
    # Toggle debate optionally via config parameters
    enable_debate = state.get("enable_debate", False)
    if not enable_debate:
        _logger.info("Debate is disabled. Skipping debate node.")
        return {"current_step": "debate"}

    from backend.debate.orchestrator import DebateOrchestrator
    from backend.graph.debate_graph import DebateGraphVisualizer

    orchestrator = DebateOrchestrator()
    with Timer() as timer:
        debate_result = await orchestrator.run_debate(prompt)
    
    # Save debate visual graph
    votes = {agent: info.get("choice", "REST") for agent, info in debate_result["rounds_history"][-1].items()}
    visualizer = DebateGraphVisualizer()
    visualizer.generate_and_save_graph(
        participants=debate_result["participants"],
        votes=votes,
        consensus=debate_result["winning_solution"]
    )
    
    workflow_profiler.record_agent_time("debate", timer.elapsed)
    _logger.info("INFO Debate Finished")
    
    revised_architecture = state.get("architecture", "") + f"\n\n### Consensus Decision:\n{debate_result['reasoning']}"
    return {
        "architecture": revised_architecture,
        "current_step": "debate"
    }


async def frontend_node(state: ProjectState) -> dict:
    _logger.info("INFO Frontend Started")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    
    plan_ui = extract_ui_info(state.get('plan', ''), state.get('architecture', ''))
    frontend_prompt = f"""Project Request
{prompt}

UI Relevant Scope
{plan_ui}

Generate functional React components and routing code for the application.
Include the React code inside code blocks annotated with the filename:
```jsx
// filename: frontend/src/App.jsx
import React from 'react';
...
```
Do NOT write summaries, folder lists, or bullet points. Generate the actual code files."""

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


async def deployment_node(state: ProjectState) -> dict:
    _logger.info("INFO Deployment Started")
    state_copy = dict(state)
    with Timer() as timer:
        result_state = await deployment_agent.run_async(state_copy)

    workflow_profiler.record_agent_time("deployment", timer.elapsed)
    _logger.info("INFO Deployment Finished")

    return {
        "deployment_files": result_state.get("deployment_files", {}),
        "deployment_report": result_state.get("deployment_report", {}),
        "deployment_platform": result_state.get("deployment_platform", "Unknown"),
        "deployment_guide": result_state.get("deployment_guide", ""),
        "documentation": result_state.get("documentation", ""),
        "current_step": "deployment",
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
    
    file_list = extract_file_list(
        state.get('frontend', ''),
        state.get('backend', ''),
        state.get('database', '')
    )
    arch_summary = summarize_architecture(state.get('architecture', ''))
    test_results = state.get('test_results') or state.get('tests') or "No test execution output."
    changed_files = "No post-generation file edits detected."
    
    previous_output = f"""Generated File List:
{file_list}

Architecture Summary:
{arch_summary}

Test Results:
{test_results}

Changed Files:
{changed_files}"""

    with Timer() as timer:
        review = await reviewer_agent.run_async(
            prompt,
            previous_output=previous_output,
        )

    workflow_profiler.record_agent_time("reviewer", timer.elapsed)
    _logger.info("INFO Reviewer Finished")

    return {
        "review": review,
        "current_step": "reviewer",
    }


async def assemble_node(state: ProjectState) -> dict:
    _logger.info("INFO Project Generation Started")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    project_dir, report = project_generator.generate_project_structure(prompt, state)
    _logger.info("INFO Project Assembled on Disk")
    return {
        "project_path": str(project_dir),
        "current_step": "assemble",
    }


async def validation_node(state: ProjectState) -> dict:
    _logger.info("INFO QA Validation Engine Started")
    project_path_str = state.get("project_path")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    
    if not project_path_str:
        _logger.warning("Project path missing from state during validation")
        return {"current_step": "validation"}

    project_path = Path(project_path_str)
    
    report, ready = await validation_orchestrator.execute_validation_pipeline(
        project_name=prompt,
        project_path=project_path,
        heal_orchestrator=self_heal_orchestrator
    )
    
    # Read final modified files back into state fields to prevent overwrite
    state_updates = {
        "validation_report": report.model_dump() if report else {},
        "quality_score": report.quality.model_dump() if report else {},
        "current_step": "validation",
    }

    backend_file = project_path / "backend/main.py"
    if backend_file.exists():
        with open(backend_file, "r", encoding="utf-8") as f:
            state_updates["backend"] = f.read()

    frontend_file = project_path / "frontend/src/App.jsx"
    if frontend_file.exists():
        with open(frontend_file, "r", encoding="utf-8") as f:
            state_updates["frontend"] = f.read()

    database_file = project_path / "database/schema.sql"
    if database_file.exists():
        with open(database_file, "r", encoding="utf-8") as f:
            state_updates["database"] = f.read()

    return state_updates


async def export_node(state: ProjectState) -> dict:
    _logger.info("INFO Finalizing Project Archive...")
    project_path_str = state.get("project_path")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    
    if project_path_str:
        # Re-zip to pack the final modified files
        from backend.generators.project_generator import GENERATED_PROJECTS_DIR
        safe_name = "".join([c if c.isalnum() or c in " -_" else "_" for c in prompt]).strip()
        zip_output_path = GENERATED_PROJECTS_DIR / f"{safe_name}.zip"
        project_generator.zip_service.zip_project(Path(project_path_str), zip_output_path)
        _logger.info("INFO ZIP package rebuilt successfully")

    # Log Execution report to output
    global workflow_start_time
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
Self-Healing PASS

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
        "current_step": "export",
    }


builder = StateGraph(ProjectState)

builder.add_node("planner", planner_node)
builder.add_node("architect", architect_node)
builder.add_node("debate", debate_node)
builder.add_node("frontend", frontend_node)
builder.add_node("backend", backend_node)
builder.add_node("database", database_node)
builder.add_node("testing", testing_node)
builder.add_node("deployment", deployment_node)
builder.add_node("documentation", documentation_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("assemble", assemble_node)
builder.add_node("validation", validation_node)
builder.add_node("reflection", reflection_node)
builder.add_node("export", export_node)

builder.set_entry_point("planner")

builder.add_edge("planner", "architect")
builder.add_edge("architect", "debate")

# Parallel Execution fan-out from SRE Debate
builder.add_edge("debate", "frontend")
builder.add_edge("debate", "backend")
builder.add_edge("debate", "database")

# Parallel Execution fan-in
builder.add_edge("frontend", "testing")
builder.add_edge("backend", "testing")
builder.add_edge("database", "testing")

builder.add_edge("testing", "deployment")
builder.add_edge("deployment", "documentation")
builder.add_edge("documentation", "reviewer")
builder.add_edge("reviewer", "assemble")
builder.add_edge("assemble", "validation")
builder.add_edge("validation", "reflection")
builder.add_edge("reflection", "export")
builder.add_edge("export", END)

parallel_graph = builder.compile()
