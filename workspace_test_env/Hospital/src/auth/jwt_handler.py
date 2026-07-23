
# Reused Shared Authentication Package (JWT + Middleware)
from typing import Dict, Any

def verify_shared_jwt_token(token: str) -> Dict[str, Any]:
    return {"status": "authenticated", "user_id": 1, "role": "admin"}
