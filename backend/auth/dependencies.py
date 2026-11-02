import ipaddress
import os

from fastapi import Request, HTTPException, Depends, status
from starlette.requests import HTTPConnection
from typing import Optional
from backend.auth.security import decode_access_token
from backend.auth.service import get_user_by_id, DEFAULT_USER

# Authentication is required unless the operator opts into single-user local development:
#   AIFORGE_AUTH_MODE=local-dev   requests WITHOUT a token, from this machine only, act as the default user.
# It is refused when AIFORGE_ENV=production, and AIFORGE_REQUIRE_AUTH=1 still forces authentication.
LOCAL_DEV_MODE = "local-dev"
_LOOPBACK_HOSTS = {"localhost", "testclient"}  # "testclient" is Starlette's in-process test peer


def local_dev_auth_enabled() -> bool:
    if os.environ.get("AIFORGE_REQUIRE_AUTH", "").strip().lower() in ("1", "true", "yes"):
        return False
    if os.environ.get("AIFORGE_ENV", "").strip().lower() in ("production", "prod"):
        return False
    return os.environ.get("AIFORGE_AUTH_MODE", "").strip().lower() == LOCAL_DEV_MODE


def _is_loopback(conn: HTTPConnection) -> bool:
    host = conn.client.host if conn.client else ""
    if host in _LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _token_from(conn: HTTPConnection) -> Optional[str]:
    auth_header = conn.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip() or None
    return conn.cookies.get("aiforge_token") or None


def resolve_user(conn: HTTPConnection) -> dict:
    """
    The user behind a request (header `Authorization: Bearer <jwt>` or the `aiforge_token` cookie).
    Raises 401 for a missing, invalid or expired token; the only exception is a request with no token
    at all from this machine while local-dev mode is on, which acts as the default user.
    """
    token = _token_from(conn)
    if token:
        payload = decode_access_token(token)
        user = get_user_by_id(payload["sub"]) if payload and "sub" in payload else None
        if user:
            return user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.",
                            headers={"WWW-Authenticate": "Bearer"})
    if local_dev_auth_enabled() and _is_loopback(conn):
        return DEFAULT_USER
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.",
                        headers={"WWW-Authenticate": "Bearer"})


def get_current_user(request: Request) -> dict:
    """The authenticated user; the app-wide auth gate has usually resolved it already."""
    user = getattr(request.state, "user", None)
    return user if user is not None else resolve_user(request)


def get_optional_user(request: Request) -> Optional[dict]:
    try:
        return get_current_user(request)
    except HTTPException:
        return None
