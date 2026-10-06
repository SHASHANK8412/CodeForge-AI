"""
AIForge Autonomous GitHub Integration Router
============================================
Exposes REST endpoints for:
- Connection & credential verification: POST /api/github/connect
- Repository creation: POST /api/github/repository
- Autonomous project publishing: POST /api/github/publish
- Repository metadata & status query: GET /api/github/repository/{project_id}
- Incremental updates & sync: POST /api/github/sync
- Local Git operations & legacy PR endpoints
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.generators.project_generator import GENERATED_PROJECTS_DIR
from backend.github.service import global_github_service
from backend.github.repositories import global_repository_analyzer
from backend.github.branches import global_branch_manager
from backend.github.commits import global_commit_manager
from backend.github.pull_requests import global_pr_generator
from backend.github.git_service import global_git_service
from backend.github.github_api_service import (
    global_github_api_service,
    GitHubAPIError,
    GitHubAuthError,
    GitHubRepoExistsError,
    GitHubRateLimitError
)
from backend.github.repo_store import global_github_repo_store, ProjectGitHubMetadata
from backend.github.publisher import (
    global_github_publisher,
    SecurityViolationError,
    PrePublishValidationError
)

logger = logging.getLogger("aiforge.routes.github")

router = APIRouter(tags=["GitHub Integration"])


# -----------------------------------------------------------------------------
# Request & Response Schemas
# -----------------------------------------------------------------------------

class GitInitRequest(BaseModel):
    project_id: str = "aiforge-demo"


class GitStatusRequest(BaseModel):
    project_id: str = "aiforge-demo"


class GitCommitRequest(BaseModel):
    project_id: str = "aiforge-demo"
    message: str


class GitPushRequest(BaseModel):
    project_id: str = "aiforge-demo"
    remote_url: Optional[str] = None


class GitBranchRequest(BaseModel):
    project_id: str = "aiforge-demo"
    branch_name: str


class GitPullRequestRequest(BaseModel):
    project_id: str = "aiforge-demo"
    title: str
    body: Optional[str] = ""
    head_branch: str
    base_branch: Optional[str] = "main"


class CopilotGithubRequest(BaseModel):
    query: str
    project_id: str = "aiforge-demo"
    full_repo_name: str = "SHASHANK8412/CodeForge-AI"


class GitHubConnectRequest(BaseModel):
    token: Optional[str] = None
    repo_url: Optional[str] = None
    project_id: Optional[str] = "aiforge-demo"


class CreateRepositoryRequest(BaseModel):
    name: str = Field(description="Repository name")
    description: Optional[str] = Field(default="", description="Repository description")
    private: bool = Field(default=True, description="True for private repository, False for public")
    org: Optional[str] = Field(default=None, description="Optional GitHub organization name")
    token: Optional[str] = Field(default=None, description="Optional GitHub PAT")


class PublishProjectRequest(BaseModel):
    project_id: str = Field(default="default_project", description="Target project ID")
    repo_name: Optional[str] = Field(default=None, description="Custom repository name")
    description: Optional[str] = Field(default="", description="Repository description")
    private: bool = Field(default=True, description="Private or Public visibility")
    org: Optional[str] = Field(default=None, description="Organization name")
    files: Optional[Dict[str, str]] = Field(default=None, description="Project file manifest")
    token: Optional[str] = Field(default=None, description="GitHub PAT")
    skip_ci_check: bool = Field(default=False, description="Whether to bypass pre-publish CI gate")


class SyncProjectRequest(BaseModel):
    project_id: str = Field(default="default_project", description="Target project ID")
    commit_message: Optional[str] = Field(default=None, description="Commit message for sync")
    files: Optional[Dict[str, str]] = Field(default=None, description="Updated file manifest")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _resolve_project_files(project_id: str, client_files: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Same rules as ZIP export: this project's real files only, never another project's or a stub."""
    from backend.routes.export import _resolve_project_files as resolve_export_files
    return resolve_export_files(project_id, client_files)


# -----------------------------------------------------------------------------
# Autonomous GitHub Integration Endpoints
# -----------------------------------------------------------------------------

@router.post("/api/github/connect")
@router.post("/github/connect")
def github_connect_endpoint(req: GitHubConnectRequest):
    """
    Validates GitHub authentication credentials and checks rate limits.
    If repo_url is provided, links the project to the existing remote repository.
    """
    try:
        user_info = global_github_api_service.verify_credentials(req.token)
        rate_info = global_github_api_service.get_rate_limit(req.token)

        connected_repo = None
        if req.repo_url:
            connected_repo = global_repository_analyzer.connect_repository(
                req.repo_url,
                project_id=req.project_id or "default_project",
                token=req.token
            )

        return {
            "success": True,
            "authenticated": user_info.get("authenticated", True),
            "simulated": user_info.get("simulated", False),
            "user": {
                "login": user_info.get("login"),
                "name": user_info.get("name"),
                "html_url": user_info.get("html_url")
            },
            "rate_limit": {
                "limit": rate_info.get("limit"),
                "remaining": rate_info.get("remaining")
            },
            "connected_repository": connected_repo
        }
    except GitHubAuthError as ae:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ae))
    except GitHubRateLimitError as rle:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(rle))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to connect to GitHub: {str(e)}")


@router.post("/api/github/repository")
@router.post("/github/repository")
def github_create_repository_endpoint(req: CreateRepositoryRequest):
    """
    Creates a new repository on GitHub (private by default).
    """
    try:
        repo_info = global_github_api_service.create_repository(
            name=req.name,
            description=req.description or "",
            private=req.private,
            org=req.org,
            token=req.token
        )
        return {
            "success": True,
            "repository": repo_info
        }
    except GitHubAuthError as ae:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ae))
    except GitHubRepoExistsError as ree:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ree))
    except GitHubRateLimitError as rle:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(rle))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/api/github/publish")
@router.post("/github/publish")
def github_publish_project_endpoint(req: PublishProjectRequest):
    """
    Orchestrates end-to-end publishing of an AIForge project to GitHub:
    - Pre-publish secret scanning
    - Auto-generated .gitignore, README.md, CI workflow
    - Git initialization and structured commit
    - GitHub remote creation and push
    - Return structured final report
    """
    files = _resolve_project_files(req.project_id, req.files)
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No files found for project '{req.project_id}'.")

    # If project already exists in generated_projects on disk, use it as working dir - but only
    # if it really is inside generated_projects ("..", absolute paths etc. would point the git
    # init/commit/push at some other directory, such as this repository).
    working_dir = None
    candidate = (GENERATED_PROJECTS_DIR / req.project_id).resolve()
    if candidate.is_dir() and GENERATED_PROJECTS_DIR.resolve() in candidate.parents:
        working_dir = candidate

    try:
        res = global_github_publisher.publish_project(
            project_id=req.project_id,
            files_manifest=files,
            repo_name=req.repo_name,
            description=req.description or "",
            private=req.private,
            org=req.org,
            token=req.token,
            working_dir=working_dir,
            skip_ci_check=req.skip_ci_check
        )
        return res
    except SecurityViolationError as sve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "SECURITY_VIOLATION",
                "message": str(sve),
                "findings": sve.findings
            }
        )
    except GitHubAuthError as ae:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ae))
    except GitHubRepoExistsError as ree:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ree))
    except GitHubRateLimitError as rle:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(rle))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception(f"Publish failed for '{req.project_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Publishing failed: {str(e)}")


@router.get("/api/github/repository/{project_id}")
@router.get("/github/repository/{project_id}")
def github_get_repository_endpoint(project_id: str):
    """
    Returns stored GitHub repository metadata and current publishing status for a project.
    """
    meta = global_github_repo_store.get(project_id)
    if not meta:
        return {
            "project_id": project_id,
            "connected": False,
            "status": "unlinked",
            "message": f"Project '{project_id}' is not published to GitHub."
        }

    return {
        "project_id": project_id,
        "connected": True,
        "status": meta.status,
        "repository": {
            "name": meta.repo_name,
            "url": meta.repo_url,
            "owner": meta.owner,
            "visibility": meta.visibility,
            "branch": meta.default_branch,
            "last_commit_sha": meta.last_commit_sha,
            "last_commit_message": meta.last_commit_message,
            "last_sync_time": meta.last_sync_time
        }
    }


@router.post("/api/github/sync")
@router.post("/github/sync")
def github_sync_project_endpoint(req: SyncProjectRequest):
    """
    Synchronizes subsequent changes and patches to the remote repository.
    """
    files = _resolve_project_files(req.project_id, req.files)
    working_dir = GENERATED_PROJECTS_DIR / req.project_id if (GENERATED_PROJECTS_DIR / req.project_id).exists() else None

    try:
        res = global_github_publisher.sync_project_updates(
            project_id=req.project_id,
            files_manifest=files,
            commit_message=req.commit_message,
            working_dir=working_dir
        )
        return res
    except SecurityViolationError as sve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "SECURITY_VIOLATION", "message": str(sve), "findings": sve.findings}
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Sync failed: {str(e)}")


# -----------------------------------------------------------------------------
# Preserved Legacy & PR Review Endpoints
# -----------------------------------------------------------------------------

@router.post("/api/github/git-init")
def git_init_endpoint(req: GitInitRequest):
    """Initializes local git repository with safe subprocess execution."""
    project_dir = GENERATED_PROJECTS_DIR / req.project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    init_res = global_git_service.init(project_dir, initial_branch="main")
    gitignore_path = project_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(global_github_publisher.generate_gitignore(), encoding="utf-8")

    return {
        "success": init_res.success,
        "stdout": init_res.stdout,
        "message": "Git repository initialized with .gitignore successfully."
    }


@router.get("/api/github/git-status")
def git_status_endpoint(project_id: str = "aiforge-demo"):
    """Returns local git status output safely."""
    project_dir = GENERATED_PROJECTS_DIR / project_id
    if not (project_dir / ".git").exists():
        return {"success": False, "stdout": "Git not initialized. Click 'Git Init' to configure."}

    status_data = global_git_service.status(project_dir)
    return {"success": True, "status": status_data, "stdout": f"Branch: {status_data.get('branch')}, Clean: {status_data.get('clean')}"}


@router.post("/api/github/commit")
def git_commit_endpoint(req: GitCommitRequest):
    """Stages files and creates a Git commit safely."""
    project_dir = GENERATED_PROJECTS_DIR / req.project_id
    if not (project_dir / ".git").exists():
        raise HTTPException(status_code=400, detail="Git repository not initialized.")

    files = _resolve_project_files(req.project_id, None)
    secret_findings = global_github_publisher.scan_for_secrets(files)
    if secret_findings:
        raise HTTPException(status_code=400, detail="Commit blocked: secrets detected in files.")

    global_git_service.add(project_dir)
    commit_res = global_git_service.commit(project_dir, message=req.message)
    return {"success": commit_res.success, "stdout": commit_res.stdout}


@router.post("/api/github/push")
def git_push_endpoint(req: GitPushRequest):
    """Pushes git commits to remote."""
    project_dir = GENERATED_PROJECTS_DIR / req.project_id
    if not (project_dir / ".git").exists():
        raise HTTPException(status_code=400, detail="Git repository not initialized.")

    if req.remote_url:
        global_git_service.remote_add(project_dir, "origin", req.remote_url)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {
            "success": True,
            "stdout": "Everything up-to-date (Simulated)",
            "message": "Git push simulation complete."
        }

    push_res = global_git_service.push(project_dir, remote="origin", branch="main")
    return {"success": push_res.success, "stdout": push_res.stdout or push_res.stderr}


@router.post("/api/github/branch")
def git_branch_endpoint(req: GitBranchRequest):
    """Creates and checkouts a new feature branch."""
    project_dir = GENERATED_PROJECTS_DIR / req.project_id
    if not (project_dir / ".git").exists():
        raise HTTPException(status_code=400, detail="Git repository not initialized.")

    branch_res = global_git_service.branch(project_dir, req.branch_name)
    return {"success": branch_res.success, "stdout": branch_res.stdout or branch_res.stderr}


@router.post("/api/github/pull-request")
def git_pull_request_endpoint(req: GitPullRequestRequest):
    """Creates a Pull Request from head branch to base branch."""
    repo_name = global_github_service.get_pr_dashboard_overview(req.project_id).get("connected_repository")
    if not repo_name:
        raise HTTPException(status_code=400, detail="Project is not published to GitHub yet; publish it before opening a pull request.")
    if not os.getenv("GITHUB_TOKEN"):
        raise HTTPException(status_code=400, detail="GITHUB_TOKEN is not configured.")

    try:
        pr = global_pr_generator.create_pull_request(
            full_repo_name=repo_name,
            title=req.title,
            head_branch=req.head_branch,
            problem=req.body or "Auto-fix transaction issues",
            project_id=req.project_id
        )
        return {
            "success": True,
            "pr_number": pr.number,
            "html_url": pr.html_url,
            "title": pr.title,
            "message": f"Pull Request #{pr.number} generated successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/github/overview")
def github_overview_endpoint(project_id: str = "aiforge-demo"):
    """Returns overview of connected repo, branches, PRs, and CI status."""
    return global_github_service.get_pr_dashboard_overview(project_id=project_id)


@router.post("/api/github/copilot")
def github_copilot_endpoint(req: CopilotGithubRequest):
    """Handles AI queries regarding CI pipeline logs, PRs, and branch code."""
    return global_github_service.handle_copilot_github_query(req.project_id, req.query, full_repo_name=req.full_repo_name)
