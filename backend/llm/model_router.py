"""
AIForge Model Router (Compatibility Wrapper)
============================================
Re-exports DynamicModelRouter and global_dynamic_model_router from router.py.
"""

from backend.llm.router import DynamicModelRouter, global_dynamic_model_router

__all__ = ["DynamicModelRouter", "global_dynamic_model_router"]
