"""
AIForge V2 – Validation & Exception Framework Generator
======================================================
Generates custom HTTP exception classes and Pydantic validation models.
"""

from typing import Dict, Any


class FastAPIValidationGenerator:

    def generate_exceptions_code(self) -> str:
        return """from fastapi import HTTPException, status

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class ResourceNotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
"""


global_validation_generator = FastAPIValidationGenerator()
