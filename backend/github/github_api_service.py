"""
AIForge Autonomous GitHub REST API Service
==========================================
Coordinates official GitHub REST API v3 operations:
- Token validation & user identity lookup
- Rate limit checking
- Repository creation (private by default)
- Repository metadata inspection
- Graceful offline/simulation mode when no token is configured
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("aiforge.github.api_service")


class GitHubAPIError(Exception):
    """Base exception for GitHub API failures."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class GitHubAuthError(GitHubAPIError):
    """Raised when GitHub token is invalid or missing."""
    pass


class GitHubRepoExistsError(GitHubAPIError):
    """Raised when repository name already exists."""
    pass


class GitHubRateLimitError(GitHubAPIError):
    """Raised when GitHub rate limit is exceeded."""
    pass


class GitHubAPIService:
    """
    Direct client for GitHub REST API v3 using standard Python HTTP.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self._custom_token = token

    @property
    def token(self) -> str:
        return self._custom_token or os.getenv("GITHUB_TOKEN", "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    def _get_headers(self, token_override: Optional[str] = None) -> Dict[str, str]:
        tok = token_override or self.token
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AIForge-Autonomous-Engineer/2.0"
        }
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        return headers

    def validate_repo_name(self, repo_name: str) -> str:
        """
        Validates and cleanses GitHub repository names.
        Rules: 1-100 characters, alphanumeric, hyphens, underscores, dots.
        """
        clean = repo_name.strip()
        if not clean:
            raise ValueError("Repository name cannot be empty.")
        if len(clean) > 100:
            clean = clean[:100]

        # Replace spaces with hyphens and remove illegal characters
        clean = re.sub(r"\s+", "-", clean)
        clean = re.sub(r"[^a-zA-Z0-9._-]", "", clean)
        clean = clean.strip(".-")

        if not clean:
            raise ValueError(f"Invalid repository name after sanitization: '{repo_name}'")
        return clean

    def _http_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        token_override: Optional[str] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Executes an HTTP request to the GitHub API.
        """
        import urllib.request
        import urllib.error

        url = f"{self.BASE_URL}{endpoint}" if endpoint.startswith("/") else endpoint
        headers = self._get_headers(token_override)
        encoded_data = json.dumps(data).encode("utf-8") if data is not None else None

        if data is not None:
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status_code = resp.getcode()
                body_bytes = resp.read()
                res_json = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                return status_code, res_json
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
            except Exception:
                err_json = {"message": err_body}

            msg = err_json.get("message", f"HTTP {he.code}")

            if he.code == 401:
                raise GitHubAuthError(f"GitHub authentication failed: {msg}", status_code=401, details=err_json)
            elif he.code == 403 and "rate limit" in msg.lower():
                raise GitHubRateLimitError(f"GitHub API rate limit exceeded: {msg}", status_code=403, details=err_json)
            elif he.code == 422 and ("already exists" in msg.lower() or any("already exists" in str(e).lower() for e in err_json.get("errors", []))):
                raise GitHubRepoExistsError(f"Repository already exists on GitHub: {msg}", status_code=422, details=err_json)
            else:
                raise GitHubAPIError(f"GitHub API error ({he.code}): {msg}", status_code=he.code, details=err_json)
        except Exception as ex:
            if isinstance(ex, GitHubAPIError):
                raise
            raise GitHubAPIError(f"Network error communicating with GitHub API: {ex}", status_code=503)

    def verify_credentials(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Verifies GitHub authentication and returns user information.
        """
        tok = token or self.token
        if not tok:
            # Simulated fallback for offline local mode
            return {
                "authenticated": True,
                "simulated": True,
                "login": "aiforge-local-developer",
                "name": "AIForge Local Developer",
                "rate_limit_remaining": 5000,
                "message": "Simulated local GitHub connection active (no token configured)."
            }

        status_code, data = self._http_request("GET", "/user", token_override=tok)
        return {
            "authenticated": True,
            "simulated": False,
            "login": data.get("login", "unknown"),
            "name": data.get("name") or data.get("login"),
            "html_url": data.get("html_url", ""),
            "public_repos": data.get("public_repos", 0),
            "total_private_repos": data.get("total_private_repos", 0),
            "rate_limit_remaining": 5000
        }

    def get_rate_limit(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Checks current GitHub API rate limit.
        """
        tok = token or self.token
        if not tok:
            return {"limit": 5000, "remaining": 5000, "reset": 0, "simulated": True}

        try:
            _, data = self._http_request("GET", "/rate_limit", token_override=tok)
            rate = data.get("rate", {})
            return {
                "limit": rate.get("limit", 5000),
                "remaining": rate.get("remaining", 5000),
                "reset": rate.get("reset", 0),
                "simulated": False
            }
        except Exception as e:
            logger.warning(f"Could not check rate limit: {e}")
            return {"limit": 5000, "remaining": 5000, "reset": 0, "simulated": True}

    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = True,
        org: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new GitHub repository for the user or organization.
        Default visibility is private.
        """
        valid_name = self.validate_repo_name(name)
        tok = token or self.token

        if not tok:
            # Simulated offline response
            safe_owner = org or "aiforge-dev"
            repo_url = f"https://github.com/{safe_owner}/{valid_name}"
            return {
                "id": f"gh_{valid_name}_mock",
                "name": valid_name,
                "full_name": f"{safe_owner}/{valid_name}",
                "html_url": repo_url,
                "clone_url": f"{repo_url}.git",
                "ssh_url": f"git@github.com:{safe_owner}/{valid_name}.git",
                "private": private,
                "default_branch": "main",
                "description": description,
                "owner": {"login": safe_owner},
                "simulated": True
            }

        endpoint = f"/orgs/{org}/repos" if org else "/user/repos"
        payload = {
            "name": valid_name,
            "description": description or f"Autonomously generated by AIForge: {valid_name}",
            "private": private,
            "auto_init": False  # Crucial: local git push will provide root commit
        }

        status_code, data = self._http_request("POST", endpoint, data=payload, token_override=tok)
        return {
            "id": str(data.get("id", "")),
            "name": data.get("name", valid_name),
            "full_name": data.get("full_name", f"user/{valid_name}"),
            "html_url": data.get("html_url", f"https://github.com/{valid_name}"),
            "clone_url": data.get("clone_url", f"https://github.com/{valid_name}.git"),
            "ssh_url": data.get("ssh_url", ""),
            "private": data.get("private", private),
            "default_branch": data.get("default_branch", "main"),
            "description": data.get("description", description),
            "owner": {"login": data.get("owner", {}).get("login", "unknown")},
            "simulated": False
        }

    def get_repository(self, owner: str, repo: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches repository details.
        """
        tok = token or self.token
        if not tok:
            return {
                "name": repo,
                "full_name": f"{owner}/{repo}",
                "html_url": f"https://github.com/{owner}/{repo}",
                "default_branch": "main",
                "private": True,
                "simulated": True
            }

        try:
            _, data = self._http_request("GET", f"/repos/{owner}/{repo}", token_override=tok)
            return data
        except GitHubAPIError as err:
            if err.status_code == 404:
                return None
            raise


global_github_api_service = GitHubAPIService()
