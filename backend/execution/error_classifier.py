"""
AIForge Autonomous Engineering Platform — ErrorClassifier
==========================================================
Deterministic rule engine mapping execution logs to standardized failure categories.
"""

import re
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.execution.classifier")

STANDARD_CATEGORIES = {
    "IMPORT_ERROR": "Missing or unresolvable module import or package dependency",
    "SYNTAX_ERROR": "Source code syntax error, unexpected token, or malformed statement",
    "TYPE_ERROR": "Type mismatch, invalid attribute access, or parameter incompatibility",
    "RUNTIME_ERROR": "Unhandled exception, uninitialized variable, or index boundary failure",
    "TEST_ASSERTION_ERROR": "Unit or integration test assertion mismatch",
    "DEPENDENCY_ERROR": "Package resolution, version conflict, or installation failure",
    "CONFIGURATION_ERROR": "Invalid environment variable, missing config file, or settings error",
    "DATABASE_ERROR": "Database connection refused, table missing, or SQL migration failure",
    "API_ERROR": "Endpoint routing, HTTP status error, or payload serialization issue",
    "FRONTEND_BUILD_ERROR": "Vite/Webpack/Babel bundler failure or JSX compilation defect",
    "BACKEND_ERROR": "Server initialization, ASGI lifespan failure, or uncaught exception",
    "UNKNOWN_ERROR": "Unclassified execution defect",
}


class ErrorClassifier:
    """
    Deterministic rule-based error classifier for software build and test logs.
    """

    def __init__(self) -> None:
        self.rules = [
            (r"ModuleNotFoundError|Cannot find module|ImportError|No module named", "IMPORT_ERROR"),
            (r"SyntaxError|Unexpected token|Invalid syntax|ParseError", "SYNTAX_ERROR"),
            (r"TypeError|AttributeError", "TYPE_ERROR"),
            (r"npm ERR! code ERESOLVE|Could not resolve dependency|pip install|package not found|requirements\.txt", "DEPENDENCY_ERROR"),
            (r"psycopg2\.OperationalError|FATAL: database|connection to server at.*failed|sqlalchemy\.exc|OperationalError.*db", "DATABASE_ERROR"),
            (r"vite:.*error|Failed to compile|webpack.*error|Babel.*error|RollupError", "FRONTEND_BUILD_ERROR"),
            (r"uvicorn.*error|Application startup failed|FastAPI.*startup|Lifespan error", "BACKEND_ERROR"),
            (r"FAILED tests/|AssertionError|test_.*failed|assert False|assert 0 ==", "TEST_ASSERTION_ERROR"),
            (r"404 Not Found|500 Internal Server Error|Endpoint.*not found|HTTPException", "API_ERROR"),
            (r"FileNotFoundError|ENOENT|config\.json.*missing|\.env.*missing|ConfigurationError", "CONFIGURATION_ERROR"),
            (r"ValueError|KeyError|IndexError|ZeroDivisionError|RuntimeError", "RUNTIME_ERROR"),
        ]

    def classify(self, log_output: str) -> str:
        """Classifies error log into standard uppercase category."""
        if not log_output or not log_output.strip():
            return "UNKNOWN_ERROR"

        for pattern, category in self.rules:
            if re.search(pattern, log_output, re.IGNORECASE):
                _logger.info(f"[ErrorClassifier] Matched rule '{pattern}' -> '{category}'")
                return category

        return "RUNTIME_ERROR"

    def classify_detailed(self, log_output: str) -> Dict[str, Any]:
        """Provides structured classification with severity and description."""
        cat = self.classify(log_output)
        severity = "CRITICAL" if cat in ("SYNTAX_ERROR", "DATABASE_ERROR", "BACKEND_ERROR") else "HIGH" if cat in ("IMPORT_ERROR", "DEPENDENCY_ERROR") else "MEDIUM"
        return {
            "category": cat,
            "severity": severity,
            "description": STANDARD_CATEGORIES.get(cat, "Unclassified execution defect"),
        }


global_error_classifier = ErrorClassifier()

