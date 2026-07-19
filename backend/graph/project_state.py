from typing import Annotated, TypedDict


def _merge_errors(existing: str, new: str) -> str:
    """
    Reducer for the `error` field.

    If more than one agent fails at the same time, LangGraph needs a
    reducer to combine both writes into a single value instead of raising
    an "Invalid update" conflict for a plain (non-annotated) field.
    """
    if not existing:
        return new
    if not new:
        return existing
    return f"{existing}\n{new}"


def _merge_current_step(existing: str, new: str) -> str:
    """
    Reducer for the `current_step` field.

    If multiple parallel nodes write to `current_step` concurrently,
    this reducer will gracefully select the latest write.
    """
    return new or existing


class ProjectState(TypedDict, total=False):
    """
    Shared state object passed between every node of the end-to-end
    "Project Generation" pipeline (Planner -> Architect -> Frontend ->
    Backend -> Database -> Reviewer -> Testing -> Documentation).

    Every agent reads whatever fields it needs from this dict and writes
    its own output back into it, so the full history of the pipeline is
    always available to every later stage.
    """

    # Prompt inputs
    prompt: str
    user_prompt: str

    # Planner Agent output
    plan: str

    # Architect Agent output
    architecture: str

    # Frontend Agent output (React / Vite / Tailwind source)
    frontend: str

    # Backend Agent output (FastAPI source)
    backend: str

    # Database Agent output (SQL schema)
    database: str

    # Documentation Agent output (README / API docs)
    documentation: str

    # Testing Agent output (pytest / unit / integration tests)
    tests: str

    # Reviewer Agent output (code review + suggested fixes)
    review: str

    # GitHub Agent output (folder structure, commit message, checklist)
    github: str

    # Populated to keep track of the current active pipeline step
    current_step: Annotated[str, _merge_current_step]

    # Populated if any stage raises an exception, so the pipeline can
    # fail gracefully instead of crashing the whole request.
    error: Annotated[str, _merge_errors]

    # Day 23 Self-Healing & Quality evaluation fields
    project_path: str
    review_findings: list[dict]
    test_results: dict
    quality_score: dict
    quality_report: str
    self_heal_attempts: int
    validation_report: dict
    reflection_report: dict

