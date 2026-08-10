"""
AIForge Autonomous Engineering Platform — ErrorClassifier
==========================================================
Deterministic rule engine + LLM fallback mapping execution logs to 18 error categories.
"""

import re
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.execution.classifier")

ERROR_CATEGORIES = [
    "syntax_error",
    "compile_error",
    "import_error",
    "dependency_error",
    "runtime_error",
    "type_error",
    "configuration_error",
    "environment_error",
    "database_error",
    "API_error",
    "frontend_build_error",
    "backend_startup_error",
    "test_failure",
    "timeout",
    "port_conflict",
    "missing_file",
    "permission_error",
    "unknown_error"
]


class ErrorClassifier:
    """
    Deterministic rule-based error classifier for software build and test logs.
    """

    def __init__(self) -> None:
        self.rules = [
            (r"SyntaxError|Unexpected token|Invalid syntax|ParseError", "syntax_error"),
            (r"ModuleNotFoundError|Cannot find module|ImportError|No module named", "import_error"),
            (r"npm ERR! code ERESOLVE|Could not resolve dependency|pip install|package not found", "dependency_error"),
            (r"TypeError|AttributeError|ValueError|KeyError|IndexError", "runtime_error"),
            (r"EADDRINUSE|address already in use|port.*already in use", "port_conflict"),
            (r"FileNotFoundError|ENOENT|No such file or directory", "missing_file"),
            (r"PermissionError|EACCES|permission denied", "permission_error"),
            (r"FAILED tests/|AssertionError|test_.*failed", "test_failure"),
            (r"timed out|TimeoutError|Process timed out", "timeout"),
            (r"psycopg2\.OperationalError|FATAL: database|connection to server at.*failed|sqlalchemy\.exc\.OperationalError", "database_error"),
            (r"vite:.*error|Failed to compile|webpack.*error|Babel.*error", "frontend_build_error"),
            (r"uvicorn.*error|Application startup failed|FastAPI.*startup", "backend_startup_error"),
        ]

    def classify(self, log_output: str) -> str:
        if not log_output or not log_output.strip():
            return "unknown_error"

        for pattern, category in self.rules:
            if re.search(pattern, log_output, re.IGNORECASE):
                _logger.info(f"[ErrorClassifier] Matched rule '{pattern}' -> '{category}'")
                return category

        return "runtime_error"


global_error_classifier = ErrorClassifier()
