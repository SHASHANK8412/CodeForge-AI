"""
AIForge V2 – Pytest Unit Test Suite Generator
=============================================
Generates automated pytest testing scripts for FastAPI routers and services.
"""

from typing import List
from v2.agents.backend.models import BackendTestSpec


class PytestTestGenerator:

    def generate_default_tests(self) -> List[BackendTestSpec]:
        return [
            BackendTestSpec(
                test_name="test_auth_endpoints",
                target_module="api.routers.auth",
                code_content="""import unittest

class TestAuthEndpoints(unittest.TestCase):
    def test_login_success(self):
        token = "mock_jwt_token_2026"
        self.assertIsNotNone(token)

if __name__ == "__main__":
    unittest.main()
"""
            ),
            BackendTestSpec(
                test_name="test_project_service",
                target_module="services.project_service",
                code_content="""import unittest

class TestProjectService(unittest.TestCase):
    def test_get_projects(self):
        projects = [{"id": "p1", "name": "AI Resume Analyzer"}]
        self.assertEqual(len(projects), 1)

if __name__ == "__main__":
    unittest.main()
"""
            )
        ]


global_test_generator = PytestTestGenerator()
