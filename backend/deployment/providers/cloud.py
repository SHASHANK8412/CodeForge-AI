"""Helpers shared by the cloud deployment providers (Vercel, Render, Neon)."""

import re
from typing import Any, Dict, Optional

import httpx


def slugify(project_id: str, max_len: int = 50) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", project_id.lower()).strip("-")
    return (slug or "aiforge-project")[:max_len].rstrip("-")


def load_project_files(project_id: str, config: Dict[str, Any]) -> Dict[str, str]:
    """Files supplied in the deploy config, else the generated project's files on disk."""
    if config.get("files"):
        return config["files"]
    from fastapi import HTTPException
    from backend.routes.export import _resolve_project_files

    try:
        return _resolve_project_files(project_id, None)
    except HTTPException:
        return {}


def subtree(files: Dict[str, str], prefix: str) -> Dict[str, str]:
    """Files under prefix/ with the prefix stripped; all files if nothing lives under it."""
    prefix = prefix.rstrip("/") + "/"
    inner = {path[len(prefix):]: body for path, body in files.items() if path.startswith(prefix)}
    return inner or files


def mask_database_url(url: Optional[str]) -> Optional[str]:
    """postgresql://user:secret@host/db -> postgresql://user:****@host/db"""
    if not url:
        return url
    return re.sub(r"(://[^:/@]+:)[^@]+@", r"\1****@", url)


def api_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"HTTP {response.status_code}: {response.text[:200]}"
    err = body.get("error") if isinstance(body, dict) else None
    if isinstance(err, dict):
        return err.get("message") or str(err)
    return (body.get("message") if isinstance(body, dict) else None) or f"HTTP {response.status_code}"


def failed(provider: str, message: str) -> Dict[str, Any]:
    return {"provider": provider, "status": "FAILED", "url": None, "message": message}


def not_configured(provider: str, display_name: str, token_env: str) -> Dict[str, Any]:
    return {
        "provider": provider,
        "status": "NOT_CONFIGURED",
        "url": None,
        "message": f"{display_name} deployment needs {token_env} set in the backend environment.",
    }
