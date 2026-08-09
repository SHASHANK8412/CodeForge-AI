"""
AIForge LangGraph Structured State Definition
=============================================
Every node reads whatever fields it needs from this dict and writes
its structured output back into its own section:
{
    "user_prompt": "",
    "plan": {},
    "architecture": {},
    "frontend": {},
    "backend": {},
    "database": {},
    "tests": {},
    "review": {},
    "documentation": {},
    "validation": {},
    "cached_nodes": [],
    "stream_events": []
}
"""

from typing import Annotated, TypedDict, Dict, Any, List, Optional


def _merge_errors(existing: str, new: str) -> str:
    if not existing:
        return new
    if not new:
        return existing
    return f"{existing}\n{new}"


def _merge_current_step(existing: str, new: str) -> str:
    return new or existing


def _merge_stream_events(existing: List[str], new: List[str]) -> List[str]:
    return (existing or []) + (new or [])


class ProjectState(TypedDict, total=False):
    """
    Shared structured state object passed between every node of the end-to-end
    parallel workflow pipeline.
    """

    # Prompt & Core Request inputs
    prompt: str
    user_prompt: str
    # Day 12 Context & Memory Extensions
    project_id: str
    generation_id: str
    technology_stack: Dict[str, Any]
    agent_outputs: Dict[str, Any]
    memory: List[Dict[str, Any]]
    review_results: Dict[str, Any]
    decisions: List[Dict[str, Any]]

    # Autonomous Engineering Project Metadata & Specs (Incremental Additions)
    project_name: str
    requirements: List[Any]
    project_spec: Dict[str, Any]
    architecture: Dict[str, Any]
    plan: Dict[str, Any]

    # File System & Code Representations
    files: Dict[str, str]
    frontend: Any
    backend: Any
    database: Any
    documentation: Any
    tests: Any
    dependencies: List[str]
    commands: List[str]

    # Structured Execution, Verification & Repair Tracking
    execution_results: Dict[str, Any]
    test_results: Dict[str, Any]
    errors_list: List[Dict[str, Any]]
    fixes: List[Dict[str, Any]]
    iteration: int
    max_iterations: int
    status: str

    # Review, GitHub & Assembly Metadata
    review: Dict[str, Any]
    github: Dict[str, Any]
    assembly_manifest: Dict[str, Any]
    duplicate_report: Dict[str, Any]

    # Pipeline tracking & validation
    current_step: Annotated[str, _merge_current_step]
    error: Annotated[str, _merge_errors]
    stream_events: Annotated[List[str], _merge_stream_events]
    cached_nodes: List[str]
    validation_status: Dict[str, Any]

    # Self-Healing & Quality evaluation fields
    project_path: str
    review_findings: List[Dict[str, Any]]
    quality_score: Dict[str, Any]
    quality_report: str
    self_heal_attempts: int
    validation_report: Dict[str, Any]
    reflection_report: Dict[str, Any]

    # Day 14 Repair Loop State
    repair_attempt: int
    max_repair_attempts: int
    findings: List[Dict[str, Any]]
    test_failures: List[Dict[str, Any]]
    root_causes: List[str]
    repairs: List[Dict[str, Any]]
    snapshots: List[Dict[str, Any]]
    repair_status: str

    # DevOps & Deployment fields
    deployment_files: Dict[str, str]
    deployment_report: Dict[str, Any]
    deployment_platform: str
    deployment_guide: str

