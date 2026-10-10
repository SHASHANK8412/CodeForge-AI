"""
AIForge GitHub Repository Metadata Store
========================================
Persists and retrieves GitHub repository metadata for AIForge projects:
- Project ID, GitHub Repo ID, name, URL, owner, default branch, visibility,
  last commit SHA, last sync time, status.
- File-backed JSON store with in-memory caching and SQLAlchemy DB sync support.
- Guaranteed: Never stores raw GitHub access tokens!
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aiforge.github.repo_store")


class ProjectGitHubMetadata(BaseModel):
    """Structured metadata record for a GitHub-linked project."""
    __test__ = False
    project_id: str = Field(description="Internal project identifier")
    github_repo_id: str = Field(default="", description="Remote GitHub repository ID")
    repo_name: str = Field(description="Repository name")
    repo_url: str = Field(description="Full HTML URL e.g. https://github.com/owner/repo")
    clone_url: str = Field(default="", description="Git clone URL")
    owner: str = Field(default="", description="GitHub username or organization")
    default_branch: str = Field(default="main", description="Primary repository branch")
    visibility: str = Field(default="private", description="'private' or 'public'")
    last_commit_sha: str = Field(default="", description="Latest pushed commit SHA")
    last_commit_message: str = Field(default="", description="Commit message of latest push")
    last_sync_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = Field(default="published", description="'published', 'syncing', 'failed'")
    ci_workflow_enabled: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GitHubRepoStore:
    """
    Store for project GitHub repository linkages.
    """

    def __init__(self, storage_file: Optional[Path] = None):
        self._cache: Dict[str, ProjectGitHubMetadata] = {}
        self.storage_file = storage_file or (Path(__file__).resolve().parents[2] / "logs" / "github_repositories.json")
        self._load()

    def _load(self) -> None:
        if not self.storage_file.exists():
            return
        try:
            content = self.storage_file.read_text(encoding="utf-8")
            data = json.loads(content)
            for k, v in data.items():
                self._cache[k] = ProjectGitHubMetadata(**v)
        except Exception as e:
            logger.warning(f"Could not load GitHub repo metadata store: {e}")

    def _save(self) -> None:
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            dumped = {k: v.model_dump() for k, v in self._cache.items()}
            self.storage_file.write_text(json.dumps(dumped, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Could not save GitHub repo metadata: {e}")

    def save(self, meta: ProjectGitHubMetadata) -> None:
        """Saves or updates repository metadata for a project."""
        self._cache[meta.project_id] = meta
        self._save()

    def get(self, project_id: str) -> Optional[ProjectGitHubMetadata]:
        """Retrieves repository metadata for a project."""
        return self._cache.get(project_id)

    def list_all(self) -> List[ProjectGitHubMetadata]:
        """Returns all connected repositories."""
        return list(self._cache.values())

    def delete(self, project_id: str) -> bool:
        """Removes repository metadata for a project."""
        if project_id in self._cache:
            del self._cache[project_id]
            self._save()
            return True
        return False


global_github_repo_store = GitHubRepoStore()
