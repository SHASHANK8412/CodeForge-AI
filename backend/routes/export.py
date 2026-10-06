"""
AIForge Export & Download Router
================================
Provides production endpoints for ZIP packaging, documentation exports, and GitHub repository creation:
- GET & POST /api/export/zip/{projectId} -> Application/ZIP file download
- GET & POST /api/export/docs/{projectId} -> Text/Markdown README & documentation download
- POST /api/export/github -> GitHub API repository creation and file commit
"""

import io
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from backend.config import GENERATED_PROJECTS_DIR_NAME
from backend.exporter.zipper import global_project_zipper
from backend.exporter.gate import global_export_gate

_logger = logging.getLogger("aiforge.routes.export")

router = APIRouter(prefix="/api/export", tags=["export"])


class GitHubExportRequest(BaseModel):
    project_id: str = "default_project"
    repo_name: Optional[str] = None
    access_token: Optional[str] = None
    private: bool = False
    files: Optional[Dict[str, str]] = None
    state: Optional[Dict[str, Any]] = None


class ExportZipRequest(BaseModel):
    project_id: str = "default_project"
    files: Optional[Dict[str, str]] = None
    state: Optional[Dict[str, Any]] = None


GENERATED_ROOT = (Path(__file__).resolve().parent.parent.parent / GENERATED_PROJECTS_DIR_NAME).resolve()
_SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".venv", "venv", "dist", "build", ".pytest_cache"}


def _safe_project_dir(candidate: str) -> Optional[Path]:
    """Resolve a project directory, refusing anything outside generated_projects/."""
    if not candidate:
        return None
    try:
        path = Path(candidate)
        if not path.is_absolute():
            path = GENERATED_ROOT / path
        path = path.resolve()
    except (OSError, ValueError):
        return None
    if GENERATED_ROOT not in path.parents:
        return None
    return path if path.is_dir() else None


def _read_project_dir(project_dir: Path) -> Dict[str, str]:
    files: Dict[str, str] = {}
    for file_path in project_dir.rglob("*"):
        rel = file_path.relative_to(project_dir)
        if not file_path.is_file() or any(part in _SKIP_DIRS for part in rel.parts):
            continue
        try:
            files[rel.as_posix()] = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            _logger.warning("Skipping non-text file in export: %s", rel)
    return files


def _generation_record(project_id: str) -> Optional[Dict[str, Any]]:
    from backend.generation.store import global_generation_store
    return global_generation_store.get(project_id)


def _resolve_project_files(project_id: str, client_files: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Files for exactly this project: client payload, a generation's output, or its directory."""
    if client_files:
        return client_files

    record = _generation_record(project_id)
    if record:
        if record.get("status") != "completed":
            raise HTTPException(
                status_code=409,
                detail=f"Generation '{project_id}' is '{record.get('status')}'; only completed generations can be exported.",
            )
        project_dir = _safe_project_dir(record.get("project_path", ""))
    else:
        project_dir = _safe_project_dir(project_id)

    files = _read_project_dir(project_dir) if project_dir else {}
    if not files:
        raise HTTPException(status_code=404, detail=f"No generated files found for project '{project_id}'.")
    return files


def _validate_export_or_raise(projectId: str, files: Dict[str, str], state: Optional[Dict[str, Any]] = None):
    # The gate judges real pipeline results; without client-supplied state there is nothing
    # to judge, and inventing a passing state would make the gate meaningless.
    if not state:
        return
    val_res = global_export_gate.validate_state(dict(state))
    if not val_res.allowed:
        _logger.warning(f"Export gate rejected export for '{projectId}': {val_res.reason}")
        raise HTTPException(status_code=403, detail=val_res.reason)


@router.get("/zip/{projectId}")
@router.post("/zip")
async def export_project_zip(projectId: str = "default_project", payload: Optional[ExportZipRequest] = None):
    """
    Packages generated project files into a ZIP archive and returns application/zip stream for browser download.
    """
    client_files = payload.files if payload else None
    client_state = payload.state if payload else None
    files = _resolve_project_files(projectId, client_files)

    _validate_export_or_raise(projectId, files, client_state)

    if not files or len(files) == 0:
        raise HTTPException(status_code=404, detail=f"Project '{projectId}' files not found or empty.")


    try:
        safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in projectId]).strip("_") or "AIForge_Project"
        zip_bytes = global_project_zipper.create_zip_bytes(files, root_folder=safe_name)

        _logger.info(f"Export ZIP endpoint generated '{safe_name}.zip' ({len(zip_bytes)} bytes)")
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.zip"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        _logger.error(f"Failed to generate ZIP archive: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP package: {str(e)}")


@router.get("/docs/{projectId}")
@router.post("/docs")
async def export_project_docs(projectId: str = "default_project", payload: Optional[ExportZipRequest] = None):
    """
    Returns README.md and project documentation as a downloadable text/markdown file.
    """
    client_files = payload.files if payload else None
    client_state = payload.state if payload else None
    files = _resolve_project_files(projectId, client_files)

    _validate_export_or_raise(projectId, files, client_state)

    doc_content = files.get("README.md") or files.get("docs/README.md")

    if not doc_content:
        safe_title = projectId.replace("_", " ").title()
        doc_content = (
            f"# {safe_title} - Architectural Documentation\n\n"
            f"Autonomously generated by **AIForge V2 Autonomous AI Software Engineer Engine**.\n\n"
            f"## 🛠 Architecture\n"
            f"- **Frontend**: Decoupled React 18 Single-Page Application\n"
            f"- **Backend**: Async FastAPI REST API service with Pydantic validation\n"
            f"- **Database**: Normalized PostgreSQL 3NF Schema\n"
            f"- **Testing**: Pytest Integration Test Suite\n"
        )

    safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in projectId]).strip("_") or "Project"
    return Response(
        content=doc_content.encode("utf-8"),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}_README.md"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@router.post("/github")
async def export_to_github(req: GitHubExportRequest):
    """
    Authenticates with GitHub, creates a repository, commits generated project files, and returns repository URL.
    """
    files = _resolve_project_files(req.project_id, req.files)
    if not files or len(files) == 0:
        raise HTTPException(status_code=404, detail="No files found to commit to GitHub.")

    _validate_export_or_raise(req.project_id, files, req.state)


    # This route used to create an empty repo and report the files as pushed without pushing
    # anything; the publisher actually commits and pushes (and secret-scans first).
    from backend.github.github_api_service import GitHubAuthError, GitHubRepoExistsError
    from backend.github.publisher import SecurityViolationError, global_github_publisher

    try:
        result = global_github_publisher.publish_project(
            project_id=req.project_id,
            files_manifest=files,
            repo_name=req.repo_name,
            private=req.private,
            token=req.access_token,
        )
    except GitHubAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except GitHubRepoExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except SecurityViolationError as exc:
        raise HTTPException(status_code=400, detail={"error": "SECURITY_VIOLATION", "message": str(exc)})
    except Exception as exc:
        _logger.error(f"Failed to export to GitHub: {exc}")
        raise HTTPException(status_code=502, detail=f"GitHub export failed: {exc}")

    return {
        "success": True,
        "repository_name": result["repository"]["name"],
        "repository_url": result["repository"]["url"],
        "committed_files": len(files),
        "commit": result["commit"],
        "status": "COMMITTED_AND_PUSHED",
    }
