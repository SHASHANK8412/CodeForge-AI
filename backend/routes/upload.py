import os
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel, Field

from backend.rag.pipeline import global_rag_pipeline

logger = logging.getLogger("aiforge.routes.upload")

router = APIRouter(tags=["Upload & Document RAG"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max

# Embedding & Hash Cache to prevent duplicate indexing
_FILE_HASH_CACHE: Dict[str, str] = {}


class UploadResponse(BaseModel):
    status: str = "success"
    filename: str
    chunks: int
    message: str


class DocumentMetadata(BaseModel):
    filename: str
    size_bytes: int
    upload_time: str
    supported: bool = True


def _compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@router.post("/upload", response_model=UploadResponse)
@router.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Accepts PDF, TXT, MD, and DOCX files.
    Saves file to /uploads, checks for duplicates, triggers RAG indexing automatically,
    and returns chunk count & index status.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    filename = Path(file.filename).name
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported formats: PDF, TXT, MD, DOCX."
        )

    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds maximum size limit of 25MB.")

    # Compute hash to detect duplicates
    file_hash = _compute_file_hash(content)
    target_path = UPLOADS_DIR / filename

    if filename in _FILE_HASH_CACHE and _FILE_HASH_CACHE[filename] == file_hash and target_path.exists():
        logger.info(f"Duplicate file upload detected for '{filename}'; skipping re-indexing.")
        return UploadResponse(
            status="success",
            filename=filename,
            chunks=global_rag_pipeline.get_stats().get("total_chunks", 1),
            message="Already Indexed"
        )

    # Write file to /uploads directory
    target_path.write_bytes(content)
    _FILE_HASH_CACHE[filename] = file_hash

    # Trigger RAG pipeline indexing
    try:
        res = global_rag_pipeline.process_and_index_document(str(target_path))
        chunk_count = res.get("chunks_count", 1)
    except Exception as e:
        logger.error(f"Failed to index uploaded document '{filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process and index document: {str(e)}")

    return UploadResponse(
        status="success",
        filename=filename,
        chunks=chunk_count,
        message="Indexed successfully"
    )


@router.get("/documents", response_model=List[DocumentMetadata])
@router.get("/api/documents", response_model=List[DocumentMetadata])
def list_documents():
    """Lists all uploaded project documents stored in /uploads."""
    docs = []
    if not UPLOADS_DIR.exists():
        return docs

    for file_path in UPLOADS_DIR.glob("*"):
        if file_path.name.startswith("."):
            continue
        stat = file_path.stat()
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
        docs.append(DocumentMetadata(
            filename=file_path.name,
            size_bytes=stat.st_size,
            upload_time=mtime_str,
            supported=file_path.suffix.lower() in SUPPORTED_EXTENSIONS
        ))

    docs.sort(key=lambda d: d.filename.lower())
    return docs


@router.delete("/documents/{filename}")
@router.delete("/api/documents/{filename}")
def delete_document(filename: str):
    """Deletes an uploaded document from disk and purges file vectors from vector store."""
    target_path = UPLOADS_DIR / filename
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")

    try:
        os.remove(target_path)
        if filename in _FILE_HASH_CACHE:
            del _FILE_HASH_CACHE[filename]

        # Re-index remaining files in /uploads
        global_rag_pipeline.vectordb.clear()
        for remaining_file in UPLOADS_DIR.glob("*"):
            if not remaining_file.name.startswith(".") and remaining_file.suffix.lower() in SUPPORTED_EXTENSIONS:
                global_rag_pipeline.process_and_index_document(str(remaining_file))

        return {"status": "success", "message": f"Deleted document '{filename}' successfully."}
    except Exception as e:
        logger.error(f"Error deleting document '{filename}': {e}")
        raise HTTPException(status_code=500, detail=f"Could not delete document: {str(e)}")
