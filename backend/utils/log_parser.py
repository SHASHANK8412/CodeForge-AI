"""
AIForge Log Parser Utility
===========================
Parses build logs, test outputs, runtime logs, and stack traces across Python, React, FastAPI, PostgreSQL, Docker, and Git.
"""

import re
from typing import Dict, Any, Optional


class LogParser:
    """
    Parses multi-technology log files and stack traces to extract error categorization, file paths, line numbers, and causes.
    """

    def parse_log(self, log_content: str) -> Dict[str, Any]:
        """
        Main entry point for parsing log text into a structured error dictionary.
        """
        if not log_content or not isinstance(log_content, str):
            return {
                "error_type": "UnknownError",
                "severity": "Low",
                "file": "unknown",
                "line": 1,
                "cause": "Empty or non-string log content",
                "category": "General",
                "raw_traceback": ""
            }

        # Order of checking parsers (framework/tech specific before general Python)
        parsed = (
            self._parse_fastapi(log_content)
            or self._parse_react(log_content)
            or self._parse_postgresql(log_content)
            or self._parse_docker(log_content)
            or self._parse_git(log_content)
            or self._parse_python(log_content)
        )

        if parsed:
            parsed["raw_traceback"] = log_content.strip()
            return parsed

        # Fallback for unrecognized error
        file_match = re.search(r'([a-zA-Z0-9_\-/\\]+\.(?:py|js|jsx|ts|tsx|sql|json|dockerfile|yml|yaml))(?::| line )(\d+)', log_content, re.IGNORECASE)
        file_path = file_match.group(1) if file_match else "unknown"
        line_num = int(file_match.group(2)) if file_match else 1

        first_line = log_content.strip().split("\n")[0] if log_content.strip() else "Unknown runtime error"
        return {
            "error_type": "UnknownError",
            "severity": "Medium",
            "file": file_path,
            "line": line_num,
            "cause": first_line[:150],
            "category": "General",
            "raw_traceback": log_content.strip()
        }

    def _parse_python(self, text: str) -> Optional[Dict[str, Any]]:
        # Match Python Exceptions
        py_errors = [
            "SyntaxError", "ImportError", "ModuleNotFoundError", "NameError",
            "IndentationError", "AttributeError", "TypeError", "KeyError"
        ]
        
        pattern = r'(' + '|'.join(py_errors) + r'):\s*(.+)'
        match = re.search(pattern, text)
        if not match:
            return None

        err_type = match.group(1)
        cause = match.group(2).strip()

        # Find file and line
        file_line_match = re.findall(r'File "([^"]+)", line (\d+)', text)
        if file_line_match:
            file_path, line_str = file_line_match[-1]
            line_num = int(line_str)
        else:
            file_path = "backend/main.py"
            line_num = 1

        severity = "High" if err_type in ["SyntaxError", "IndentationError", "ModuleNotFoundError", "ImportError"] else "Medium"

        return {
            "error_type": err_type,
            "severity": severity,
            "file": file_path,
            "line": line_num,
            "cause": cause,
            "category": "Python"
        }

    def _parse_react(self, text: str) -> Optional[Dict[str, Any]]:
        if "React Hook" in text or "use" in text and "is called conditionally" in text:
            file_match = re.search(r'([a-zA-Z0-9_\-/.]+\.(?:jsx|tsx|js|ts))(?::|:line )(\d+)?', text)
            return {
                "error_type": "HookMisuse",
                "severity": "High",
                "file": file_match.group(1) if file_match else "src/App.jsx",
                "line": int(file_match.group(2)) if file_match and file_match.group(2) else 10,
                "cause": "React Hook called conditionally or out of component top-level",
                "category": "React"
            }

        if "Maximum update depth exceeded" in text or "infinite render" in text.lower():
            return {
                "error_type": "InfiniteRender",
                "severity": "High",
                "file": "src/App.jsx",
                "line": 1,
                "cause": "Maximum update depth exceeded (infinite useEffect/state trigger loop)",
                "category": "React"
            }

        if "Module not found: Can't resolve" in text or "Failed to resolve import" in text:
            match = re.search(r"Can't resolve '([^']+)'|Failed to resolve import \"([^\"]+)\"", text)
            module_name = match.group(1) or match.group(2) if match else "unknown-module"
            return {
                "error_type": "MissingImport",
                "severity": "High",
                "file": "src/App.jsx",
                "line": 1,
                "cause": f"Missing import or unresolvable module: {module_name}",
                "category": "React"
            }

        if "JSX" in text or "Parsing error: Unexpected token" in text:
            file_match = re.search(r'([a-zA-Z0-9_\-/.]+\.(?:jsx|tsx))(?::| line )(\d+)?', text)
            return {
                "error_type": "JSXSyntaxError",
                "severity": "High",
                "file": file_match.group(1) if file_match else "src/App.jsx",
                "line": int(file_match.group(2)) if file_match and file_match.group(2) else 1,
                "cause": "JSX syntax error or unclosed element tag",
                "category": "React"
            }

        return None

    def _parse_fastapi(self, text: str) -> Optional[Dict[str, Any]]:
        if "ResponseValidationError" in text or "response_model" in text.lower():
            return {
                "error_type": "ResponseModelMismatch",
                "severity": "Medium",
                "file": "backend/main.py",
                "line": 15,
                "cause": "FastAPI response data does not match response_model schema definition",
                "category": "FastAPI"
            }

        if "router" in text.lower() and ("not registered" in text.lower() or "has no attribute 'include_router'" in text.lower() or "404 not found" in text.lower()):
            return {
                "error_type": "MissingRouter",
                "severity": "High",
                "file": "backend/main.py",
                "line": 25,
                "cause": "FastAPI router is not registered on app instance",
                "category": "FastAPI"
            }

        if "Task attached to a different loop" in text or "was never awaited" in text:
            return {
                "error_type": "AsyncLoopMismatch",
                "severity": "High",
                "file": "backend/main.py",
                "line": 30,
                "cause": "Async event loop mismatch or missing await keyword on coroutine",
                "category": "FastAPI"
            }

        return None

    def _parse_postgresql(self, text: str) -> Optional[Dict[str, Any]]:
        if "connection to server at" in text.lower() or "connection refused" in text.lower() or "OperationalError" in text:
            return {
                "error_type": "PostgreSQLConnectionRefused",
                "severity": "High",
                "file": "backend/config.py",
                "line": 10,
                "cause": "PostgreSQL connection refused: database host or port unreachable",
                "category": "PostgreSQL"
            }

        if "password authentication failed" in text.lower() or "FATAL:  password authentication failed" in text:
            return {
                "error_type": "PostgreSQLAuthFailed",
                "severity": "High",
                "file": "backend/.env",
                "line": 5,
                "cause": "PostgreSQL authentication failed for user/password credentials",
                "category": "PostgreSQL"
            }

        if "relation" in text.lower() and "does not exist" in text.lower():
            match = re.search(r'relation "([^"]+)" does not exist', text, re.IGNORECASE)
            table_name = match.group(1) if match else "unknown"
            return {
                "error_type": "PostgreSQLMissingTable",
                "severity": "High",
                "file": "database/schema.sql",
                "line": 1,
                "cause": f"Missing PostgreSQL database table relation: {table_name}",
                "category": "PostgreSQL"
            }

        return None

    def _parse_docker(self, text: str) -> Optional[Dict[str, Any]]:
        if "failed to solve" in text.lower() or "docker build" in text.lower() or "Dockerfile" in text:
            return {
                "error_type": "DockerBuildFailed",
                "severity": "High",
                "file": "Dockerfile",
                "line": 1,
                "cause": "Docker image build step failed",
                "category": "Docker"
            }

        if "container exited with code" in text.lower() or "docker run" in text.lower():
            return {
                "error_type": "ContainerCrashed",
                "severity": "High",
                "file": "docker-compose.yml",
                "line": 1,
                "cause": "Docker container exited unexpectedly during startup",
                "category": "Docker"
            }

        return None

    def _parse_git(self, text: str) -> Optional[Dict[str, Any]]:
        if "merge conflict" in text.lower() or "CONFLICT (content)" in text:
            file_match = re.search(r'Merge conflict in ([^\s]+)', text)
            return {
                "error_type": "GitMergeConflict",
                "severity": "Medium",
                "file": file_match.group(1) if file_match else "unknown",
                "line": 1,
                "cause": "Git merge conflict in project repository file",
                "category": "Git"
            }

        if "HEAD detached" in text or "detached HEAD" in text.lower():
            return {
                "error_type": "GitDetachedHead",
                "severity": "Low",
                "file": ".git",
                "line": 1,
                "cause": "Git repository is in a detached HEAD state",
                "category": "Git"
            }

        return None


global_log_parser = LogParser()
