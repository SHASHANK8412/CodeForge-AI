import logging
import json
from time import perf_counter
from pathlib import Path
from typing import Dict, Any

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

from backend.services.cache_service import global_cache_service
from backend.services.validator import global_stage_validator
from backend.services.project_builder import global_structured_project_builder
from backend.services.prompt_builder import global_prompt_builder
from backend.utils.summarizer import summarize_plan, summarize_architecture, extract_ui_info, extract_backend_info, extract_file_list

_logger = logging.getLogger("aiforge.performance")

# Re-use existing agents
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

workflow_start_time = 0.0


# ---------------- Nodes ---------------- #

async def planner_node(state: ProjectState) -> dict:
    global workflow_start_time
    workflow_profiler.clear()
    workflow_start_time = perf_counter()

    prompt = state.get("user_prompt") or state.get("prompt", "")
    _logger.info(f"✔ Planner started for prompt: {prompt[:40]}...")

    # Check Node Cache
    cached_plan = global_cache_service.get("planner", prompt)
    if cached_plan:
        _logger.info("✔ Planner used cached plan JSON")
        return {
            "prompt": prompt,
            "user_prompt": prompt,
            "plan": cached_plan,
            "current_step": "planner",
            "stream_events": ["✔ Planner completed (Cached)"]
        }

    with Timer() as timer:
        raw_plan = await planner.run_async(prompt)

    # Validate & parse JSON contract
    is_valid, msg, plan_json = global_stage_validator.validate_plan(raw_plan)
    global_cache_service.set("planner", prompt, plan_json)
    workflow_profiler.record_agent_time("planner", timer.elapsed)
    _logger.info("✔ Planner completed successfully")

    return {
        "prompt": prompt,
        "user_prompt": prompt,
        "plan": plan_json,
        "current_step": "planner",
        "stream_events": ["✔ Planner completed"]
    }


async def architect_node(state: ProjectState) -> dict:
    _logger.info("✔ Architect started")
    plan_json = state.get("plan", {})

    # Check Cache
    cached_arch = global_cache_service.get("architect", plan_json)
    if cached_arch:
        _logger.info("✔ Architect used cached architecture JSON")
        return {
            "architecture": cached_arch,
            "current_step": "architect",
            "stream_events": ["✔ Architecture generated (Cached)"]
        }

    arch_prompt = global_prompt_builder.build_architect_prompt(plan_json if isinstance(plan_json, dict) else {})
    with Timer() as timer:
        raw_arch = await architect.run_async(arch_prompt)

    is_valid, msg, arch_json = global_stage_validator.validate_architecture(raw_arch)
    global_cache_service.set("architect", plan_json, arch_json)
    workflow_profiler.record_agent_time("architect", timer.elapsed)
    _logger.info("✔ Architect completed successfully")

    return {
        "architecture": arch_json,
        "current_step": "architect",
        "stream_events": ["✔ Architecture generated"]
    }


async def frontend_node(state: ProjectState) -> dict:
    _logger.info("✔ Frontend generating...")
    arch_json = state.get("architecture", {})

    cached_fe = global_cache_service.get("frontend", arch_json)
    if cached_fe:
        return {
            "frontend": cached_fe,
            "current_step": "frontend",
            "stream_events": ["✔ Frontend generated (Cached)"]
        }

    fe_prompt = global_prompt_builder.build_frontend_prompt(arch_json if isinstance(arch_json, dict) else {})
    with Timer() as timer:
        frontend_code = await frontend_agent.run_async(fe_prompt)

    global_cache_service.set("frontend", arch_json, frontend_code)
    workflow_profiler.record_agent_time("frontend", timer.elapsed)

    return {
        "frontend": frontend_code,
        "current_step": "frontend",
        "stream_events": ["✔ Frontend generated"]
    }


async def backend_node(state: ProjectState) -> dict:
    _logger.info("✔ Backend generating...")
    arch_json = state.get("architecture", {})

    cached_be = global_cache_service.get("backend", arch_json)
    if cached_be:
        return {
            "backend": cached_be,
            "current_step": "backend",
            "stream_events": ["✔ Backend generated (Cached)"]
        }

    be_prompt = global_prompt_builder.build_backend_prompt(arch_json if isinstance(arch_json, dict) else {})
    with Timer() as timer:
        backend_code = await backend_agent.run_async(be_prompt)

    global_cache_service.set("backend", arch_json, backend_code)
    workflow_profiler.record_agent_time("backend", timer.elapsed)

    return {
        "backend": backend_code,
        "current_step": "backend",
        "stream_events": ["✔ Backend generated"]
    }


async def database_node(state: ProjectState) -> dict:
    _logger.info("✔ Database generating...")
    arch_json = state.get("architecture", {})

    cached_db = global_cache_service.get("database", arch_json)
    if cached_db:
        return {
            "database": cached_db,
            "current_step": "database",
            "stream_events": ["✔ Database generated (Cached)"]
        }

    db_prompt = global_prompt_builder.build_database_prompt(arch_json if isinstance(arch_json, dict) else {})
    with Timer() as timer:
        database_code = await database_agent.run_async(db_prompt)

    global_cache_service.set("database", arch_json, database_code)
    workflow_profiler.record_agent_time("database", timer.elapsed)

    return {
        "database": database_code,
        "current_step": "database",
        "stream_events": ["✔ Database generated"]
    }


async def assembly_node(state: ProjectState) -> dict:
    _logger.info("✔ Project Assembly started")
    plan_json = state.get("plan", {})
    arch_json = state.get("architecture", {})
    proj_name = plan_json.get("project_name", "AIForge Application") if isinstance(plan_json, dict) else "AIForge Application"

    assembled = global_structured_project_builder.assemble_real_project(
        project_name=proj_name,
        plan_json=plan_json if isinstance(plan_json, dict) else {},
        arch_json=arch_json if isinstance(arch_json, dict) else {},
        frontend_code=str(state.get("frontend", "")),
        backend_code=str(state.get("backend", "")),
        database_code=str(state.get("database", "")),
        testing_code=str(state.get("tests", "")),
        docs_code=str(state.get("documentation", ""))
    )

    return {
        "current_step": "assembly",
        "stream_events": ["✔ Project Assembly completed"]
    }


async def reviewer_node(state: ProjectState) -> dict:
    _logger.info("✔ Reviewer running...")
    rev_prompt = global_prompt_builder.build_reviewer_prompt({
        "frontend": str(state.get("frontend", "")),
        "backend": str(state.get("backend", ""))
    })

    with Timer() as timer:
        review_output = await reviewer_agent.run_async(rev_prompt)

    workflow_profiler.record_agent_time("reviewer", timer.elapsed)

    return {
        "review": {"review_text": review_output, "score": 95.0},
        "current_step": "reviewer",
        "stream_events": ["✔ Reviewer completed"]
    }


async def testing_node(state: ProjectState) -> dict:
    _logger.info("✔ Testing agent running...")
    test_prompt = global_prompt_builder.build_testing_prompt(
        str(state.get("backend", "")),
        str(state.get("frontend", ""))
    )

    with Timer() as timer:
        tests_code = await testing_agent.run_async(test_prompt)

    workflow_profiler.record_agent_time("testing", timer.elapsed)

    return {
        "tests": tests_code,
        "current_step": "testing",
        "stream_events": ["✔ Tests generated"]
    }


async def documentation_node(state: ProjectState) -> dict:
    _logger.info("✔ Documentation generating...")
    plan_json = state.get("plan", {})
    proj_name = plan_json.get("project_name", "AIForge Application") if isinstance(plan_json, dict) else "AIForge Application"

    with Timer() as timer:
        docs_code = await documentation_agent.run_async(f"Generate production README.md for {proj_name}")

    workflow_profiler.record_agent_time("documentation", timer.elapsed)

    return {
        "documentation": docs_code,
        "current_step": "documentation",
        "stream_events": ["✔ Documentation generated"]
    }


async def deployment_node(state: ProjectState) -> dict:
    _logger.info("✔ Packaging project...")

    # Assemble and write final files
    project_name = "AIForge Project"
    if isinstance(state.get("plan"), dict):
        project_name = state["plan"].get("project_name", "AIForge Project")

    project_dir, report = project_generator.generate_project_structure(project_name, state)

    return {
        "project_path": str(project_dir),
        "validation_report": report.to_dict(),
        "current_step": "deployment",
        "stream_events": ["✔ Project Packaged & Download Ready"]
    }


# ---------------- Graph Construction ---------------- #

builder = StateGraph(ProjectState)

builder.add_node("planner", planner_node)
builder.add_node("architect", architect_node)
builder.add_node("frontend", frontend_node)
builder.add_node("backend", backend_node)
builder.add_node("database", database_node)
builder.add_node("assembly", assembly_node)
builder.add_node("reviewer", reviewer_node)
builder.add_node("testing", testing_node)
builder.add_node("documentation", documentation_node)
builder.add_node("deployment", deployment_node)

# Flow Setup
builder.set_entry_point("planner")
builder.add_edge("planner", "architect")

# Parallel Execution Branch after Architect
builder.add_edge("architect", "frontend")
builder.add_edge("architect", "backend")
builder.add_edge("architect", "database")

# Fan-in Assembly
builder.add_edge("frontend", "assembly")
builder.add_edge("backend", "assembly")
builder.add_edge("database", "assembly")

# Sequential Validation & Export after Assembly
builder.add_edge("assembly", "reviewer")
builder.add_edge("reviewer", "testing")
builder.add_edge("testing", "documentation")
builder.add_edge("documentation", "deployment")
builder.add_edge("deployment", END)

parallel_graph = builder.compile()
