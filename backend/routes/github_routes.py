import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.generators.project_generator import GENERATED_PROJECTS_DIR
from backend.github.service import global_github_service
from backend.github.repositories import global_repository_analyzer
from backend.github.branches import global_branch_manager
from backend.github.commits import global_commit_manager
from backend.github.pull_requests import global_pr_generator

logger = logging.getLogger("aiforge.routes.github")

router = APIRouter(tags=["GitHub Integration"])


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


class GithubConnectRequest(BaseModel):
    repo_url: str
    project_id: str = "aiforge-demo"
    token: Optional[str] = None


def _run_git_cmd(project_dir: Path, cmd: str) -> str:
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode != 0:
            return f"Error: {res.stderr.strip()}"
        return res.stdout.strip()
    except Exception as e:
        return f"Git exception: {str(e)}"


@router.post("/api/github/git-init")
def git_init_endpoint(req: GitInitRequest):
    """Initializes local git repository and creates technology-appropriate .gitignore."""
    project_dir = GENERATED_PROJECTS_DIR / req.project_id
    if not project_dir.exists():
        project_dir.mkdir(parents=True, exist_ok=True)

    # Run git init
    out = _run_git_cmd(project_dir, "git init")

    # Create standard .gitignore
    gitignore_path = project_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = (
            "# Node\nnode_modules/\ndist/\nbuild/\n\n"
            "# Python\n__pycache__/\n*.pyc\n.venv/\nvenv/\n\n"
            "# Secrets\n.env\n*.key\nsecrets/\n"
        )
        gitignore_path.write_text(gitignore_content, encoding="utf-8")

    return {
        "success": True,
        "stdout": out,
        "message": "Git repository initialized with .gitignore successfully."
    }


@router.get("/api/github/git-status")
def git_status_endpoint(project_id: str = "aiforge-demo"):
    """Returns local git status output."""
    project_dir = GENERATED_PROJECTS_DIR / project_id
    if not (project_dir / ".git").exists():
        return {"success": False, "stdout": "Git not initialized. Click 'Git Init' to configure."}
    
    out = _run_git_cmd(project_dir, "git status")
    return {"success": True, "stdout": out}


@router.post("/api/github/commit")
def git_commit_endpoint(req: GitCommitRequest):
    """Stages all workspace files and creates a Git commit."""
    project_dir = GENERATED_PROJECTS_DIR / req.project_id
    if not (project_dir / ".git").exists():
        raise HTTPException(status_code=400, detail="Git repository not initialized.")

    # Prevent committing secrets - scan first
    from backend.routes.deployment import _read_project_files, scan_secrets
    files = _read_project_files(project_dir)
    secret_findings = scan_secrets(files)
    if secret_findings:
        raise HTTPException(status_code=400, detail="Commit blocked: secrets detected in files.")

    # Configure mock user config if not already configured
    _run_git_cmd(project_dir, 'git config user.name "AIForge Agent"')
    _run_git_cmd(project_dir, 'git config user.email "agent@aiforge.dev"')

    # Git add and commit
    _run_git_cmd(project_dir, "git add .")
    out = _run_git_cmd(project_dir, f'git commit -m "{req.message}"')
    
    return {"success": "error" not in out.lower(), "stdout": out}


@router.post("/api/github/push")
def git_push_endpoint(req: GitPushRequest):
    """Pushes git commits to the designated GitHub repository."""
    project_dir = GENERATED_PROJECTS_DIR / req.project_id
    if not (project_dir / ".git").exists():
        raise HTTPException(status_code=400, detail="Git repository not initialized.")

    # Configure remote url if specified
    if req.remote_url:
        _run_git_cmd(project_dir, f"git remote add origin {req.remote_url}")

    # For safety/mock environment, we simulate a successful push unless a real GITHUB_TOKEN is active
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {
            "success": True,
            "stdout": "Everything up-to-date (Simulated)",
            "message": "Git push simulation complete."
        }

    out = _run_git_cmd(project_dir, "git push -u origin main")
    return {"success": "error" not in out.lower(), "stdout": out}


@router.post("/api/github/branch")
def git_branch_endpoint(req: GitBranchRequest):
    """Creates and checkouts a new feature branch."""
    project_dir = GENERATED_PROJECTS_DIR / req.project_id
    if not (project_dir / ".git").exists():
        raise HTTPException(status_code=400, detail="Git repository not initialized.")

    out = _run_git_cmd(project_dir, f"git checkout -b {req.branch_name}")
    return {"success": "error" not in out.lower(), "stdout": out}


@router.post("/api/github/pull-request")
def git_pull_request_endpoint(req: GitPullRequestRequest):
    """Creates a Pull Request from head branch to base branch."""
    repo_overview = global_github_service.get_pr_dashboard_overview(req.project_id)
    repo_name = repo_overview.get("connected_repository", "SHASHANK8412/CodeForge-AI")

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


@router.post("/api/github/connect")
def github_connect_endpoint(req: GithubConnectRequest):
    """Connects project to a remote GitHub repository URL."""
    return global_repository_analyzer.connect_repository(req.repo_url, project_id=req.project_id, token=req.token)


@router.post("/api/github/copilot")
def github_copilot_endpoint(req: CopilotGithubRequest):
    """Handles AI queries regarding CI pipeline logs, PRs, and branch code."""
    return global_github_service.handle_copilot_github_query(req.project_id, req.query, full_repo_name=req.full_repo_name)
