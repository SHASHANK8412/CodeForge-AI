"""
AIForge Node Manager & Cloud Deployment Profiles
=================================================
Manages cluster node registration and maintains cloud deployment profiles (AWS EKS, Azure AKS, GCP GKE, DigitalOcean, Kubernetes, Docker Swarm).
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.distributed.node_manager")


class NodeManager:
    """
    Manages active worker nodes and cloud cluster deployment profiles.
    """

    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {
            "worker_node_1": {
                "node_id": "worker_node_1",
                "host": "10.0.0.12",
                "capacity": 4,
                "status": "ONLINE",
                "active_tasks_count": 1,
                "cloud_provider": "AWS EKS",
                "last_heartbeat": time.time()
            },
            "worker_node_2": {
                "node_id": "worker_node_2",
                "host": "10.0.0.13",
                "capacity": 4,
                "status": "ONLINE",
                "active_tasks_count": 0,
                "cloud_provider": "AWS EKS",
                "last_heartbeat": time.time()
            },
            "worker_node_3": {
                "node_id": "worker_node_3",
                "host": "10.0.0.14",
                "capacity": 4,
                "status": "ONLINE",
                "active_tasks_count": 2,
                "cloud_provider": "AWS EKS",
                "last_heartbeat": time.time()
            }
        }

    def register_node(
        self,
        node_id: str,
        host: str = "10.0.0.20",
        capacity: int = 4,
        cloud_provider: str = "AWS EKS"
    ) -> Dict[str, Any]:
        node = {
            "node_id": node_id,
            "host": host,
            "capacity": capacity,
            "status": "ONLINE",
            "active_tasks_count": 0,
            "cloud_provider": cloud_provider,
            "last_heartbeat": time.time()
        }
        self.nodes[node_id] = node
        _logger.info(f"NodeManager: Registered new worker node '{node_id}' ({cloud_provider} @ {host})")
        return node

    def update_node_heartbeat(self, node_id: str) -> bool:
        if node_id in self.nodes:
            self.nodes[node_id]["last_heartbeat"] = time.time()
            self.nodes[node_id]["status"] = "ONLINE"
            return True
        return False

    def list_nodes(self) -> List[Dict[str, Any]]:
        return list(self.nodes.values())

    def get_cloud_deployment_profiles(self) -> Dict[str, Any]:
        return {
            "supported_platforms": ["AWS EKS", "Azure AKS", "Google Cloud GKE", "DigitalOcean DOKS", "Kubernetes", "Docker Swarm"],
            "profiles": [
                {"platform": "AWS EKS", "container_runtime": "containerd", "recommended_instance": "t3.xlarge"},
                {"platform": "Azure AKS", "container_runtime": "containerd", "recommended_instance": "Standard_D4s_v3"},
                {"platform": "Google Cloud GKE", "container_runtime": "containerd", "recommended_instance": "e2-standard-4"},
                {"platform": "Kubernetes Local", "container_runtime": "docker", "recommended_instance": "Minikube / MicroK8s"}
            ]
        }


global_node_manager = NodeManager()
