"""
AIForge Day 12 - Git Workflow Configuration & Remote Action Policy
===================================================================
Enforces safety rules, feature flags, and authorization policies for
Git and remote GitHub interactions.
"""

import os
import logging
from typing import Dict, Any, Optional
from backend.git_workflow.models import RemoteActionType

logger = logging.getLogger("aiforge.git_workflow.config")


class GitWorkflowConfig:
    """
    Feature flags and safety policies for AIForge Day 12 Git Workflows.
    """

    def __init__(self):
        self.git_workflow_enabled: bool = self._get_bool_env("AIFORGE_GIT_WORKFLOW_ENABLED", True)
        self.git_worktree_enabled: bool = self._get_bool_env("AIFORGE_GIT_WORKTREE_ENABLED", True)
        self.local_commit_enabled: bool = self._get_bool_env("AIFORGE_LOCAL_COMMIT_ENABLED", True)
        self.remote_push_enabled: bool = self._get_bool_env("AIFORGE_REMOTE_PUSH_ENABLED", False)
        self.pr_creation_enabled: bool = self._get_bool_env("AIFORGE_PR_CREATION_ENABLED", False)
        self.auto_merge_enabled: bool = self._get_bool_env("AIFORGE_AUTO_MERGE_ENABLED", False)
        self.force_push_enabled: bool = self._get_bool_env("AIFORGE_FORCE_PUSH_ENABLED", False)

    def _get_bool_env(self, key: str, default: bool) -> bool:
        val = os.getenv(key)
        if val is None:
            return default
        return val.lower() in ("true", "1", "yes", "on")


class RemoteActionPolicy:
    """
    Evaluates permission and policy rules before performing any remote or Git operation.
    """

    def __init__(self, config: Optional[GitWorkflowConfig] = None):
        self.config = config or GitWorkflowConfig()

    def is_action_allowed(self, action: RemoteActionType, user_override: bool = False) -> bool:
        """
        Check if a remote action is permitted under the current security policy.
        """
        if action == RemoteActionType.FETCH:
            return True

        if action == RemoteActionType.FORCE_PUSH:
            # Force push is strictly disabled on Day 12
            if not self.config.force_push_enabled:
                logger.warning("RemoteActionPolicy: FORCE_PUSH blocked by security policy.")
                return False
            return user_override

        if action == RemoteActionType.MERGE_PR:
            # Auto merge is strictly disabled on Day 12
            if not self.config.auto_merge_enabled:
                logger.warning("RemoteActionPolicy: MERGE_PR blocked by security policy.")
                return False
            return user_override

        if action == RemoteActionType.PUSH:
            return self.config.remote_push_enabled or user_override

        if action == RemoteActionType.CREATE_PR:
            return self.config.pr_creation_enabled or user_override

        if action in (RemoteActionType.DELETE_REMOTE_BRANCH, RemoteActionType.CLOSE_ISSUE):
            return user_override

        return True


global_git_config = GitWorkflowConfig()
global_remote_policy = RemoteActionPolicy(global_git_config)
