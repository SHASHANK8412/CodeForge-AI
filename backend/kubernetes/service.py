"""
AIForge Kubernetes service.

What is real: manifest generation and validation (non-root security contexts, resource limits, probes, network
policies, HPA, plaintext-secret detection), the HPA scaling recommendation and the command allowlist. When a real
cluster is reachable (kubeconfig or in-cluster config), status is read from it: nodes, version and the project's pods.

What is not implemented: applying manifests, scaling, rolling back or running commands against a cluster. Those
calls say so - they never report LIVE, HEALTHY or a completed action, and they write no audit event claiming one.
"""

import logging
from typing import Any, Dict, List, Optional

from backend.kubernetes.client import get_k8s_client
from backend.kubernetes.manifests import global_manifest_generator
from backend.kubernetes.deployment import global_rolling_deployment_manager
from backend.kubernetes.scaling import global_scaling_manager
from backend.kubernetes.rollback import global_k8s_rollback_engine
from backend.kubernetes.models import (
    K8sClusterStatus, K8sPodStatus, PodPhaseEnum, K8sManifestSet,
    K8sScaleRequest, K8sDeploymentEvent, K8sRollbackResult
)

_logger = logging.getLogger("aiforge.kubernetes.service")

COMMAND_ALLOWLIST = {
    "create_deployment", "update_deployment", "get_deployment",
    "scale_deployment", "get_pods", "get_service", "get_events", "rollback_deployment"
}
NOT_CONNECTED = ("No Kubernetes cluster is connected (no kubeconfig or in-cluster configuration was found): "
                 "nothing below was read from a cluster.")
WRITE_NOTE = "Applying, scaling and rolling back against a cluster is not implemented; manifests are generated only."


def _cluster_facts(client) -> Dict[str, Any]:
    """Nodes and version from a real cluster; empty when not connected or when a read fails."""
    if not client.is_connected():
        return {}
    facts: Dict[str, Any] = {}
    try:
        facts["nodes_count"] = len(client.core_api.list_node().items)
    except Exception as e:  # noqa: BLE001 - an unreadable fact stays unknown
        _logger.info("could not list nodes: %s", e)
    try:
        import kubernetes.client as k8s
        facts["k8s_version"] = k8s.VersionApi().get_code().git_version
    except Exception as e:  # noqa: BLE001
        _logger.info("could not read the cluster version: %s", e)
    try:
        from kubernetes import config as k8s_config
        _, active = k8s_config.list_kube_config_contexts()
        facts["cluster_name"] = (active or {}).get("context", {}).get("cluster")
    except Exception:  # noqa: BLE001 - in-cluster config has no context name
        pass
    return facts


class KubernetesService:
    """Kubernetes orchestration: manifests are real; cluster writes are not implemented and say so."""

    def validate_cluster(self, project_id: str = "aiforge-demo") -> Dict[str, Any]:
        client = get_k8s_client()
        connected = client.is_connected()
        return {"connected": connected, "namespace": f"aiforge-{project_id}", **_cluster_facts(client),
                "note": "" if connected else NOT_CONNECTED}

    def generate_manifests(
        self,
        project_id: str = "aiforge-demo",
        namespace: Optional[str] = None
    ) -> K8sManifestSet:
        ns = namespace or f"aiforge-{project_id}"
        return global_manifest_generator.generate_manifests(project_id=project_id, namespace=ns)

    def validate_manifests(self, manifest_set: K8sManifestSet) -> Dict[str, Any]:
        return global_manifest_generator.validate_manifests(manifest_set)

    def deploy(
        self,
        project_id: str = "aiforge-demo",
        image_tag: str = "v1.5",
        simulate_failure: bool = False
    ) -> Dict[str, Any]:
        ns = f"aiforge-{project_id}"
        # Check Production Readiness Gate
        try:
            from backend.readiness.service import global_readiness_service
            gate = global_readiness_service.evaluate_gate(project_id)
            if not gate.passed:
                _logger.warning(f"[K8sService] Deployment BLOCKED by Readiness Gate for project '{project_id}'")
                return {"success": False, "status": "BLOCKED_BY_READINESS_GATE", "reason": "Production Readiness Gate audit failed."}
        except Exception as e:  # noqa: BLE001 - a gate that cannot be evaluated does not approve anything
            _logger.warning("readiness gate unavailable: %s", e)
            return {"success": False, "status": "BLOCKED_BY_READINESS_GATE",
                    "reason": f"The Production Readiness Gate could not be evaluated ({type(e).__name__})."}

        _, msg = global_rolling_deployment_manager.execute_rolling_deployment(
            project_id=project_id,
            namespace=ns,
            image_tag=image_tag,
            simulate_failure=simulate_failure
        )
        return {"success": False, "status": "NOT_DEPLOYED", "simulated": True, "reason": msg, "message": msg}

    def get_status(self, project_id: str = "aiforge-demo") -> K8sClusterStatus:
        ns = f"aiforge-{project_id}"
        client = get_k8s_client()
        if not client.is_connected():
            return K8sClusterStatus(connected=False, namespace=ns, project_id=project_id, mode="not_connected",
                                    note=NOT_CONNECTED + " " + WRITE_NOTE)
        status = K8sClusterStatus(connected=True, namespace=ns, project_id=project_id, mode="read_only",
                                  note=WRITE_NOTE + " CPU, memory, latency and error rates are not measured.",
                                  **_cluster_facts(client))
        try:
            for pod in client.core_api.list_namespaced_pod(ns).items:
                labels = (pod.metadata.labels or {})
                component = labels.get("component") or labels.get("app") or "other"
                statuses = pod.status.container_statuses or []
                image = pod.spec.containers[0].image if pod.spec.containers else ""
                p = K8sPodStatus(name=pod.metadata.name, component=component,
                                 status=PodPhaseEnum(pod.status.phase) if pod.status.phase in PodPhaseEnum._value2member_map_ else PodPhaseEnum.PENDING,
                                 ready=all(c.ready for c in statuses) if statuses else False,
                                 restarts=sum(c.restart_count for c in statuses), cpu_percent=0.0, memory_mb=0.0,
                                 version=image.rsplit(":", 1)[-1] if ":" in image else "", image=image)
                {"frontend": status.frontend_pods, "backend": status.backend_pods, "redis": status.redis_pods}.get(
                    component, status.other_pods).append(p)
        except Exception as e:  # noqa: BLE001 - pods stay unknown, and the note says why
            status.note += f" Pods could not be listed: {type(e).__name__}."
        return status

    def scale(self, request: K8sScaleRequest, user_approved: bool = False) -> Dict[str, Any]:
        success, msg = global_scaling_manager.apply_scale(request, user_approved=user_approved)
        req_dict = request.model_dump() if hasattr(request, "model_dump") else request.dict()
        return {"success": success, "status": "NOT_EXECUTED" if user_approved else "APPROVAL_REQUIRED",
                "message": msg, "request": req_dict}

    def health_check(self, project_id: str = "aiforge-demo") -> Dict[str, Any]:
        return {"status": "NOT_DEPLOYED", "liveness": "NOT_RUN", "readiness": "NOT_RUN", "startup": "NOT_RUN",
                "note": "Nothing is deployed to a cluster, so no probe ran. " + WRITE_NOTE}

    def rollback(self, project_id: str = "aiforge-demo") -> K8sRollbackResult:
        return global_k8s_rollback_engine.rollback_deployment(project_id=project_id)

    def get_events(self, project_id: str = "aiforge-demo") -> List[K8sDeploymentEvent]:
        """No deployment events exist: nothing was ever applied to a cluster."""
        return []

    def evaluate_architecture_tradeoffs(self, current_mode: str = "Docker") -> Dict[str, Any]:
        return {
            "current_mode": current_mode,
            "proposed_mode": "Kubernetes",
            "complexity": "HIGH",
            "operational_overhead": "HIGH",
            "scalability": "EXCELLENT",
            "cost": "POTENTIALLY_HIGHER",
            "recommendation": "Use Kubernetes only if traffic scaling, high availability, or multi-service orchestration requires it. Docker remains optimal for local & medium-scale deployments."
        }

    def execute_command_allowlist_operation(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if command not in COMMAND_ALLOWLIST:
            raise PermissionError(f"Command '{command}' is not in the authorized Kubernetes allowlist. Arbitrary kubectl commands are strictly prohibited.")
        return {"command": command, "status": "NOT_IMPLEMENTED",
                "result": "Allowed, but not executed: running cluster operations is not implemented."}


global_kubernetes_service = KubernetesService()
