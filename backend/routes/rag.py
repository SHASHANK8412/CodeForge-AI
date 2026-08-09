"""
AIForge V2 — Day 13 FastAPI RAG API Routes
"""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.rag.pipeline import global_rag_pipeline
from backend.rag.loader import DocumentLoader
from backend.rag.vector_store import global_vector_store
from backend.rag.query_analyzer import global_query_analyzer
from backend.rag.models import GroundedResponse, GroundingStatus

router = APIRouter(prefix="/api", tags=["rag"])
legacy_router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=1)
    project_id: str = "default_project"


class RAGDebugRequest(BaseModel):
    project_id: str = Field(default="default_project")
    agent: str = Field(default="backend")
    query: str = Field(min_length=1)


class RAGUploadResponse(BaseModel):
    success: bool
    project_id: str
    files: List[str]
    chunks_indexed: int
    message: str


def _documents_dir(project_id: str) -> Path:
    p = Path(f"data/projects/{project_id}/documents")
    p.mkdir(parents=True, exist_ok=True)
    return p


async def _upload_project_documents(project_id: str, files: List[UploadFile]) -> RAGUploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    documents_dir = _documents_dir(project_id)
    saved_files: List[Path] = []
    total_chunks = 0

    for uploaded_file in files:
        suffix = Path(uploaded_file.filename or "").suffix.lower()
        if suffix not in DocumentLoader.SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {uploaded_file.filename}")

        unique_name = f"{uuid4().hex[:8]}_{Path(uploaded_file.filename).name}"
        target_path = documents_dir / unique_name
        content = await uploaded_file.read()
        if not content:
            continue
        target_path.write_bytes(content)
        saved_files.append(target_path)

        res = global_rag_pipeline.process_and_index_document(str(target_path), project_id=project_id)
        total_chunks += res.get("chunks_count", 0)

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid document content was uploaded.")

    return RAGUploadResponse(
        success=True,
        project_id=project_id,
        files=[path.name for path in saved_files],
        chunks_indexed=total_chunks,
        message="Document indexed successfully into Project RAG pipeline"
    )


@router.post("/projects/{project_id}/rag/upload", response_model=RAGUploadResponse)
async def upload_project_documents(
    project_id: str,
    files: List[UploadFile] = File(...),
    user: dict = Depends(get_current_user)
):
    return await _upload_project_documents(project_id, files)


@router.delete("/projects/{project_id}/rag/documents/{document_id}")
def delete_project_document(
    project_id: str,
    document_id: str,
    user: dict = Depends(get_current_user)
):
    """Deletes document metadata and vector embeddings for project_id."""
    success = global_vector_store.delete_document(project_id, document_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document chunk '{document_id}' not found for project '{project_id}'.")
    return {"status": "success", "message": f"Deleted document '{document_id}' successfully."}


@router.get("/projects/{project_id}/rag/stats")
def get_project_rag_stats(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    """Returns RAG knowledge stats for project_id."""
    stats = global_vector_store.get_stats(project_id=project_id)
    return {"status": "success", **stats}


@router.post("/rag/debug")
def debug_rag_retrieval(
    req: RAGDebugRequest,
    user: dict = Depends(get_current_user)
):
    """Development/admin debug endpoint showing query analysis, retrieved chunks, and scores."""
    analysis = global_query_analyzer.analyze_query(req.query, req.agent)
    chunks = global_rag_pipeline.retrieve_context(req.query, top_k=5, project_id=req.project_id)

    results = []
    for c in chunks:
        results.append({
            "source": c.get("source", "unknown"),
            "score": c.get("score", 0.0),
            "content_preview": c.get("text", "")[:200],
            "retrieval_method": c.get("retrieval_method", "vector")
        })

    return {
        "status": "success",
        "analysis": analysis,
        "query": req.query,
        "results": results
    }


@router.post("/upload", response_model=RAGUploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    return await _upload_project_documents("default_project", files)


@legacy_router.post("/upload", response_model=RAGUploadResponse)
async def legacy_upload_documents(files: List[UploadFile] = File(...)):
    return await _upload_project_documents("default_project", files)


@router.post("/query")
async def query_documents(request: RAGQueryRequest):
    grounded_res = global_rag_pipeline.query_grounded_answer(request.question)
    return {
        "success": True,
        "question": request.question,
        "answer": grounded_res.answer,
        "grounding_status": grounded_res.grounding_status.value,
        "citations": [c.model_dump() for c in grounded_res.citations],
        "unsupported_claims": grounded_res.unsupported_claims,
        "confidence_score": grounded_res.confidence_score
    }


@legacy_router.post("/query")
async def legacy_query_documents(request: RAGQueryRequest):
    return await query_documents(request)
