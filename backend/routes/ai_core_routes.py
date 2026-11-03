"""
AIForge Next-Gen AI Agent Core — REST API Routes
=================================================
Endpoints:
- POST /api/agents/run
- GET /api/agents/runs
- GET /api/agents/runs/{run_id}
- GET /api/models
- GET /api/tools
- POST /api/tools/execute
- GET /api/memory
- POST /api/memory/store
- POST /api/memory/search
- GET /api/rag/documents
- POST /api/rag/upload
- POST /api/rag/search
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.ai_core.agent_runtime import global_agent_runtime, AgentMode, AgentRunRecord
from backend.ai_core.model_provider import global_model_provider
from backend.ai_core.tool_registry import WORKSPACE_TOOLS, global_tool_registry
from backend.auth.dependencies import get_current_user
from backend.auth.ownership import user_id_of
from backend.evolution.routes import _project_dir
from backend.ai_core.agent_memory import global_memory_manager
from backend.ai_core.rag_engine import global_rag_engine

router = APIRouter(prefix="/api/ai-core", tags=["AIForge Next-Gen AI Core"])


class RunAgentPayload(BaseModel):
    prompt: str
    mode: Optional[AgentMode] = AgentMode.AGENT
    model_id: Optional[str] = None          # an installed Ollama model; None lets the model router choose
    project_id: Optional[str] = None


class ExecuteToolPayload(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    user_confirmed: bool = False
    # The generation whose folder file_reader / file_search are confined to.
    project_id: Optional[str] = None


class StoreMemoryPayload(BaseModel):
    key: str
    content: str
    memory_type: Optional[str] = "LONG_TERM"
    project_id: Optional[str] = None


class SearchMemoryPayload(BaseModel):
    query: str
    project_id: Optional[str] = None
    limit: Optional[int] = 5


class IngestDocPayload(BaseModel):
    filename: str
    content: str
    content_type: Optional[str] = "markdown"
    project_id: Optional[str] = None


class SearchRAGPayload(BaseModel):
    query: str
    project_id: Optional[str] = None
    limit: Optional[int] = 4


@router.post("/agents/run", status_code=status.HTTP_201_CREATED)
def run_agent(payload: RunAgentPayload, user: dict = Depends(get_current_user)):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    run = global_agent_runtime.execute_agent(
        prompt=payload.prompt,
        user_id=user_id_of(user),
        mode=payload.mode or AgentMode.AGENT,
        model_id=payload.model_id,
        project_id=payload.project_id,
    )
    if run.status == "FAILED":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=run.error)
    return {
        "success": True,
        "run": run.model_dump()
    }


@router.get("/agents/runs")
def list_agent_runs(project_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    runs = global_agent_runtime.list_runs(user_id_of(user), project_id=project_id)
    return {
        "success": True,
        "count": len(runs),
        "runs": [r.model_dump() for r in runs]
    }


@router.get("/agents/runs/{run_id}")
def get_agent_run(run_id: str, user: dict = Depends(get_current_user)):
    r = global_agent_runtime.get_run(run_id, user_id_of(user))
    if not r:
        raise HTTPException(status_code=404, detail=f"Agent run '{run_id}' not found")
    return {
        "success": True,
        "run": r.model_dump()
    }


@router.get("/models")
def list_models():
    models = global_model_provider.list_models()
    return {
        "success": True,
        "count": len(models),
        "models": [m.model_dump() for m in models]
    }


@router.get("/tools")
def list_tools():
    tools = global_tool_registry.list_tools()
    return {
        "success": True,
        "count": len(tools),
        "tools": [t.model_dump() for t in tools]
    }


@router.post("/tools/execute")
def execute_tool(payload: ExecuteToolPayload, user: dict = Depends(get_current_user)):
    workspace = None
    if payload.tool_name in WORKSPACE_TOOLS:
        if not payload.project_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"'{payload.tool_name}' needs a project_id.")
        workspace = _project_dir(payload.project_id, user)
    res = global_tool_registry.execute_tool(
        name=payload.tool_name,
        arguments=payload.arguments,
        user_confirmed=payload.user_confirmed,
        workspace=workspace
    )
    if res.get("status") == "DENIED":
        raise HTTPException(status.HTTP_403_FORBIDDEN, res.get("error"))
    return res


@router.get("/memory")
def list_memories(user: dict = Depends(get_current_user)):
    mems = global_memory_manager.list_memories(user_id_of(user))
    return {
        "success": True,
        "count": len(mems),
        "memories": [m.model_dump() for m in mems]
    }


@router.post("/memory/store", status_code=status.HTTP_201_CREATED)
def store_memory(payload: StoreMemoryPayload, user: dict = Depends(get_current_user)):
    rec = global_memory_manager.store(
        key=payload.key,
        content=payload.content,
        user_id=user_id_of(user),
        memory_type=payload.memory_type or "LONG_TERM",
        project_id=payload.project_id
    )
    return {
        "success": True,
        "memory": rec.model_dump()
    }


@router.post("/memory/search")
def search_memory(payload: SearchMemoryPayload, user: dict = Depends(get_current_user)):
    results = global_memory_manager.search(
        query=payload.query,
        user_id=user_id_of(user),
        project_id=payload.project_id,
        limit=payload.limit or 5
    )
    return {
        "success": True,
        "count": len(results),
        "results": [r.model_dump() for r in results]
    }


@router.get("/rag/documents")
def list_rag_documents(user: dict = Depends(get_current_user)):
    docs = global_rag_engine.list_documents(user_id_of(user))
    return {
        "success": True,
        "count": len(docs),
        "documents": [d.model_dump() for d in docs]
    }


@router.post("/rag/upload", status_code=status.HTTP_201_CREATED)
def upload_rag_document(payload: IngestDocPayload, user: dict = Depends(get_current_user)):
    doc = global_rag_engine.ingest_document(
        filename=payload.filename,
        content=payload.content,
        user_id=user_id_of(user),
        content_type=payload.content_type or "markdown",
        project_id=payload.project_id,
    )
    return {
        "success": True,
        "document": doc.model_dump()
    }


@router.post("/rag/search")
def search_rag(payload: SearchRAGPayload, user: dict = Depends(get_current_user)):
    chunks = global_rag_engine.search(
        query=payload.query,
        limit=payload.limit or 4,
        project_id=payload.project_id,
        user_id=user_id_of(user),
    )
    return {
        "success": True,
        "count": len(chunks),
        "results": [c.model_dump() for c in chunks]
    }
