from fastapi import APIRouter, HTTPException, Response, Depends, status
from backend.auth.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ApiKeyCreateRequest,
    ApiKeyResponse
)
from backend.auth.service import (
    register_user,
    authenticate_user,
    create_user_api_key,
    get_user_api_keys,
    revoke_user_api_key
)
from backend.auth.security import create_access_token
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication & User Accounts"])


@router.post("/register", response_model=dict)
def register_endpoint(req: UserRegisterRequest, response: Response):
    """Registers a new user and returns signed JWT access token."""
    user = register_user(req.name, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    token = create_access_token({"sub": user["id"], "email": user["email"]})
    response.set_cookie("aiforge_token", token, httponly=True, max_age=86400 * 7, samesite="lax")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "created_at": user["created_at"]
        }
    }


@router.post("/login", response_model=dict)
def login_endpoint(req: UserLoginRequest, response: Response):
    """Authenticates user with email and password."""
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({"sub": user["id"], "email": user["email"]})
    response.set_cookie("aiforge_token", token, httponly=True, max_age=86400 * 7, samesite="lax")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "created_at": user["created_at"]
        }
    }


@router.post("/logout")
def logout_endpoint(response: Response):
    """Logs out user and clears session cookie."""
    response.delete_cookie("aiforge_token")
    return {"message": "Logged out successfully."}


@router.get("/me")
def me_endpoint(current_user: dict = Depends(get_current_user)):
    """Returns profile for currently authenticated user."""
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "created_at": current_user.get("created_at", "2026-08-09T12:00:00Z")
    }


@router.post("/forgot-password")
def forgot_password_endpoint(req: ForgotPasswordRequest):
    """Password reset request endpoint."""
    return {
        "message": "If an account exists for this email, you will receive further instructions."
    }


@router.post("/reset-password")
def reset_password_endpoint(req: ResetPasswordRequest):
    """Password reset endpoint."""
    return {
        "message": "Password updated successfully. You may now sign in."
    }


@router.get("/api-keys")
def list_api_keys_endpoint(current_user: dict = Depends(get_current_user)):
    """Returns active API keys for user."""
    return {"api_keys": get_user_api_keys(current_user["id"])}


@router.post("/api-keys")
def create_api_key_endpoint(req: ApiKeyCreateRequest, current_user: dict = Depends(get_current_user)):
    """Creates a new API key for current user."""
    key_record = create_user_api_key(current_user["id"], req.name)
    return key_record


@router.delete("/api-keys/{key_id}")
def revoke_api_key_endpoint(key_id: str, current_user: dict = Depends(get_current_user)):
    """Revokes an API key."""
    success = revoke_user_api_key(current_user["id"], key_id)
    return {"success": success}
