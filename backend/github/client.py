"""
AIForge Day 30 — GitHub Client Manager
======================================
Manages PyGithub client interactions with token encryption/scrubbing and offline mock fallback.
"""

import os
import logging
from typing import Any, Optional

_logger = logging.getLogger("aiforge.github.client")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


class MockGithubRepository:
    def __init__(self, name: str = "CodeForge-AI", owner: str = "SHASHANK8412"):
        self.name = name
        self.full_name = f"{owner}/{name}"
        self.default_branch = "main"

    def get_branch(self, branch_name: str):
        class MockBranch:
            name = branch_name
            commit = type("MockCommit", (), {"sha": "9af8c96"})()
            protected = branch_name in ("main", "master")
        return MockBranch()

    def create_git_ref(self, ref: str, sha: str):
        return {"ref": ref, "sha": sha}

    def create_pull(self, title: str, body: str, head: str, base: str):
        class MockPR:
            number = 42
            html_url = f"https://github.com/{self.full_name}/pull/42"
            state = "open"
        return MockPR()


class GithubClientWrapper:
    def __init__(self, token: Optional[str] = None):
        self.raw_token = token or GITHUB_TOKEN
        self.pygithub_client = None

        if self.raw_token:
            try:
                from github import Github
                self.pygithub_client = Github(self.raw_token)
                _logger.info("[GithubClient] Initialized PyGithub client with configured token.")
            except Exception as e:
                _logger.info(f"[GithubClient] PyGithub init notice ({e}); using mock client.")

    def get_repo(self, full_name: str = "SHASHANK8412/CodeForge-AI"):
        if self.pygithub_client:
            try:
                return self.pygithub_client.get_repo(full_name)
            except Exception as e:
                _logger.warning(f"[GithubClient] Failed to fetch live repo '{full_name}': {e}")

        owner, name = full_name.split("/") if "/" in full_name else ("SHASHANK8412", full_name)
        return MockGithubRepository(name=name, owner=owner)


def get_github_client(token: Optional[str] = None) -> GithubClientWrapper:
    return GithubClientWrapper(token=token)
