from typing import Dict, Any, List, TypedDict, Optional


class WorkflowState(TypedDict, total=False):
    """
    Shared workflow state passed through the LangGraph multi-agent execution pipeline.
    """
    prompt: str
    session_id: str
    retrieved_context: str
    plan: Dict[str, Any]
    architecture: Dict[str, Any]
    frontend_code: Dict[str, str]
    backend_code: Dict[str, str]
    database_schema: str
    review: Dict[str, Any]
    tests: Dict[str, str]
    documentation: str
    project_files: Dict[str, str]
    errors: List[Dict[str, Any]]
    retry_count: Dict[str, int]
    logs: List[str]
    is_complete: bool
