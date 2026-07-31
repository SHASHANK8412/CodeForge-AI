"""
AIForge Root Cause Finder Agent
===============================
Performs deep root cause analysis (RCA) on error diagnostics to isolate the underlying cause and determine target repair actions and confidence scores.
"""

import time
import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.agents.root_cause")


class RootCauseFinder:
    """
    Analyzes error reports from ErrorAnalyzerAgent to identify root causes and specific suggested fixes.
    """

    def analyze(self, error_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes structured error analysis and returns root cause details, suggested fix, and confidence score (0-100%).
        """
        err_type = error_report.get("error_type", "General")
        msg = (error_report.get("cause") or error_report.get("message") or error_report.get("raw_traceback") or "").lower()
        file = error_report.get("file", "unknown")
        category = error_report.get("category", "General")

        # 1. Dependency Errors
        if err_type in ["ModuleNotFoundError", "ImportError"] or "not installed" in msg or "no module named" in msg:
            pkg_name = "fastapi"
            if "no module named" in msg:
                parts = msg.split("no module named")
                if len(parts) > 1:
                    pkg_name = parts[1].strip(" '\"`")
            root_cause = f"Module {pkg_name} not installed"
            suggested_fix = f"pip install {pkg_name}"
            confidence = 94
            action_type = "INSTALL_DEPENDENCY"

        # 2. Python Syntax / Indentation Errors
        elif err_type in ["SyntaxError", "IndentationError", "JSXSyntaxError"]:
            root_cause = f"Syntax error in code file {file}"
            suggested_fix = f"Fix missing brackets, parentheses, or improper indentation in {file}"
            confidence = 90
            action_type = "PATCH_SYNTAX"

        # 3. Missing React Import / Hook Misuse / Infinite Render
        elif err_type == "HookMisuse" or "hook" in msg:
            root_cause = f"React Hook called conditionally or outside function component top-level in {file}"
            suggested_fix = f"Move Hook invocation to top-level of function component in {file}"
            confidence = 88
            action_type = "REFACTOR_REACT"
        elif err_type == "InfiniteRender" or "infinite" in msg:
            root_cause = f"State update trigger causing infinite render loop in {file}"
            suggested_fix = f"Add dependency array to useEffect or wrap callback in useCallback in {file}"
            confidence = 85
            action_type = "REFACTOR_REACT"
        elif err_type == "MissingImport" or ("resolve" in msg and "import" in msg):
            root_cause = f"Missing module or component import statement in {file}"
            suggested_fix = f"Add top-level import statement for missing symbol in {file}"
            confidence = 92
            action_type = "ADD_IMPORT"

        # 4. FastAPI Errors
        elif err_type == "MissingRouter" or "router" in msg:
            root_cause = "FastAPI router missing registration in main application"
            suggested_fix = "Include router using app.include_router(router) in backend/main.py"
            confidence = 91
            action_type = "REGISTER_ROUTER"
        elif err_type == "ResponseModelMismatch" or "responsemodel" in msg:
            root_cause = f"FastAPI endpoint response payload violates response_model schema in {file}"
            suggested_fix = f"Align dictionary keys and types in endpoint handler with pydantic response_model in {file}"
            confidence = 86
            action_type = "MODIFY_SCHEMA"
        elif err_type == "AsyncLoopMismatch" or "awaited" in msg:
            root_cause = f"Unawaited coroutine or event loop mismatch in {file}"
            suggested_fix = f"Add await keyword before async call or run inside active event loop in {file}"
            confidence = 87
            action_type = "FIX_ASYNC"

        # 5. PostgreSQL Errors
        elif err_type == "PostgreSQLConnectionRefused" or "connection refused" in msg:
            root_cause = "PostgreSQL service unavailable or database host connection refused"
            suggested_fix = "Verify PostgreSQL service is running and update DB_HOST / DB_PORT in backend/.env"
            confidence = 89
            action_type = "UPDATE_CONFIG"
        elif err_type == "PostgreSQLAuthFailed" or "password authentication failed" in msg:
            root_cause = "PostgreSQL authentication failed due to invalid credentials"
            suggested_fix = "Verify DB_USER and DB_PASSWORD credentials in backend/.env"
            confidence = 93
            action_type = "UPDATE_CONFIG"
        elif err_type == "PostgreSQLMissingTable" or "relation" in msg:
            root_cause = f"Missing PostgreSQL database table relation in schema"
            suggested_fix = "Execute database schema migration scripts or create missing table in database/schema.sql"
            confidence = 90
            action_type = "MIGRATE_DB"

        # 6. Docker Errors
        elif err_type == "DockerBuildFailed" or "docker build" in msg:
            root_cause = "Dockerfile build instruction failed during image creation"
            suggested_fix = "Fix base image tag or RUN installation steps in Dockerfile"
            confidence = 85
            action_type = "FIX_DOCKERFILE"
        elif err_type == "ContainerCrashed" or "container exited" in msg:
            root_cause = "Docker container process exited prematurely on startup"
            suggested_fix = "Check CMD entrypoint script and environment variables in docker-compose.yml"
            confidence = 82
            action_type = "FIX_DOCKER_COMPOSE"

        # 7. Git Errors
        elif err_type == "GitMergeConflict" or "merge conflict" in msg:
            root_cause = f"Git merge conflict marker encountered in {file}"
            suggested_fix = f"Resolve conflict markers (<<<<<<< / >>>>>>>) in {file} and commit changes"
            confidence = 90
            action_type = "RESOLVE_GIT"
        elif err_type == "GitDetachedHead" or "detached head" in msg:
            root_cause = "Git working copy in detached HEAD state"
            suggested_fix = "Checkout main or develop branch using git checkout main"
            confidence = 88
            action_type = "RESOLVE_GIT"

        # 8. Python Runtime Exceptions (AttributeError, TypeError, KeyError, NameError)
        elif err_type in ["AttributeError", "TypeError", "KeyError", "NameError"]:
            root_cause = f"Unhandled {err_type} exception in {file}"
            suggested_fix = f"Add null safety guard, check variable definition, or validate dictionary key in {file}"
            confidence = 78
            action_type = "PATCH_CODE"

        # 9. Unknown or Unhandled Failures
        else:
            root_cause = f"Unclassified error exception in {file}"
            suggested_fix = f"Inspect stack trace and refine exception handling in {file}"
            confidence = 45  # Low confidence for unknown error trigger (<60% condition)
            action_type = "INVESTIGATE"

        formatted_report = (
            f"Root Cause:\n"
            f"{root_cause}\n\n"
            f"Suggested Fix:\n"
            f"{suggested_fix}"
        )

        return {
            "rca_id": f"rca_{int(time.time() * 1000)}",
            "error_id": error_report.get("error_id", "unknown"),
            "target_file": file,
            "error_type": err_type,
            "category": category,
            "root_cause": root_cause,
            "suggested_fix": suggested_fix,
            "formatted_text": formatted_report,
            "confidence_score": confidence,
            "action_type": action_type,
            "analyzed_at": time.time()
        }


global_root_cause_finder = RootCauseFinder()
