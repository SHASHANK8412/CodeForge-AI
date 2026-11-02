"""
AIForge Autonomous GitHub Integration Module
============================================
Provides safe Git CLI services, official GitHub REST API integration,
pre-publish security validation, and automated repository publishing.
"""

from backend.github.client import get_github_client
from backend.github.service import global_github_service
from backend.github.git_service import GitService, global_git_service, GitExecutionResult
from backend.github.github_api_service import (
    GitHubAPIService,
    global_github_api_service,
    GitHubAPIError,
    GitHubAuthError,
    GitHubRepoExistsError,
    GitHubRateLimitError
)
from backend.github.repo_store import (
    GitHubRepoStore,
    global_github_repo_store,
    ProjectGitHubMetadata
)
from backend.github.publisher import (
    AutonomousGitHubPublisher,
    global_github_publisher,
    SecurityViolationError,
    PrePublishValidationError
)

__all__ = [
    "get_github_client",
    "global_github_service",
    "GitService",
    "global_git_service",
    "GitExecutionResult",
    "GitHubAPIService",
    "global_github_api_service",
    "GitHubAPIError",
    "GitHubAuthError",
    "GitHubRepoExistsError",
    "GitHubRateLimitError",
    "GitHubRepoStore",
    "global_github_repo_store",
    "ProjectGitHubMetadata",
    "AutonomousGitHubPublisher",
    "global_github_publisher",
    "SecurityViolationError",
    "PrePublishValidationError",
]
