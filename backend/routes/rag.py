from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from backend.rag.rag_pipeline import RAGPipeline
from backend.rag.utils.loader import DocumentLoader
from backend.rag.utils.splitter import DocumentSplitter
from backend.rag.utils.vector_store import VectorStore


router = APIRouter(tags=["rag"])
legacy_router = APIRouter(prefix="/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
	question: str = Field(min_length=1)


class RAGUploadResponse(BaseModel):
	success: bool
	files: list[str]
	chunks_indexed: int
	message: str


rag_pipeline = RAGPipeline()
document_loader = DocumentLoader()
document_splitter = DocumentSplitter()
vector_store = VectorStore()


def _documents_dir() -> Path:
	return document_loader.documents_path


async def _upload_documents(files: list[UploadFile]):
	if not files:
		raise HTTPException(status_code=400, detail="At least one file is required.")

	documents_dir = _documents_dir()
	documents_dir.mkdir(parents=True, exist_ok=True)

	saved_files: list[Path] = []
	for uploaded_file in files:
		suffix = Path(uploaded_file.filename or "").suffix.lower()
		if suffix not in {".pdf", ".txt", ".md"}:
			raise HTTPException(status_code=400, detail=f"Unsupported file type: {uploaded_file.filename}")

		unique_name = f"{uuid4().hex}_{Path(uploaded_file.filename).name}"
		target_path = documents_dir / unique_name
		content = await uploaded_file.read()
		if not content:
			continue
		target_path.write_bytes(content)
		saved_files.append(target_path)

	if not saved_files:
		raise HTTPException(status_code=400, detail="No valid document content was uploaded.")

	loaded_documents = document_loader.load_paths(saved_files)
	if not loaded_documents:
		raise HTTPException(status_code=400, detail="Uploaded files could not be read as documents.")

	chunks = document_splitter.split_documents(loaded_documents)
	if not chunks:
		raise HTTPException(status_code=400, detail="No retrievable chunks were created from the uploaded documents.")

	vector_store.add_documents(chunks)

	return RAGUploadResponse(
		success=True,
		files=[path.name for path in saved_files],
		chunks_indexed=len(chunks),
		message="Document indexed successfully",
	)


@router.post("/upload", response_model=RAGUploadResponse)
async def upload_documents(files: list[UploadFile] = File(...)):
	return await _upload_documents(files)


@legacy_router.post("/upload", response_model=RAGUploadResponse)
async def legacy_upload_documents(files: list[UploadFile] = File(...)):
	return await _upload_documents(files)


@router.post("/query")
async def query_documents(request: RAGQueryRequest):
	result = rag_pipeline.query(request.question)
	return {
		"success": True,
		"question": request.question,
		"answer": result["answer"],
		"sources": [source["source"] for source in result["sources"]],
		"source_details": result["sources"],
	}


@legacy_router.post("/query")
async def legacy_query_documents(request: RAGQueryRequest):
	return await query_documents(request)
