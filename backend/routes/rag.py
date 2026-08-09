"""
AIForge V2 — Day 13 FastAPI RAG API Routes
"""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from typing import List, Dict, Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.rag.pipeline import global_rag_pipeline
from backend.rag.ingestion import global_ingestion_pipeline
from backend.rag.models import GroundedResponse, GroundingStatus

router = APIRouter(tags=["rag"])
legacy_router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=1)


class RAGUploadResponse(BaseModel):
    success: bool
    files: list[str]
    chunks_indexed: int
    message: str


def _documents_dir() -> Path:
    return Path("data/documents")


async def _upload_documents(files: list[UploadFile]):
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    documents_dir = _documents_dir()
    documents_dir.mkdir(parents=True, exist_ok=True)

    saved_files: list[Path] = []
    total_chunks = 0

    for uploaded_file in files:
        suffix = Path(uploaded_file.filename or "").suffix.lower()
        if suffix not in {".pdf", ".txt", ".md", ".docx"}:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {uploaded_file.filename}")

        unique_name = f"{uuid4().hex[:8]}_{Path(uploaded_file.filename).name}"
        target_path = documents_dir / unique_name
        content = await uploaded_file.read()
        if not content:
            continue
        target_path.write_bytes(content)
        saved_files.append(target_path)

        res = global_rag_pipeline.process_and_index_document(str(target_path))
        total_chunks += res.get("chunks_count", 0)

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid document content was uploaded.")

    return RAGUploadResponse(
        success=True,
        files=[path.name for path in saved_files],
        chunks_indexed=total_chunks,
        message="Document indexed successfully into Production RAG pipeline"
    )


@router.post("/upload", response_model=RAGUploadResponse)
async def upload_documents(files: list[UploadFile] = File(...)):
    return await _upload_documents(files)


@legacy_router.post("/upload", response_model=RAGUploadResponse)
async def legacy_upload_documents(files: list[UploadFile] = File(...)):
    return await _upload_documents(files)


@router.post("/query")
async def query_documents(request: RAGQueryRequest):
    grounded_res = global_rag_pipeline.query_grounded_answer(request.question)
    return {
        "success": True,
        "question": request.question,
        "answer": grounded_res.answer,
        "grounding_status": grounded_res.grounding_status.value,
        "citations": [c.dict() for c in grounded_res.citations],
        "unsupported_claims": grounded_res.unsupported_claims,
        "confidence_score": grounded_res.confidence_score
    }


@legacy_router.post("/query")
async def legacy_query_documents(request: RAGQueryRequest):
    return await query_documents(request)
