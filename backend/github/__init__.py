"""
AIForge Day 30 — GitHub Integration & Autonomous Pull Request Engineering Module
"""
from backend.github.client import get_github_client
from backend.github.service import global_github_service

__all__ = [
    "get_github_client",
    "global_github_service"
]
