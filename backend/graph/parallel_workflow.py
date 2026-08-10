import os
import logging
import json
import re
import contextvars
from time import perf_counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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

# New Platform Agents
from backend.agents.build_validation_agent import BuildValidationAgent
from backend.agents.dependency_manager_agent import DependencyManagerAgent
from backend.agents.project_execution_agent import ProjectExecutionAgent
from backend.agents.file_quality_agent import FileQualityAgent
from backend.agents.security_agent import SecurityAgent
from backend.agents.performance_agent import PerformanceAgent
from backend.agents.project_packaging_agent import ProjectPackagingAgent

from backend.generators.project_generator import ProjectGenerator
from backend.review.self_heal import SelfHealOrchestrator
from backend.utils.timer import Timer
from backend.graph.profiler import workflow_profiler

from backend.services.cache_service import global_cache_service
from backend.services.validator import global_stage_validator
from backend.services.project_builder import global_structured_project_builder
from backend.services.prompt_builder import global_prompt_builder
from backend.quality.duplicate_detector import global_duplicate_detector
from backend.memory.memory_manager import memory_manager
from backend.execution.project_runner import global_project_runner
from backend.agents.debug_agent import global_debug_agent



_logger = logging.getLogger("aiforge.performance")

# ---------------------------------------------------------------------------
# ContextVar: generation lifecycle callback
# ---------------------------------------------------------------------------
# GenerationManager sets this ContextVar on its asyncio.Task before calling
# parallel_graph.ainvoke(). Every node calls _fire_lifecycle() which reads the
# ContextVar and, if set, notifies the manager about agent start/complete/fail.
# Zero impact on nodes that run without a callback (CLI, tests, etc.).
generation_event_callback_var: contextvars.ContextVar[Optional[Callable]] = (
    contextvars.ContextVar("generation_event_callback_var", default=None)
)


def _fire_lifecycle(
    event_type: str,
    agent_name: str,
    *,
    duration: float = 0.0,
    error: str = "",
) -> None:
    """
    Invoke the registered generation lifecycle callback (if any).
    Safe to call from any node — silently no-ops if no callback is set.
    """
    cb = generation_event_callback_var.get()
    if cb is None:
        return
    try:
        cb(event_type, agent_name, duration=duration, error=error)
    except Exception as exc:  # noqa: BLE001
        _logger.warning("_fire_lifecycle error [%s/%s]: %s", event_type, agent_name, exc)


# Instantiate all Platform Agents
planner = PlannerAgent()
architect = ArchitectAgent()
frontend_agent = FrontendAgent()
backend_agent = BackendAgent()
database_agent = DatabaseAgent()
reviewer_agent = ReviewerAgent()
testing_agent = TestingAgent()
documentation_agent = DocumentationAgent()
build_validation_agent = BuildValidationAgent()
dependency_manager_agent = DependencyManagerAgent()
security_agent = SecurityAgent()
performance_agent = PerformanceAgent()
execution_agent = ProjectExecutionAgent()
file_quality_agent = FileQualityAgent()
packaging_agent = ProjectPackagingAgent()
deployment_agent = DeploymentAgent()

project_generator = ProjectGenerator()
self_heal_orchestrator = SelfHealOrchestrator()

agent_timers: Dict[str, float] = {}


# ---------------- Nodes ---------------- #

async def planner_node(state: ProjectState) -> dict:
    workflow_profiler.clear()
    agent_timers.clear()

    prompt = state.get("user_prompt") or state.get("prompt", "")
    project_id = state.get("project_id") or state.get("project_name") or "default_project"
    gen_id = state.get("generation_id") or state.get("session_id", "default")
    _logger.info(f"✔ [1/14] Planner started: {prompt[:40]}...")
    _fire_lifecycle("agent_started", "planner")

    cached_plan = global_cache_service.get("planner", prompt)
    if cached_plan:
        _fire_lifecycle("agent_completed", "planner", duration=0.0)
        return {
            "prompt": prompt,
            "user_prompt": prompt,
            "plan": cached_plan,
            "current_step": "planner",
            "stream_events": ["✔ Planner completed (Cached)"]
        }

    with Timer() as timer:
        raw_plan = await planner.run_async(prompt)

    session_id = gen_id
    plan_json = planner.parse_plan_json(raw_plan, allow_fallback=True)
    global_cache_service.set("planner", prompt, plan_json)
    memory_manager.save_agent_output(session_id, "planner", plan_json)
    agent_timers["planner"] = timer.elapsed
    workflow_profiler.record_agent_time("planner", timer.elapsed)
    _fire_lifecycle("agent_completed", "planner", duration=timer.elapsed)

    # Persist Planner requirements & tech choices to long-term memory safely
    try:
        reqs = plan_json.get("functional_requirements") or plan_json.get("requirements", [])
        if reqs:
            memory_manager.save(project_id, "REQUIREMENT", "functional_requirements", reqs, "planner", "HIGH", generation_id=gen_id)
        stack = plan_json.get("tech_stack") or {}
        if stack:
            memory_manager.save(project_id, "TECHNOLOGY", "tech_stack", stack, "planner", "HIGH", generation_id=gen_id)
        if "auth" in str(reqs).lower() or "jwt" in str(reqs).lower():
            memory_manager.save_decision(project_id, "JWT Bearer Authentication", "Secure user sessions across API routes", "planner", "HIGH", generation_id=gen_id)
    except Exception as e:
        _logger.warning(f"Planner memory persistence warning: {e}")

    return {
        "prompt": prompt,
        "user_prompt": prompt,
        "user_request": prompt,
        "project_id": project_id,
        "generation_id": gen_id,
        "project_name": plan_json.get("project_name", "AIForgeApp"),
        "requirements": plan_json.get("functional_requirements") or plan_json.get("requirements", []),
        "project_spec": plan_json,
        "plan": plan_json,
        "current_step": "planner",
        "stream_events": ["✔ Planner completed"]
    }



async def architect_node(state: ProjectState) -> dict:
    _logger.info("✔ [2/14] Architect started")
    _fire_lifecycle("agent_started", "architect")
    session_id = state.get("session_id", "default")
    project_id = state.get("project_id") or state.get("project_name") or "default_project"
    gen_id = state.get("generation_id") or session_id
    plan_json = state.get("plan") or memory_manager.get_agent_output(session_id, "planner")

    cached_arch = global_cache_service.get("architect", plan_json)
    if cached_arch:
        memory_manager.save_agent_output(session_id, "architect", cached_arch)
        _fire_lifecycle("agent_completed", "architect", duration=0.0)
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
    memory_manager.save_agent_output(session_id, "architect", arch_json)
    agent_timers["architect"] = timer.elapsed
    workflow_profiler.record_agent_time("architect", timer.elapsed)
    _fire_lifecycle("agent_completed", "architect", duration=timer.elapsed)

    # Persist Architect architecture & key decisions to long-term memory safely
    try:
        memory_manager.save(project_id, "ARCHITECTURE", "architecture_spec", arch_json, "architect", "CRITICAL", generation_id=gen_id)
        be_framework = arch_json.get("backend", "FastAPI")
        db_engine = arch_json.get("database", "PostgreSQL")
        fe_framework = arch_json.get("frontend", "React")

        memory_manager.save_decision(project_id, f"Use {db_engine} database engine", "Relational consistency, indexing, and schema integrity", "architect", "CRITICAL", generation_id=gen_id)
        memory_manager.save_decision(project_id, f"Use {be_framework} backend framework", "High performance async REST API endpoint routing", "architect", "CRITICAL", generation_id=gen_id)
        memory_manager.save_decision(project_id, f"Use {fe_framework} frontend framework", "Component-driven reactive single-page app architecture", "architect", "HIGH", generation_id=gen_id)
    except Exception as e:
        _logger.warning(f"Architect memory persistence warning: {e}")

    return {
        "architecture": arch_json,
        "current_step": "architect",
        "stream_events": ["✔ Architecture generated"]
    }


async def frontend_node(state: ProjectState) -> dict:
    _logger.info("✔ [3a/14] Frontend generating...")
    _fire_lifecycle("agent_started", "frontend")
    session_id = state.get("session_id", "default")
    arch_json = state.get("architecture") or memory_manager.get_agent_output(session_id, "architect")

    cached_fe = global_cache_service.get("frontend", arch_json)
    if cached_fe:
        memory_manager.save_agent_output(session_id, "frontend", cached_fe)
        _fire_lifecycle("agent_completed", "frontend", duration=0.0)
        return {
            "frontend": cached_fe,
            "current_step": "frontend",
            "stream_events": ["✔ Frontend generated (Cached)"]
        }

    fe_prompt = global_prompt_builder.build_frontend_prompt(arch_json if isinstance(arch_json, dict) else {})
    with Timer() as timer:
        frontend_code = await frontend_agent.run_async(fe_prompt)

    global_cache_service.set("frontend", arch_json, frontend_code)
    memory_manager.save_agent_output(session_id, "frontend", frontend_code)
    agent_timers["frontend"] = timer.elapsed
    workflow_profiler.record_agent_time("frontend", timer.elapsed)
    _fire_lifecycle("agent_completed", "frontend", duration=timer.elapsed)

    return {
        "frontend": frontend_code,
        "current_step": "frontend",
        "stream_events": ["✔ Frontend generated"]
    }


async def backend_node(state: ProjectState) -> dict:
    _logger.info("✔ [3b/14] Backend generating...")
    _fire_lifecycle("agent_started", "backend")
    session_id = state.get("session_id", "default")
    arch_json = state.get("architecture") or memory_manager.get_agent_output(session_id, "architect")

    cached_be = global_cache_service.get("backend", arch_json)
    if cached_be:
        memory_manager.save_agent_output(session_id, "backend", cached_be)
        return {
            "backend": cached_be,
            "current_step": "backend",
            "stream_events": ["✔ Backend generated (Cached)"]
        }

    be_prompt = global_prompt_builder.build_backend_prompt(arch_json if isinstance(arch_json, dict) else {})
    with Timer() as timer:
        backend_code = await backend_agent.run_async(be_prompt)

    global_cache_service.set("backend", arch_json, backend_code)
    memory_manager.save_agent_output(session_id, "backend", backend_code)
    agent_timers["backend"] = timer.elapsed
    workflow_profiler.record_agent_time("backend", timer.elapsed)
    _fire_lifecycle("agent_completed", "backend", duration=timer.elapsed)

    return {
        "backend": backend_code,
        "current_step": "backend",
        "stream_events": ["✔ Backend generated"]
    }


async def database_node(state: ProjectState) -> dict:
    _logger.info("✔ [3c/14] Database generating...")
    _fire_lifecycle("agent_started", "database")
    session_id = state.get("session_id", "default")
    arch_json = state.get("architecture") or memory_manager.get_agent_output(session_id, "architect")

    cached_db = global_cache_service.get("database", arch_json)
    if cached_db:
        memory_manager.save_agent_output(session_id, "database", cached_db)
        return {
            "database": cached_db,
            "current_step": "database",
            "stream_events": ["✔ Database generated (Cached)"]
        }

    db_prompt = global_prompt_builder.build_database_prompt(arch_json if isinstance(arch_json, dict) else {})
    with Timer() as timer:
        database_code = await database_agent.run_async(db_prompt)

    global_cache_service.set("database", arch_json, database_code)
    memory_manager.save_agent_output(session_id, "database", database_code)
    agent_timers["database"] = timer.elapsed
    workflow_profiler.record_agent_time("database", timer.elapsed)
    _fire_lifecycle("agent_completed", "database", duration=timer.elapsed)

    return {
        "database": database_code,
        "current_step": "database",
        "stream_events": ["✔ Database generated"]
    }


async def assembly_node(state: ProjectState) -> dict:
    _logger.info("✔ Project Assembly fan-in completed")
    _fire_lifecycle("agent_started", "assembly")
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

    duplicate_report = global_duplicate_detector.detect_duplicates(assembled.get("manifest", {}))
    files_manifest = assembled.get("manifest", {})
    written_path = global_structured_project_builder.write_project_to_disk(proj_name, files_manifest)

    _fire_lifecycle("agent_completed", "assembly")
    return {
        "project_path": str(written_path),
        "files": files_manifest,
        "assembly_manifest": assembled,
        "duplicate_report": duplicate_report,
        "current_step": "assembly",
        "stream_events": [
            "✔ Assembly completed",
            f"✔ Files written to disk at {written_path}",
            f"✔ Duplicate scan: {duplicate_report['duplicate_count']} duplicate block(s) found",
        ]
    }



async def reviewer_node(state: ProjectState) -> dict:
    _logger.info("✔ [4/14] Reviewer running...")
    _fire_lifecycle("agent_started", "reviewer")
    duplicate_report = state.get("duplicate_report", {}) or {}
    rev_prompt = global_prompt_builder.build_reviewer_prompt(
        frontend_code=str(state.get("frontend", "")),
        backend_code=str(state.get("backend", "")),
        database_code=str(state.get("database", "")),
        duplicate_report=duplicate_report,
    )

    with Timer() as timer:
        review_output = await reviewer_agent.run_async(rev_prompt)

    agent_timers["reviewer"] = timer.elapsed
    workflow_profiler.record_agent_time("reviewer", timer.elapsed)

    # Real, if simple, computed score: start at 100 and deduct for actually-detected
    # duplicates and for severity tags the reviewer itself raised in its findings.
    # This is a heuristic, not a precise metric — it replaces a flat hardcoded 95.0.
    score = 100.0
    score -= duplicate_report.get("duplicate_count", 0) * 5
    score -= review_output.count("[Critical]") * 10
    score -= review_output.count("[Major]") * 5
    score -= review_output.count("[Minor]") * 2
    score = max(0.0, min(100.0, score))

    _fire_lifecycle("agent_completed", "reviewer", duration=timer.elapsed)
    return {
        "review": {"review_text": review_output, "score": round(score, 1)},
        "current_step": "reviewer",
        "stream_events": ["✔ Code Review completed"]
    }


TEST_SECTION_HEADERS = ["Unit Tests", "Integration Tests", "API Tests", "End-to-End Tests"]


def _count_tests_by_section(raw_text: str) -> Dict[str, int]:
    """Counts real `def test_...` functions per labeled section in the LLM's response.

    This is intentionally a plain count of what was actually generated, not a fabricated
    pass/fail/coverage statistic — no sandboxed execution happens here.
    """
    counts: Dict[str, int] = {}
    pattern = re.compile(r"##\s*(" + "|".join(TEST_SECTION_HEADERS) + r")", re.IGNORECASE)
    matches = list(pattern.finditer(raw_text))
    for i, match in enumerate(matches):
        section_name = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        counts[section_name] = len(re.findall(r"def\s+test_\w+", raw_text[start:end]))
    return counts


async def testing_node(state: ProjectState) -> dict:
    _logger.info("✔ [5/14] Testing Agent generating test suites...")
    _fire_lifecycle("agent_started", "testing")
    testing_prompt = global_prompt_builder.build_testing_prompt(
        backend_code=str(state.get("backend", "")),
        frontend_code=str(state.get("frontend", "")),
    )

    with Timer() as timer:
        raw_tests = await testing_agent.run_async(testing_prompt)

    agent_timers["testing"] = timer.elapsed
    workflow_profiler.record_agent_time("testing", timer.elapsed)

    section_counts = _count_tests_by_section(raw_tests)
    total_tests = sum(section_counts.values())

    report_lines = [
        "# Automated Test Suite Report",
        "",
        "**Status**: Static generation only — not executed. No pass/fail or coverage data "
        "exists until these tests are actually run.",
        f"**Total test functions generated**: `{total_tests}`",
        "",
        "## Test Suite Breakdown",
        "",
        "| Test Suite Type | Test Functions Generated |",
        "|---|---|",
    ]
    for section in TEST_SECTION_HEADERS:
        report_lines.append(f"| {section} | {section_counts.get(section, 0)} |")
    report_md = "\n".join(report_lines) + "\n"

    exec_results = state.get("execution_results", {})
    project_spec = state.get("project_spec", {})
    architecture = state.get("architecture", {})

    test_res = testing_agent.evaluate_execution_results(
        exec_results=exec_results if isinstance(exec_results, dict) else {},
        project_spec=project_spec if isinstance(project_spec, dict) else {},
        architecture=architecture if isinstance(architecture, dict) else {}
    )

    _fire_lifecycle("agent_completed", "testing", duration=timer.elapsed)
    return {
        "tests": raw_tests,
        "test_results": test_res.model_dump(),
        "testing_report": report_md,
        "current_step": "testing",
        "stream_events": [f"✔ Generated {total_tests} real test function(s) across 4 suites (Verification: {'PASS' if test_res.success else 'FAIL'})"]
    }


testing_node.__test__ = False




async def documentation_node(state: ProjectState) -> dict:
    _logger.info("✔ [6/14] Documentation Agent generating README...")
    _fire_lifecycle("agent_started", "documentation")
    plan_json = state.get("plan", {})
    proj_name = plan_json.get("project_name", "AIForge Application") if isinstance(plan_json, dict) else "AIForge Application"

    with Timer() as timer:
        docs_code = await documentation_agent.run_async(f"Generate production README.md for {proj_name}")

    agent_timers["documentation"] = timer.elapsed
    workflow_profiler.record_agent_time("documentation", timer.elapsed)

    _fire_lifecycle("agent_completed", "documentation", duration=timer.elapsed)
    return {
        "documentation": docs_code,
        "current_step": "documentation",
        "stream_events": ["✔ Documentation generated"]
    }


async def build_validation_node(state: ProjectState) -> dict:
    _logger.info("✔ [7/14] Build Validation Agent executing checks...")
    _fire_lifecycle("agent_started", "build_validation")

    fe_files = {"App.jsx": str(state.get("frontend", ""))}
    be_files = {"main.py": str(state.get("backend", ""))}
    db_code = str(state.get("database", ""))
    dk_files = {"Dockerfile": "FROM python:3.11-slim\nWORKDIR /app"}

    with Timer() as timer:
        val_report = build_validation_agent.validate_all(fe_files, be_files, db_code, dk_files)

    agent_timers["build_validation"] = timer.elapsed

    _fire_lifecycle("agent_completed", "build_validation", duration=timer.elapsed)
    return {
        "validation_report": val_report.dict(),
        "current_step": "build_validation",
        "stream_events": [f"✔ Build Validation: {'PASSED' if val_report.is_valid else 'FAILED'}"]
    }


async def dependency_manager_node(state: ProjectState) -> dict:
    _logger.info("✔ [8/14] Dependency Manager Agent building package manifests...")
    _fire_lifecycle("agent_started", "dependency_manager")
    plan_json = state.get("plan", {})
    proj_name = plan_json.get("project_name", "aiforge-app") if isinstance(plan_json, dict) else "aiforge-app"

    fe_files = {"App.jsx": str(state.get("frontend", ""))}
    be_files = {"main.py": str(state.get("backend", ""))}

    with Timer() as timer:
        deps_files = dependency_manager_agent.run_dependency_analysis(proj_name, be_files, fe_files)

    agent_timers["dependency_manager"] = timer.elapsed

    _fire_lifecycle("agent_completed", "dependency_manager", duration=timer.elapsed)
    return {
        "deployment_files": deps_files,
        "current_step": "dependency_manager",
        "stream_events": ["✔ Dependencies & Manifests compiled"]
    }


async def security_scan_node(state: ProjectState) -> dict:
    _logger.info("✔ [9/14] Security Agent scanning codebase...")
    _fire_lifecycle("agent_started", "security_scan")
    all_files = {
        "frontend/App.jsx": str(state.get("frontend", "")),
        "backend/main.py": str(state.get("backend", "")),
        "database/schema.sql": str(state.get("database", ""))
    }

    with Timer() as timer:
        sec_report = security_agent.scan_files(all_files)
        sec_md = security_agent.generate_security_report_markdown(sec_report)

    agent_timers["security_scan"] = timer.elapsed

    _fire_lifecycle("agent_completed", "security_scan", duration=timer.elapsed)
    return {
        "security_report": sec_md,
        "current_step": "security_scan",
        "stream_events": [f"✔ Security Audit Completed (Score: {sec_report.score}/100)"]
    }


async def performance_node(state: ProjectState) -> dict:
    _logger.info("✔ [10/14] Performance Agent profiling generation metrics...")
    _fire_lifecycle("agent_started", "performance")
    total_time = sum(agent_timers.values())

    with Timer() as timer:
        perf_report = performance_agent.collect_metrics(total_time, agent_timers, estimated_tokens=14200)
        perf_md = performance_agent.generate_performance_report_markdown(perf_report)

    agent_timers["performance"] = timer.elapsed

    _fire_lifecycle("agent_completed", "performance", duration=timer.elapsed)
    return {
        "performance_report": perf_md,
        "current_step": "performance",
        "stream_events": ["✔ Performance Metrics & Profiling report compiled"]
    }


from backend.agents.execution_agent import global_execution_agent
from backend.agents.diagnostic_agent import global_diagnostic_agent
from backend.validation.validation_pipeline import global_validation_pipeline


async def execution_validation_node(state: ProjectState) -> dict:
    _logger.info("✔ [11/14] Execution Agent verifying sandboxed runtime & compilation...")
    _fire_lifecycle("agent_started", "execution_validation")
    project_path = state.get("project_path", "")
    existing_commands = state.get("commands", []) or []
    files_manifest = dict(state.get("files", {}) or {})
    history = list(state.get("execution_history", []) or [])

    with Timer() as timer:
        exec_report = global_execution_agent.execute_project(
            files_manifest=files_manifest,
            project_dir=project_path if project_path else None
        )

    agent_timers["execution_validation"] = timer.elapsed
    exec_dict = exec_report.model_dump()
    cmd_str = exec_report.failed_command or "compileall"
    new_status = "PASS" if exec_report.exit_code == 0 else "FAIL"

    # Run 8-Level Validation Pipeline
    val_report = global_validation_pipeline.run_pipeline(
        files_manifest=files_manifest,
        execution_data=exec_dict,
        test_data=state.get("test_results", {})
    )

    attempt_record = {
        "attempt": len(history) + 1,
        "status": exec_report.status,
        "exit_code": exec_report.exit_code,
        "error_type": exec_report.error_type,
        "failed_command": exec_report.failed_command,
        "duration_ms": exec_report.duration_ms,
        "validation_status": val_report.overall_status
    }
    history.append(attempt_record)

    _fire_lifecycle("agent_completed", "execution_validation", duration=timer.elapsed)
    return {
        "execution_results": exec_dict,
        "execution_history": history,
        "validation_report": val_report.model_dump(),
        "quality_score": val_report.quality_scores,
        "commands": existing_commands + [cmd_str],
        "status": new_status,
        "error": exec_report.stderr if exec_report.exit_code != 0 else "",
        "current_step": "execution_validation",
        "stream_events": [f"✔ Execution Verification: {val_report.overall_status} (Exit code: {exec_report.exit_code})"]
    }


from backend.memory.project_memory_service import global_project_memory_service
from backend.execution.models import MemoryRecord


from backend.execution.failure_classifier import classify_test_failure, FailureCategory
from backend.agents.repair_agent import global_repair_agent
from backend.quality.version_manager import global_version_manager
from backend.quality.gates import evaluate_quality_gates, GateStatus

MAX_REPAIR_ATTEMPTS = int(os.getenv("MAX_REPAIR_ATTEMPTS", 3))


async def debug_node(state: ProjectState) -> dict:
    _logger.info("✔ [12/14] Diagnostic Agent analyzing failure evidence & root causes...")
    _fire_lifecycle("agent_started", "debug")
    iteration = state.get("iteration", 0) + 1
    max_iterations = state.get("max_iterations", MAX_REPAIR_ATTEMPTS)

    files_map = dict(state.get("files", {}) or {})
    exec_res = dict(state.get("execution_results", {}) or {})
    fixes = list(state.get("fixes", []) or [])
    existing_errors = list(state.get("errors", []) or [])
    existing_causes = list(state.get("root_causes", []) or [])

    # Structured Diagnosis via DiagnosticAgent
    diag_res = global_diagnostic_agent.diagnose_failure(
        execution_report=exec_res,
        files_manifest=files_map,
        architecture_spec=state.get("architecture"),
        previous_fixes=fixes
    )
    diag_dict = diag_res.model_dump()

    # Generate targeted RepairPlan via RepairAgent
    repair_plan = global_repair_agent.generate_repair_plan(
        root_cause=diag_res.root_cause,
        affected_files=diag_res.affected_files,
        classified_failures=[{"message": exec_res.get("stderr", "")}],
        files_map=files_map
    )

    debug_res = global_debug_agent.diagnose_and_repair(dict(state))

    try:
        global_project_memory_service.store_memory(MemoryRecord(
            project_id=str(state.get("project_name", state.get("project_id", "default_project"))),
            memory_type="FAILURE",
            content=diag_res.root_cause,
            error_type=diag_res.error_category,
            technology=str(state.get("technology_stack", "python")),
            files=diag_res.affected_files,
            root_cause=diag_res.root_cause,
            fix=json.dumps([p.model_dump() for p in repair_plan.patches]),
            result="FAIL",
            confidence=diag_res.confidence
        ))
    except Exception as e:
        _logger.warning(f"Memory store failed safely in debug_node: {e}")

    _fire_lifecycle("agent_completed", "debug")
    return {
        "iteration": iteration,
        "max_iterations": max_iterations,
        "error_category": diag_res.error_category,
        "diagnostic_result": diag_dict,
        "fixes": fixes + [debug_res.model_dump()],
        "errors": existing_errors + [diag_res.root_cause],
        "root_causes": existing_causes + [diag_res.root_cause],
        "repair_status": f"DIAGNOSED_ATTEMPT_{iteration}",
        "current_step": "debug",
        "stream_events": [f"⚠️ Diagnostic Agent: ({diag_res.error_category}) -> {diag_res.root_cause}"]
    }


async def patch_node(state: ProjectState) -> dict:
    _logger.info("✔ Applying targeted patch and taking version snapshot...")
    _fire_lifecycle("agent_started", "patch")
    fixes = state.get("fixes", []) or []
    files_map = dict(state.get("files", {}) or {})
    proj_path_str = state.get("project_path", "")
    project_id = str(state.get("project_name", state.get("project_id", "default_project")))
    target_dir = Path(proj_path_str).resolve() if proj_path_str else None

    # Take Snapshot before applying repair
    global_version_manager.create_snapshot(
        project_id=project_id,
        files_map=files_map,
        repair_reason="Pre-patch snapshot",
        test_result=state.get("test_results", {})
    )

    if not fixes:
        _fire_lifecycle("agent_completed", "patch")
        return {"current_step": "patch"}

    latest_fix = fixes[-1]
    changes = latest_fix.get("changes", {})
    modified_files = []

    for rel_path, new_content in changes.items():
        clean_rel = rel_path.replace("\\", "/").lstrip("/")
        if clean_rel.startswith("/") or clean_rel.startswith("\\"):
            _logger.warning(f"Path traversal rejected in patch_node: {rel_path}")
            continue

        patch_op = global_repair_agent.generate_repair_plan(
            root_cause=latest_fix.get("root_cause", "Patch fix"),
            affected_files=[clean_rel],
            classified_failures=[],
            files_map=files_map
        ).patches[0] if latest_fix.get("root_cause") else None

        if target_dir:
            dest_path = (target_dir / clean_rel).resolve()
            if not str(dest_path).startswith(str(target_dir)):
                _logger.warning(f"Path traversal rejected in patch_node: {rel_path}")
                continue
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(new_content, encoding="utf-8")

        files_map[clean_rel] = new_content
        modified_files.append(clean_rel)

    attempt = state.get("repair_attempt", state.get("iteration", 0)) + 1

    _fire_lifecycle("agent_completed", "patch")
    return {
        "files": files_map,
        "repair_attempt": attempt,
        "iteration": attempt,
        "repair_status": f"PATCHED_ATTEMPT_{attempt}",
        "current_step": "patch",
        "stream_events": [f"✔ Applied targeted patch (Attempt {attempt}) to {len(modified_files)} file(s): {modified_files}"]
    }


def restore_file_backups(state: ProjectState) -> dict:
    """
    Restores modified files on disk and in ProjectState["files"] from ProjectState["file_backups"].
    """
    project_id = str(state.get("project_name", state.get("project_id", "default_project")))
    files_map = dict(state.get("files", {}) or {})
    proj_path_str = state.get("project_path", "")
    target_dir = Path(proj_path_str).resolve() if proj_path_str else None

    restored_ver = global_version_manager.rollback(project_id, files_map, project_dir=target_dir)

    return {
        "files": files_map,
        "current_step": "rollback",
        "stream_events": [f"✔ Restored project to version '{restored_ver.version_id if restored_ver else 'snapshot'}'"]
    }


from backend.exporter.gate import global_export_gate


def route_after_testing(state: ProjectState) -> str:
    exec_res = state.get("execution_results", {}) or {}
    test_res = state.get("test_results", {}) or {}
    status = state.get("status", "")
    quality_report = state.get("quality_report")

    exit_code = exec_res.get("exit_code", -1)
    is_test_success = test_res.get("success", False)

    q_status = getattr(quality_report, "overall_status", None) if quality_report else None
    if isinstance(quality_report, dict):
        q_status = quality_report.get("overall_status")

    if exit_code == 0 and is_test_success and q_status in (None, "PASS", "WARN", GateStatus.PASS, GateStatus.WARN):
        global_export_gate.mark_verified(state)
        return "packaging"

    if status in ["UNSUPPORTED", "SECURITY_ERROR", "FAILED_REPEATED_ROOT_CAUSE", "FAILED_MAX_ITERATIONS"]:
        return END

    attempt = state.get("repair_attempt", state.get("iteration", 0))
    max_attempts = state.get("max_repair_attempts", state.get("max_iterations", MAX_REPAIR_ATTEMPTS))

    root_causes = state.get("root_causes", [])
    if global_version_manager.detect_repeated_failure(root_causes):
        state["status"] = "FAILED_REPEATED_ROOT_CAUSE"
        state["repair_status"] = "STOPPED_REPEATED_FAILURE"
        _logger.warning("Repeated repair failure detected. Manual intervention required.")
        return END

    if attempt >= max_attempts:
        state["status"] = "FAILED_MAX_ITERATIONS"
        state["repair_status"] = "STOPPED_MAX_ATTEMPTS"
        _logger.warning(f"Maximum repair attempts ({max_attempts}) reached. Stopping loop.")
        return END

    return "debug"


async def packaging_node(state: ProjectState) -> dict:
    _logger.info("✔ [13/14] Project Packaging Agent assembling export bundle...")
    _fire_lifecycle("agent_started", "packaging")
    plan_json = state.get("plan", {})
    arch_json = state.get("architecture", {})
    proj_name = plan_json.get("project_name", "AIForge Application") if isinstance(plan_json, dict) else "AIForge Application"

    with Timer() as timer:
        arch_md = packaging_agent.generate_architecture_md(proj_name, plan_json if isinstance(plan_json, dict) else {}, arch_json if isinstance(arch_json, dict) else {})
        api_md = packaging_agent.generate_api_docs_md(proj_name)

    agent_timers["packaging"] = timer.elapsed
    _fire_lifecycle("agent_completed", "packaging", duration=timer.elapsed)

    return {
        "architecture_report": arch_md,
        "api_documentation": api_md,
        "current_step": "packaging",
        "stream_events": ["✔ Project Bundled with Architecture & API Docs"]
    }


async def deployment_node(state: ProjectState) -> dict:
    _logger.info("✔ [14/14] Deployment Agent generating cloud manifests...")
    _fire_lifecycle("agent_started", "deployment")
    updated_state = await deployment_agent.run_async(dict(state))

    # Also run final project path assembly
    project_name = "AIForge Project"
    if isinstance(state.get("plan"), dict):
        project_name = state["plan"].get("project_name", "AIForge Project")

    project_dir, report = project_generator.generate_project_structure(project_name, state)
    report_dict = report.dict() if hasattr(report, "dict") else (report.to_dict() if hasattr(report, "to_dict") else str(report))

    _fire_lifecycle("agent_completed", "deployment")
    return {
        "project_path": str(project_dir),
        "validation_report": report_dict,
        "deployment_files": updated_state.get("deployment_files", {}),
        "deployment_guide": updated_state.get("deployment_guide", ""),
        "current_step": "deployment",
        "stream_events": ["🚀 AIForge Autonomous Pipeline Complete & Download Ready!"]
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
builder.add_node("build_validation", build_validation_node)
builder.add_node("dependency_manager", dependency_manager_node)
builder.add_node("security_scan", security_scan_node)
builder.add_node("performance", performance_node)
builder.add_node("execution_validation", execution_validation_node)
builder.add_node("debug", debug_node)
builder.add_node("patch", patch_node)
builder.add_node("packaging", packaging_node)
builder.add_node("deployment", deployment_node)

# Entry Point
builder.set_entry_point("planner")
builder.add_edge("planner", "architect")

# Parallel Branches
builder.add_edge("architect", "frontend")
builder.add_edge("architect", "backend")
builder.add_edge("architect", "database")

# Fan-in Assembly
builder.add_edge("frontend", "assembly")
builder.add_edge("backend", "assembly")
builder.add_edge("database", "assembly")

# Sequential Stage Progression
builder.add_edge("assembly", "reviewer")
builder.add_edge("reviewer", "documentation")
builder.add_edge("documentation", "build_validation")
builder.add_edge("build_validation", "dependency_manager")
builder.add_edge("dependency_manager", "security_scan")
builder.add_edge("security_scan", "performance")
builder.add_edge("performance", "execution_validation")
builder.add_edge("execution_validation", "testing")

# Self-Correction Loop Routing
builder.add_conditional_edges("testing", route_after_testing, {"packaging": "packaging", "debug": "debug", END: END})
builder.add_edge("debug", "patch")
builder.add_edge("patch", "execution_validation")

builder.add_edge("packaging", "deployment")
builder.add_edge("deployment", END)

parallel_graph = builder.compile()


