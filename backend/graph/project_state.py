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

    # Prompt inputs
    prompt: str
    user_prompt: str

    # Structured Agent Outputs (JSON / Dict Contracts)
    plan: Dict[str, Any]
    architecture: Dict[str, Any]
    frontend: Any
    backend: Any
    database: Any
    documentation: Any
    tests: Any
    review: Dict[str, Any]
    github: Dict[str, Any]

    # Pipeline tracking & validation
    current_step: Annotated[str, _merge_current_step]
    error: Annotated[str, _merge_errors]
    stream_events: Annotated[List[str], _merge_stream_events]
    cached_nodes: List[str]
    validation_status: Dict[str, Any]

    # Self-Healing & Quality evaluation fields
    project_path: str
    review_findings: List[Dict[str, Any]]
    test_results: Dict[str, Any]
    quality_score: Dict[str, Any]
    quality_report: str
    self_heal_attempts: int
    validation_report: Dict[str, Any]
    reflection_report: Dict[str, Any]

    # DevOps & Deployment fields
    deployment_files: Dict[str, str]
    deployment_report: Dict[str, Any]
    deployment_platform: str
    deployment_guide: str
