"""
Who may work on a generation (project) record. One rule, used by the app-wide project guard and by the
routes that resolve a project's folder (`backend.evolution.routes._project_dir`, generation routes).
"""

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from backend.auth.dependencies import local_dev_auth_enabled

# Records written before generations carried a real owner. In single-user local development they belong
# to whoever runs the app; with authentication enforced they belong to nobody, so nobody can open them.
LEGACY_OWNERS = ("default", "demo_user", "", None)


def user_id_of(user: Optional[Dict[str, Any]]) -> str:
    user = user or {}
    return str(user.get("id") or user.get("user_id") or "")


def may_access(user: Optional[Dict[str, Any]], record: Dict[str, Any]) -> bool:
    owner = record.get("user_id")
    uid = user_id_of(user)
    if uid and owner == uid:
        return True
    return owner in LEGACY_OWNERS and local_dev_auth_enabled()


def find_generation(project: str) -> Optional[Dict[str, Any]]:
    """The generation with this id, or the one whose project folder has this name."""
    from backend.generation.store import global_generation_store
    rec = global_generation_store.get(project)
    if rec is not None:
        return rec
    for candidate in global_generation_store.list_all():
        if Path(str(candidate.get("project_path") or "")).name == project:
            return candidate
    return None


def owned_project_folder(project: str, user: Optional[Dict[str, Any]]) -> Path:
    """
    The folder of a project (generation id or folder name) the user may access, resolved inside
    generated_projects/. A project id is never joined onto a path: 404 if it is not a known project, 403 if
    it is someone else's.
    """
    from backend.routes.export import _safe_project_dir
    from backend.security.paths import is_plain_filename
    if not is_plain_filename(project or "") or ".." in project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    rec = find_generation(project)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
    if not may_access(user, rec):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this project.")
    folder = _safe_project_dir(rec.get("project_path") or "")
    if folder is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "The project's folder is missing.")
    return folder
