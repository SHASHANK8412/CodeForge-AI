"""
AIForge Day 31 — Intelligent Kubernetes Orchestration Module
"""
from backend.kubernetes.client import get_k8s_client
from backend.kubernetes.service import global_kubernetes_service

__all__ = [
    "get_k8s_client",
    "global_kubernetes_service"
]
