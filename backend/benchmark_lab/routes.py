"""
AIForge Benchmark Lab — FastAPI Routes
======================================
REST API endpoints for tasks, dynamic model discovery, configuration management,
controlled benchmark suite execution, comparison, and reporting.
"""

import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from backend.benchmark_lab.models import (
    BenchmarkTask,
    BenchmarkConfig,
    BenchmarkRun,
    EvaluationPriority,
    ComparisonWeights,
)
from backend.benchmark_lab.tasks.library import get_all_tasks, get_task_by_id
from backend.benchmark_lab.config_manager import global_config_manager
from backend.benchmark_lab.engine import global_benchmark_engine
from backend.benchmark_lab.comparator import global_config_comparator
from backend.benchmark_lab.recommender import global_benchmark_recommender
from backend.benchmark_lab.reporter import global_benchmark_reporter
from backend.benchmark_lab.store import global_benchmark_store

router = APIRouter(prefix="/api/benchmark-lab", tags=["AIForge Benchmark Lab"])


class CreateRunRequest(BaseModel):
    name: Optional[str] = None
    task_ids: List[str] = Field(default_factory=list)
    configuration_ids: List[str] = Field(default_factory=list)
    repeated_runs: int = Field(default=1, ge=1, le=5)
    priority: EvaluationPriority = EvaluationPriority.BEST_OVERALL
    weights: Optional[ComparisonWeights] = None


class CompareRequest(BaseModel):
    run_id: str
    priority: Optional[EvaluationPriority] = None
    weights: Optional[ComparisonWeights] = None


# Background execution worker
async def _run_benchmark_background(run: BenchmarkRun):
    try:
        await global_benchmark_engine.execute_benchmark_suite(run)
        # Compute comparative analytics & ranking
        comparison = global_config_comparator.aggregate_and_compare(run)
        run.comparison = comparison
        # Generate recommendations
        all_runs = global_benchmark_store.list_runs()
        run.recommendations = global_benchmark_recommender.generate_recommendations(all_runs)
        global_benchmark_store.save_run(run)
    except Exception as e:
        run.status = "FAILED"
        run.error = str(e)
        run.completed_at = datetime.now(timezone.utc).isoformat()
        global_benchmark_store.save_run(run)


@router.get("/tasks", response_model=List[BenchmarkTask])
def list_tasks():
    """Lists all structured benchmark tasks in the task library."""
    return get_all_tasks()


@router.get("/tasks/{task_id}", response_model=BenchmarkTask)
def get_task(task_id: str):
    """Retrieves a specific benchmark task by ID."""
    t = get_task_by_id(task_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return t


@router.get("/models")
def list_models(force_refresh: bool = False):
    """Dynamically discovers local Ollama and configured models without exposing secrets."""
    return global_config_manager.discover_installed_models(force_refresh=force_refresh)


@router.get("/configurations", response_model=List[BenchmarkConfig])
def list_configurations():
    """Lists all registered benchmark configurations with live availability detection."""
    return global_config_manager.list_configurations()


@router.post("/configurations", response_model=BenchmarkConfig)
def create_configuration(config: BenchmarkConfig):
    """Creates or updates a benchmark configuration."""
    return global_config_manager.save_configuration(config)


@router.post("/runs", response_model=BenchmarkRun)
def start_benchmark_run(req: CreateRunRequest, background_tasks: BackgroundTasks):
    """
    Launches an automated benchmark run comparing selected tasks and configurations.
    """
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    run_name = req.name or f"Benchmark Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"

    # Resolve configurations
    configs: List[BenchmarkConfig] = []
    if req.configuration_ids:
        for cid in req.configuration_ids:
            cfg = global_config_manager.get_configuration(cid)
            if cfg:
                configs.append(cfg)
    else:
        # Default: first two available configurations
        all_configs = global_config_manager.list_configurations()
        avail = [c for c in all_configs if c.is_available]
        configs = avail[:2] if avail else all_configs[:2]

    # Resolve tasks
    selected_tasks = req.task_ids if req.task_ids else [t.id for t in get_all_tasks()[:5]]

    run = BenchmarkRun(
        id=run_id,
        name=run_name,
        created_at=datetime.now(timezone.utc).isoformat(),
        status="PENDING",
        configurations=configs,
        task_ids=selected_tasks,
        repeated_runs=req.repeated_runs,
        priority=req.priority,
        weights=req.weights
    )

    global_benchmark_store.save_run(run)
    background_tasks.add_task(_run_benchmark_background, run)

    return run


@router.get("/runs", response_model=List[BenchmarkRun])
def list_benchmark_runs():
    """Lists historical benchmark runs in reverse chronological order."""
    return global_benchmark_store.list_runs()


@router.get("/runs/{run_id}", response_model=BenchmarkRun)
def get_benchmark_run(run_id: str):
    """Retrieves live execution status and results for a benchmark run."""
    run = global_benchmark_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Benchmark run '{run_id}' not found.")
    return run


@router.post("/runs/{run_id}/cancel")
def cancel_benchmark_run(run_id: str):
    """Cancels a currently active benchmark run."""
    run = global_benchmark_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Benchmark run '{run_id}' not found.")

    global_benchmark_engine.cancel_run(run_id)
    run.status = "CANCELLED"
    global_benchmark_store.save_run(run)
    return {"status": "cancelled", "run_id": run_id}


@router.post("/compare")
def compare_configurations(req: CompareRequest):
    """
    Ranks configurations for a run based on customizable weights and priorities.
    """
    run = global_benchmark_store.get_run(req.run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Benchmark run '{req.run_id}' not found.")

    comparison = global_config_comparator.aggregate_and_compare(
        run=run,
        weights=req.weights,
        priority=req.priority
    )
    run.comparison = comparison
    global_benchmark_store.save_run(run)
    return comparison


@router.get("/runs/{run_id}/report")
def get_markdown_report(run_id: str):
    """Generates a comprehensive markdown evaluation report for the benchmark run."""
    run = global_benchmark_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Benchmark run '{run_id}' not found.")

    comparison = run.comparison or global_config_comparator.aggregate_and_compare(run)
    md_content = global_benchmark_reporter.generate_markdown_report(run, comparison)
    return {"run_id": run_id, "report_markdown": md_content}


@router.get("/runs/{run_id}/artifacts/{task_id}/{config_id}/{filename:path}")
def get_artifact(run_id: str, task_id: str, config_id: str, filename: str):
    """Safely retrieves generated artifact source code while strictly preventing path traversal."""
    content = global_benchmark_store.get_artifact_content(
        run_id=run_id,
        task_id=task_id,
        config_id=config_id,
        filename=filename
    )
    if content is None:
        raise HTTPException(status_code=404, detail="Artifact not found or access restricted.")
    return {"run_id": run_id, "task_id": task_id, "config_id": config_id, "filename": filename, "content": content}


@router.get("/recommendations")
def get_recommendations():
    """Generates evidence-backed recommendations synthesized from all historical runs."""
    all_runs = global_benchmark_store.list_runs()
    return global_benchmark_recommender.generate_recommendations(all_runs)
