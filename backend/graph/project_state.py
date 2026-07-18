from typing import Annotated, TypedDict


def _merge_errors(existing: str, new: str) -> str:
    """
    Reducer for the `error` field.

    Frontend, Backend and Database now run concurrently (same superstep).
    If more than one of them fails at the same time, LangGraph needs a
    reducer to combine both writes into a single value instead of raising
    an "Invalid update" conflict for a plain (non-annotated) field.
    """
    if not existing:
        return new
    if not new:
        return existing
    return f"{existing}\n{new}"


class ProjectState(TypedDict, total=False):
    """
    Shared state object passed between every node of the end-to-end
    "Project Generation" pipeline (Planner -> Architect -> [Frontend,
    Backend, Database run concurrently] -> Documentation -> Testing ->
    Reviewer -> GitHub).

    Every agent reads whatever fields it needs from this dict and writes
    its own output back into it, so the full history of the pipeline is
    always available to every later stage (e.g. the Reviewer Agent can
    see the Backend Agent's code, the GitHub Agent can see everything).
    """

    # Original user request, e.g. "Build an E-Commerce Website"
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

    # Populated if any stage raises an exception, so the pipeline can
    # fail gracefully instead of crashing the whole request. Uses a
    # reducer because Frontend/Backend/Database can fail concurrently.
    error: Annotated[str, _merge_errors]

