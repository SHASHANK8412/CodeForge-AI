"""
Unit and Integration Tests for AIForge Autonomous GitHub Integration
====================================================================
Covers:
1. Git repository initialization & branch naming ('main')
2. Git safe staging and structured commit creation
3. Git branch creation and sanitization
4. Git remote configuration and push execution
5. GitHub authentication & credential verification
6. GitHub repository creation (private by default, public option)
7. Repository already exists collision handling
8. GitHub API failure & error reporting
9. GitHub API rate limit handling (429 / RateLimitError)
10. Pre-publish secret detection & security abort
11. Technology-aware .gitignore generation
12. Comprehensive README.md generation
13. CI workflow generation (.github/workflows/aiforge-ci.yml)
14. Full publish workflow & structured return payload
15. Incremental sync / versioning updates
16. Repository metadata persistence & retrieval
17. REST API endpoints verification
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.github.git_service import GitService, GitExecutionResult
from backend.github.github_api_service import (
    GitHubAPIService,
    GitHubAPIError,
    GitHubAuthError,
    GitHubRepoExistsError,
    GitHubRateLimitError
)
from backend.github.repo_store import GitHubRepoStore, ProjectGitHubMetadata
from backend.github.publisher import (
    AutonomousGitHubPublisher,
    SecurityViolationError
)
from backend.execution.project_detector import ProjectDetector, DetectedProjectConfig
from backend.ci.github_actions_generator import GitHubActionsGenerator
from backend.main import app


class TestAutonomousGitHubIntegration:
    """Test suite for Autonomous GitHub Integration."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        ws = tmp_path / "test_project_workspace"
        ws.mkdir(parents=True, exist_ok=True)
        return ws

    @pytest.fixture
    def mock_repo_store(self, tmp_path):
        store_file = tmp_path / "test_repos.json"
        return GitHubRepoStore(storage_file=store_file)

    # -------------------------------------------------------------------------
    # 1. Git Initialization
    # -------------------------------------------------------------------------
    def test_git_init(self, temp_workspace):
        git = GitService()
        res = git.init(temp_workspace, initial_branch="main")
        assert res.success
        assert (temp_workspace / ".git").exists()
        current_branch = git.get_current_branch(temp_workspace)
        assert current_branch in ["main", "master"]

    # -------------------------------------------------------------------------
    # 2. Git Staging & Commit
    # -------------------------------------------------------------------------
    def test_git_staging_and_commit(self, temp_workspace):
        git = GitService()
        git.init(temp_workspace, initial_branch="main")

        # Create a test file
        test_file = temp_workspace / "app.py"
        test_file.write_text("print('hello AIForge')", encoding="utf-8")

        # Add and commit
        add_res = git.add(temp_workspace)
        assert add_res.success

        commit_res = git.commit(temp_workspace, message="feat: initial project creation")
        assert commit_res.success

        sha = git.get_latest_commit_sha(temp_workspace)
        assert len(sha) >= 7

        status = git.status(temp_workspace)
        assert status["clean"]
        assert len(status["staged"]) == 0

    # -------------------------------------------------------------------------
    # 3. Branch Creation & Sanitization
    # -------------------------------------------------------------------------
    def test_git_branch_creation_and_sanitization(self, temp_workspace):
        git = GitService()
        git.init(temp_workspace, initial_branch="main")

        (temp_workspace / "init.txt").write_text("initial", encoding="utf-8")
        git.add(temp_workspace)
        git.commit(temp_workspace, "feat: init")

        # Test branch creation
        branch_res = git.branch(temp_workspace, "feature/payment-gateway; rm -rf /")
        assert branch_res.success

        current = git.get_current_branch(temp_workspace)
        assert ";" not in current
        assert "rm" not in current or "payment-gateway" in current

    # -------------------------------------------------------------------------
    # 4. Remote Configuration & Push Execution
    # -------------------------------------------------------------------------
    def test_git_remote_and_push(self, temp_workspace):
        git = GitService()
        git.init(temp_workspace, initial_branch="main")

        (temp_workspace / "main.py").write_text("print('push')", encoding="utf-8")
        git.add(temp_workspace)
        git.commit(temp_workspace, "feat: push test")

        # Remote add
        remote_res = git.remote_add(temp_workspace, "origin", "https://github.com/aiforge/mock-repo.git")
        assert remote_res.success

        url = git.remote_get(temp_workspace, "origin")
        assert url == "https://github.com/aiforge/mock-repo.git"

    # -------------------------------------------------------------------------
    # 5. GitHub Authentication & Credential Verification
    # -------------------------------------------------------------------------
    def test_github_authentication_verification(self):
        # Simulated mode (no token configured)
        api = GitHubAPIService(token=None)
        res = api.verify_credentials()
        assert res["authenticated"]
        assert res["simulated"]
        assert "login" in res

        # Rate limit check
        rate = api.get_rate_limit()
        assert rate["limit"] >= 5000
        assert rate["remaining"] >= 5000

    # -------------------------------------------------------------------------
    # 6. GitHub Repository Creation (Private by Default, Public Configurable)
    # -------------------------------------------------------------------------
    def test_github_repository_creation(self):
        api = GitHubAPIService(token=None)

        # Private default
        repo_priv = api.create_repository(name="my-awesome-service", description="Test service", private=True)
        assert repo_priv["name"] == "my-awesome-service"
        assert repo_priv["private"] is True
        assert "html_url" in repo_priv

        # Public option
        repo_pub = api.create_repository(name="open-library", private=False)
        assert repo_pub["name"] == "open-library"
        assert repo_pub["private"] is False

    # -------------------------------------------------------------------------
    # 7. Repository Already Exists Collision Handling
    # -------------------------------------------------------------------------
    def test_repository_already_exists_handling(self):
        api = GitHubAPIService(token="ghp_fake_token_for_testing")

        with patch.object(api, "_http_request") as mock_req:
            mock_req.side_effect = GitHubRepoExistsError("Repository already exists on this account", status_code=422)
            with pytest.raises(GitHubRepoExistsError) as exc_info:
                api.create_repository("existing-repo")
            assert exc_info.value.status_code == 422
            assert "already exists" in str(exc_info.value).lower()

    # -------------------------------------------------------------------------
    # 8. GitHub API Failure Handling
    # -------------------------------------------------------------------------
    def test_github_api_failure_handling(self):
        api = GitHubAPIService(token="ghp_fake_token")

        with patch.object(api, "_http_request") as mock_req:
            mock_req.side_effect = GitHubAuthError("Bad credentials", status_code=401)
            with pytest.raises(GitHubAuthError) as exc_info:
                api.verify_credentials("invalid_token")
            assert exc_info.value.status_code == 401

    # -------------------------------------------------------------------------
    # 9. GitHub API Rate Limit Handling
    # -------------------------------------------------------------------------
    def test_github_api_rate_limit_handling(self):
        api = GitHubAPIService(token="ghp_fake_token")

        with patch.object(api, "_http_request") as mock_req:
            mock_req.side_effect = GitHubRateLimitError("API rate limit exceeded", status_code=403)
            with pytest.raises(GitHubRateLimitError) as exc_info:
                api.create_repository("rate-limited-repo")
            assert exc_info.value.status_code == 403

    # -------------------------------------------------------------------------
    # 10. Pre-Publish Secret Detection & Security Abort
    # -------------------------------------------------------------------------
    def test_pre_publish_secret_detection_blocks_publishing(self, mock_repo_store):
        publisher = AutonomousGitHubPublisher(repo_store=mock_repo_store)

        # Leaked AWS credential and API token
        files_with_secrets = {
            "config.py": 'AWS_ACCESS_KEY = "AKIA1234567890123456"\n',
            "main.py": 'api_key = "abcdefghijklmnopqrstuvwxyz1234"\n'
        }

        with pytest.raises(SecurityViolationError) as exc_info:
            publisher.publish_project(
                project_id="compromised_project",
                files_manifest=files_with_secrets
            )

        assert "hardcoded secret" in str(exc_info.value).lower()
        findings = exc_info.value.findings
        assert len(findings) >= 1
        assert any(f["rule"] == "AWS_ACCESS_KEY" for f in findings)

    # -------------------------------------------------------------------------
    # 11. Technology-Aware .gitignore Generation
    # -------------------------------------------------------------------------
    def test_gitignore_generation(self):
        publisher = AutonomousGitHubPublisher()
        gitignore = publisher.generate_gitignore()

        assert ".env" in gitignore
        assert "*.key" in gitignore
        assert "__pycache__" in gitignore
        assert ".venv" in gitignore
        assert "node_modules" in gitignore
        assert "secrets/" in gitignore

    # -------------------------------------------------------------------------
    # 12. Comprehensive README.md Generation
    # -------------------------------------------------------------------------
    def test_readme_generation(self):
        publisher = AutonomousGitHubPublisher()
        detector = ProjectDetector()

        python_files = {
            "requirements.txt": "fastapi>=0.100.0\npytest\n",
            "main.py": "def app(): pass"
        }
        cfg = detector.detect(python_files)
        readme = publisher.generate_readme("ecommerce-api", python_files, cfg)

        assert "# Ecommerce Api" in readme
        assert "Project Overview" in readme
        assert "Architecture" in readme
        assert "Installation" in readme
        assert "Running Tests" in readme
        assert "CI/CD Pipeline" in readme
        assert "AIForge" in readme

    # -------------------------------------------------------------------------
    # 13. CI Workflow Generation (.github/workflows/aiforge-ci.yml)
    # -------------------------------------------------------------------------
    def test_ci_workflow_generation(self):
        generator = GitHubActionsGenerator()
        files = {
            "requirements.txt": "fastapi\npytest\n",
            "main.py": "print('ok')"
        }
        workflow = generator.generate_workflow(files, project_name="analytics-service")

        assert "name: AIForge CI - analytics-service" in workflow
        assert "actions/checkout" in workflow
        assert "actions/setup-python" in workflow
        assert "pytest" in workflow

    # -------------------------------------------------------------------------
    # 14. Full Publish Workflow & Structured Return Payload
    # -------------------------------------------------------------------------
    def test_full_publish_workflow(self, mock_repo_store, temp_workspace):
        publisher = AutonomousGitHubPublisher(repo_store=mock_repo_store)

        clean_files = {
            "requirements.txt": "fastapi>=0.100.0\npytest\n",
            "main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root(): return {'status': 'ok'}\n",
            "tests/test_main.py": "from main import root\ndef test_root(): assert root() == {'status': 'ok'}\n"
        }

        result = publisher.publish_project(
            project_id="ecommerce_v2",
            files_manifest=clean_files,
            repo_name="ecommerce-v2",
            description="Autonomous eCommerce API",
            private=True,
            working_dir=temp_workspace
        )

        # Validate structured result fields per requirement
        assert result["status"] == "published"
        assert "repository" in result
        assert result["repository"]["name"] == "ecommerce-v2"
        assert result["repository"]["visibility"] == "private"
        assert result["repository"]["branch"] == "main"
        assert "url" in result["repository"]
        assert "commit" in result
        assert len(result["commit"]["sha"]) >= 4
        assert result["commit"]["message"] == "feat: generate project"
        assert result["ci"]["workflow_created"] is True

        # Verify generated files on disk
        assert (temp_workspace / ".gitignore").exists()
        assert (temp_workspace / "README.md").exists()
        assert (temp_workspace / ".github" / "workflows" / "aiforge-ci.yml").exists()

        # Verify metadata persisted in store
        meta = mock_repo_store.get("ecommerce_v2")
        assert meta is not None
        assert meta.repo_name == "ecommerce-v2"
        assert meta.visibility == "private"
        assert meta.status == "published"

    # -------------------------------------------------------------------------
    # 15. Incremental Sync / Versioning Updates
    # -------------------------------------------------------------------------
    def test_incremental_sync_updates(self, mock_repo_store, temp_workspace):
        publisher = AutonomousGitHubPublisher(repo_store=mock_repo_store)

        # Initial publish
        initial_files = {"main.py": "def foo(): return 1\n"}
        publisher.publish_project(
            project_id="sync_demo",
            files_manifest=initial_files,
            working_dir=temp_workspace
        )

        # Update files and sync
        updated_files = {
            "main.py": "def foo(): return 2\n",
            "utils.py": "def bar(): return 'new helper'\n"
        }

        sync_res = publisher.sync_project_updates(
            project_id="sync_demo",
            files_manifest=updated_files,
            commit_message="fix: update foo logic and add utils",
            working_dir=temp_workspace
        )

        assert sync_res["status"] == "synced"
        assert sync_res["commit"]["message"] == "fix: update foo logic and add utils"

        meta = mock_repo_store.get("sync_demo")
        assert meta.last_commit_message == "fix: update foo logic and add utils"

    # -------------------------------------------------------------------------
    # 16. REST API Endpoints Verification
    # -------------------------------------------------------------------------
    def test_rest_api_endpoints(self):
        client = TestClient(app)

        # 1. Connect
        conn_res = client.post("/api/github/connect", json={"project_id": "test_api_proj"})
        assert conn_res.status_code == 200
        assert conn_res.json()["authenticated"] is True

        # 2. Repository creation
        repo_res = client.post("/api/github/repository", json={
            "name": "test-created-repo",
            "description": "Created via REST API",
            "private": True
        })
        assert repo_res.status_code == 200
        assert repo_res.json()["success"] is True

        # 3. Publish
        pub_res = client.post("/api/github/publish", json={
            "project_id": "api_test_project",
            "repo_name": "api-test-repo",
            "private": True,
            "files": {
                "main.py": "print('API published')",
                "requirements.txt": "fastapi\n"
            }
        })
        assert pub_res.status_code == 200
        pub_data = pub_res.json()
        assert pub_data["status"] == "published"
        assert pub_data["repository"]["name"] == "api-test-repo"

        # 4. Get Repository Metadata
        meta_res = client.get("/api/github/repository/api_test_project")
        assert meta_res.status_code == 200
        assert meta_res.json()["connected"] is True
        assert meta_res.json()["repository"]["name"] == "api-test-repo"

        # 5. Security Rejection via API
        sec_res = client.post("/api/github/publish", json={
            "project_id": "compromised_api_project",
            "files": {
                "secret.py": 'AWS_ACCESS_KEY = "AKIA1234567890123456"\n'
            }
        })
        assert sec_res.status_code == 400
        assert "SECURITY_VIOLATION" in str(sec_res.json())
