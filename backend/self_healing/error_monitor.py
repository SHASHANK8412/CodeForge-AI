"""
AIForge Error Monitor
=====================
Monitors application and pipeline failure sources (API, tests, build, runtime, DB, Docker, CI/CD, dependencies, performance, security).
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.self_healing.monitor")


class FailureSource:
    API_FAILURE = "API"
    TEST_FAILURE = "Test"
    BUILD_FAILURE = "Build"
    RUNTIME_EXCEPTION = "Runtime"
    DATABASE_ERROR = "Database"
    DOCKER_FAILURE = "Docker"
    CICD_FAILURE = "CI/CD"
    DEPENDENCY_CONFLICT = "Dependency"
    PERFORMANCE_REGRESSION = "Performance"
    SECURITY_SCAN_FAILURE = "Security"

    ALL_SOURCES = [
        API_FAILURE, TEST_FAILURE, BUILD_FAILURE, RUNTIME_EXCEPTION,
        DATABASE_ERROR, DOCKER_FAILURE, CICD_FAILURE, DEPENDENCY_CONFLICT,
        PERFORMANCE_REGRESSION, SECURITY_SCAN_FAILURE
    ]


class ErrorMonitor:
    """
    Captures failure events across 10 system sources and maintains error history.
    """

    def __init__(self) -> None:
        self.error_reports: List[Dict[str, Any]] = [
            {
                "error_id": "err_001",
                "error_type": FailureSource.DATABASE_ERROR,
                "severity": "High",
                "file": "database.py",
                "line": 84,
                "message": "Connection timeout: pool exhausted",
                "timestamp": time.time() - 3600,
                "status": "DETECTED"
            },
            {
                "error_id": "err_002",
                "error_type": FailureSource.API_FAILURE,
                "severity": "Medium",
                "file": "src/api/auth.py",
                "line": 42,
                "message": "HTTP 500 Internal Server Error on /api/v1/login",
                "timestamp": time.time() - 1800,
                "status": "RESOLVED"
            }
        ]

    def record_error(
        self,
        error_type: str,
        message: str,
        file: str = "main.py",
        line: int = 1,
        severity: str = "High",
        stack_trace: str = ""
    ) -> Dict[str, Any]:
        err_id = f"err_{int(time.time() * 1000)}"
        report = {
            "error_id": err_id,
            "error_type": error_type,
            "severity": severity,
            "file": file,
            "line": line,
            "message": message,
            "stack_trace": stack_trace,
            "timestamp": time.time(),
            "status": "DETECTED"
        }
        self.error_reports.insert(0, report)
        _logger.info(f"ErrorMonitor: [{error_type}:{severity}] Recorded error in '{file}:L{line}' - {message}")
        return report

    def get_errors(
        self,
        error_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        results = self.error_reports
        if error_type:
            results = [e for e in results if e["error_type"].lower() == error_type.lower()]
        if status:
            results = [e for e in results if e["status"].lower() == status.lower()]
        return results[:limit]

    def update_error_status(self, error_id: str, new_status: str) -> bool:
        for e in self.error_reports:
            if e["error_id"] == error_id:
                e["status"] = new_status
                return True
        return False


global_error_monitor = ErrorMonitor()
