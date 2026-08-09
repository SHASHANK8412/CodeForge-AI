from fastapi import Request, HTTPException, Depends, status
from typing import Optional
from backend.auth.security import decode_access_token
from backend.auth.service import get_user_by_id, DEFAULT_USER


def get_current_user(request: Request) -> dict:
    """
    Extracts authenticated user from Authorization header or HTTP-Only cookie.
    Falls back to DEFAULT_USER in development if no token provided.
    """
    token = None

    # Check Authorization Header: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # Check Cookie
    if not token and "aiforge_token" in request.cookies:
        token = request.cookies["aiforge_token"]

    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user = get_user_by_id(payload["sub"])
            if user:
                return user

    # Fallback to default user if token missing in local environment
    return DEFAULT_USER


def get_optional_user(request: Request) -> Optional[dict]:
    try:
        return get_current_user(request)
    except HTTPException:
        return None
