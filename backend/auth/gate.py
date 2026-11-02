"""
App-wide access control, applied in backend/main.py so no route can forget it.

1. AuthGateMiddleware authenticates every HTTP request before routing or body parsing, except the few
   public paths below; a request without valid credentials gets 401 (see dependencies.resolve_user).
2. enforce_project_access (an app-level dependency) runs once the route is known: any path parameter that
   names a project or generation must be a plain id (never a path), and a generation that exists must be
   one the user may access (403 otherwise).
"""

import json
import os

from fastapi import HTTPException, Request, status
from starlette.requests import HTTPConnection

from backend.auth.dependencies import get_current_user, resolve_user
from backend.auth.ownership import find_generation, may_access
from backend.security.paths import is_plain_filename

# Public by design: liveness, the sign-in flow, and (outside production) the API docs.
PUBLIC_PATHS = {
    ("GET", "/"), ("GET", "/health"), ("GET", "/api/health"),
    ("POST", "/api/auth/login"), ("POST", "/api/auth/register"), ("POST", "/api/auth/logout"),
    ("POST", "/api/auth/forgot-password"), ("POST", "/api/auth/reset-password"),
}
DOC_PATHS = {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}

# Path parameters that name a project (a generation id, or a generated project's folder name).
PROJECT_PARAMS = ("project_id", "generation_id", "gen_id", "projectId", "project_name")


def _production() -> bool:
    return os.environ.get("AIFORGE_ENV", "").strip().lower() in ("production", "prod")


def is_public(method: str, path: str) -> bool:
    path = path.rstrip("/") or "/"
    if method == "OPTIONS":  # CORS preflight carries no credentials; CORSMiddleware answers it
        return True
    if method in ("GET", "HEAD") and path in DOC_PATHS:
        return not _production()
    return (method if method != "HEAD" else "GET", path) in PUBLIC_PATHS


class AuthGateMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
        method = scope.get("method", "GET") if scope["type"] == "http" else "WEBSOCKET"
        if scope["type"] == "http" and is_public(method, scope.get("path", "/")):
            return await self.app(scope, receive, send)
        try:
            user = resolve_user(HTTPConnection(scope))
        except HTTPException as exc:
            if scope["type"] == "websocket":
                return await send({"type": "websocket.close", "code": 4401})
            body = json.dumps({"detail": exc.detail}).encode()
            headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
            headers += [(k.lower().encode(), v.encode()) for k, v in (exc.headers or {}).items()]
            await send({"type": "http.response.start", "status": exc.status_code, "headers": headers})
            return await send({"type": "http.response.body", "body": body})
        scope.setdefault("state", {})["user"] = user
        return await self.app(scope, receive, send)


def enforce_project_access(request: Request) -> None:
    # Path parameters and query strings both name projects (e.g. ?project_id=...); JSON bodies are checked
    # by the routes that use them (owned_project_folder).
    for source in (request.path_params, request.query_params):
        for name in PROJECT_PARAMS:
            value = source.get(name)
            if value is None:
                continue
            if not is_plain_filename(value) or ".." in value:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found.")
            # Some routes take the generated folder's name rather than the generation id.
            rec = find_generation(value)
            if rec is not None and not may_access(get_current_user(request), rec):
                raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this project.")
