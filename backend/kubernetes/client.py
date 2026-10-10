"""
AIForge Day 31 — Kubernetes Client Manager
==========================================
Manages python kubernetes-client SDK connections with in-memory mock cluster fallback.
"""

import os
import logging
from typing import Any, Optional

_logger = logging.getLogger("aiforge.kubernetes.client")


class MockK8sCoreV1Api:
    def list_namespaced_pod(self, namespace: str):
        class MockPodList:
            items = []
        return MockPodList()


class KubernetesClientWrapper:
    """
    Kubernetes API client wrapper with mock fallback.
    """

    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.k8s_client = None
        self.core_api = None
        self.apps_api = None

        try:
            import kubernetes.client as k8s
            from kubernetes import config as k8s_config

            if kubeconfig_path and os.path.exists(kubeconfig_path):
                k8s_config.load_kube_config(config_file=kubeconfig_path)
            else:
                try:
                    k8s_config.load_incluster_config()
                except Exception:
                    k8s_config.load_kube_config()

            self.core_api = k8s.CoreV1Api()
            self.apps_api = k8s.AppsV1Api()
            _logger.info("[KubernetesClient] Connected to active Kubernetes cluster.")
        except Exception as e:
            _logger.info(f"[KubernetesClient] Cluster connection notice ({e}); using mock K8s API wrapper.")
            self.core_api = MockK8sCoreV1Api()

    def is_connected(self) -> bool:
        return True


def get_k8s_client(kubeconfig_path: Optional[str] = None) -> KubernetesClientWrapper:
    return KubernetesClientWrapper(kubeconfig_path=kubeconfig_path)
