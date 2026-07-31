import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.agents.error_analyzer import ErrorAnalyzerAgent
from backend.utils.log_parser import LogParser


class TestErrorAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = ErrorAnalyzerAgent()
        self.parser = LogParser()

    def test_python_error_parsing(self):
        log = """
Traceback (most recent call last):
  File "backend/main.py", line 21, in <module>
ModuleNotFoundError: No module named 'fastapi'
        """
        analysis = self.analyzer.analyze_log(log)
        self.assertEqual(analysis["error_type"], "ModuleNotFoundError")
        self.assertEqual(analysis["category"], "Python")
        self.assertEqual(analysis["file"], "backend/main.py")
        self.assertEqual(analysis["line"], 21)

    def test_react_hook_error_parsing(self):
        log = "Error: React Hook 'useState' is called conditionally in src/App.jsx:15"
        analysis = self.analyzer.analyze_log(log)
        self.assertEqual(analysis["error_type"], "HookMisuse")
        self.assertEqual(analysis["category"], "React")
        self.assertEqual(analysis["file"], "src/App.jsx")

    def test_fastapi_missing_router_parsing(self):
        log = "AttributeError: 'FastAPI' object has no attribute 'include_router' or router missing in backend/main.py:25"
        analysis = self.analyzer.analyze_log(log)
        self.assertEqual(analysis["error_type"], "MissingRouter")
        self.assertEqual(analysis["category"], "FastAPI")

    def test_postgresql_connection_refused(self):
        log = "psycopg2.OperationalError: connection to server at '127.0.0.1', port 5432 failed: Connection refused"
        analysis = self.analyzer.analyze_log(log)
        self.assertEqual(analysis["error_type"], "PostgreSQLConnectionRefused")
        self.assertEqual(analysis["category"], "PostgreSQL")

    def test_docker_build_failure(self):
        log = "ERROR: failed to solve: process '/bin/sh -c pip install' exited with code: 1 in Dockerfile"
        analysis = self.analyzer.analyze_log(log)
        self.assertEqual(analysis["error_type"], "DockerBuildFailed")
        self.assertEqual(analysis["category"], "Docker")

    def test_git_merge_conflict(self):
        log = "CONFLICT (content): Merge conflict in backend/main.py"
        analysis = self.analyzer.analyze_log(log)
        self.assertEqual(analysis["error_type"], "GitMergeConflict")
        self.assertEqual(analysis["category"], "Git")


if __name__ == "__main__":
    unittest.main()
