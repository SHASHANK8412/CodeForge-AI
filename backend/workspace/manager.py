"""
AIForge Workspace Manager (Compatibility Wrapper)
=================================================
Re-exports WorkspaceManager and global_workspace_manager from workspace_manager.py.
"""

from backend.workspace.workspace_manager import WorkspaceManager, global_workspace_manager

__all__ = ["WorkspaceManager", "global_workspace_manager"]
