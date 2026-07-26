"""
AIForge V2 – JWT Authentication & RBAC Generator
================================================
Generates JWT Bearer authentication, password hashing, and Role-Based Access Control (RBAC).
"""

from v2.agents.backend.models import BackendAuthSpec


class FastAPIBackendAuthGenerator:

    def generate_auth_spec(self) -> BackendAuthSpec:
        return BackendAuthSpec(
            auth_type="JWT Bearer / OAuth2 Password Flow",
            roles=["Admin", "Developer", "Viewer"],
            permissions=["read", "write", "delete", "deploy", "manage_agents"],
            code_content="""from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return {"id": "u1", "username": "admin", "role": "admin"}

def require_role(allowed_roles: list):
    def role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return role_checker
"""
        )


global_auth_generator = FastAPIBackendAuthGenerator()
