"""
AIForge V2 — Day 14 Test Failure Classification
================================================
Classifies test failures and execution exceptions into structured failure categories.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    SYNTAX_ERROR = "SYNTAX_ERROR"
    TYPE_ERROR = "TYPE_ERROR"
    IMPORT_ERROR = "IMPORT_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    API_ERROR = "API_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    LOGIC_ERROR = "LOGIC_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    UI_ERROR = "UI_ERROR"
    TEST_ERROR = "TEST_ERROR"
    UNKNOWN = "UNKNOWN"


class ClassifiedFailure(BaseModel):
    test: str = Field(default="unknown_test", description="Test function or context name")
    category: FailureCategory = FailureCategory.UNKNOWN
    file: Optional[str] = Field(default=None, description="Affected source or test file")
    message: str = Field(..., description="Error message / exception trace")
    line: Optional[int] = Field(default=None, description="Line number if available")


def classify_test_failure(error_msg: str, test_name: str = "test_execution", file_hint: Optional[str] = None) -> ClassifiedFailure:
    """
    Analyzes error message, stack trace, or stderr to classify into FailureCategory.
    """
    msg_lower = error_msg.lower()

    if "syntaxerror" in msg_lower or "invalid syntax" in msg_lower or "unexpected token" in msg_lower:
        cat = FailureCategory.SYNTAX_ERROR
    elif "typeerror" in msg_lower or "cannot read property" in msg_lower or "is not a function" in msg_lower:
        cat = FailureCategory.TYPE_ERROR
    elif "importerror" in msg_lower or "modulenotfounderror" in msg_lower or "cannot find module" in msg_lower:
        cat = FailureCategory.IMPORT_ERROR
    elif "pip install" in msg_lower or "npm install" in msg_lower or "requirement" in msg_lower:
        cat = FailureCategory.DEPENDENCY_ERROR
    elif "404" in msg_lower or "500" in msg_lower or "route" in msg_lower or "api" in msg_lower or "bad request" in msg_lower:
        cat = FailureCategory.API_ERROR
    elif "table" in msg_lower or "sqlite" in msg_lower or "postgres" in msg_lower or "sqlalchemy" in msg_lower or "column" in msg_lower or "database" in msg_lower or "relation" in msg_lower:
        cat = FailureCategory.DATABASE_ERROR
    elif "auth" in msg_lower or "jwt" in msg_lower or "401" in msg_lower or "403" in msg_lower or "unauthorized" in msg_lower:
        cat = FailureCategory.AUTHENTICATION_ERROR
    elif "env" in msg_lower or "config" in msg_lower or "setting" in msg_lower:
        cat = FailureCategory.CONFIGURATION_ERROR
    elif "react" in msg_lower or "dom" in msg_lower or "css" in msg_lower or "component" in msg_lower:
        cat = FailureCategory.UI_ERROR
    elif "assertionerror" in msg_lower or "assert" in msg_lower:
        cat = FailureCategory.LOGIC_ERROR
    else:
        cat = FailureCategory.UNKNOWN

    return ClassifiedFailure(
        test=test_name,
        category=cat,
        file=file_hint,
        message=error_msg[:500] if len(error_msg) > 500 else error_msg
    )
