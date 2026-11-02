"""
AIForge Day 31 — Intelligent Kubernetes Orchestration Test Suite
==================================================================
Comprehensive unit and integration tests covering:
1. Manifest Generation & Validation (Deployments, Services, Ingress, Secrets, HPA, NetworkPolicy)
2. Secret Protection & SecretKeyRef Enforcement
3. Non-Root Security Context & Resource Limits
4. Health Probes (Liveness, Readiness, Startup)
5. Rolling Updates & Automated Rollback on Smoke/Readiness Failure
6. HPA Scaling & Performance Engineer Approval Policies
7. Project & Namespace Isolation
8. Command Allowlist Enforcement (Blocking arbitrary kubectl exec/apply/delete)
9. Architecture Simulator Trade-Off Evaluation
10. Kubernetes Provider Integration
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.kubernetes.manifests import ManifestGenerator
from backend.kubernetes.deployment import RollingDeploymentManager
from backend.kubernetes.scaling import KubernetesScalingManager, K8sScaleRequest
from backend.kubernetes.health import HealthProbeManager
from backend.kubernetes.rollback import KubernetesRollbackEngine
from backend.kubernetes.service import KubernetesService, COMMAND_ALLOWLIST
from backend.devops.providers.factory import DeploymentProviderFactory
from backend.devops.providers.kubernetes import KubernetesProvider


@pytest.fixture
def client():
    return TestClient(app)


class TestKubernetesSuite:

    def test_manifest_generation_and_security_validation(self):
        gen = ManifestGenerator()
        m_set = gen.generate_manifests(project_id="proj_alpha", namespace="aiforge-proj_alpha")

        assert m_set.is_valid is True
        assert "runAsNonRoot: true" in m_set.deployments_yaml
        assert "secretRef:" in m_set.deployments_yaml
        assert "resources:" in m_set.deployments_yaml
        assert "kind: NetworkPolicy" in m_set.network_policies_yaml
        assert "kind: HorizontalPodAutoscaler" in m_set.hpa_yaml

    def test_secret_protection_detects_plaintext_secrets(self):
        gen = ManifestGenerator()
        clean_set = gen.generate_manifests()

        # Inject plaintext password into YAML
        dirty_set = clean_set.model_copy() if hasattr(clean_set, "model_copy") else clean_set.copy()

        dirty_set.secrets_yaml = 'stringData:\n  password: "raw_secret_password_123"'

        val = gen.validate_manifests(dirty_set)
        assert val["is_valid"] is False
        assert any("Plaintext secret detected" in e for e in val["errors"])

    def test_non_root_security_context_and_resource_limits(self):
        gen = ManifestGenerator()
        m_set = gen.generate_manifests()

        assert "runAsNonRoot: true" in m_set.deployments_yaml
        assert "cpu: \"250m\"" in m_set.deployments_yaml
        assert "memory: \"256Mi\"" in m_set.deployments_yaml

    def test_health_probe_configuration(self):
        hpm = HealthProbeManager()
        probes = hpm.configure_probes(endpoint_path="/health", port=8000)

        assert probes["livenessProbe"].path == "/health"
        assert probes["readinessProbe"].port == 8000

    def test_rolling_deployment_is_not_reported_live(self):
        # Applying manifests to a cluster is not implemented: a deployment never reports LIVE or a passing smoke test.
        rdm = RollingDeploymentManager()
        ok, msg = rdm.execute_rolling_deployment("proj_alpha", "aiforge-proj_alpha", "v1.5", simulate_failure=False)
        assert ok is False and "Not deployed" in msg and "LIVE" not in msg
        fail_ok, fail_msg = rdm.execute_rolling_deployment("proj_alpha", "aiforge-proj_alpha", "v1.5-broken", simulate_failure=True)
        assert fail_ok is False and "nothing was deployed" in fail_msg

        result = KubernetesService().deploy(project_id="proj_alpha")
        assert result["success"] is False and result["status"] in ("NOT_DEPLOYED", "BLOCKED_BY_READINESS_GATE")
        rb = KubernetesService().rollback("proj_alpha")
        assert rb.success is False and rb.status == "NOT_EXECUTED"

    def test_hpa_scaling_and_user_approval_policy(self):
        sm = KubernetesScalingManager()

        # Recommendation based on telemetry
        rec = sm.recommend_scaling("proj_alpha", component="backend", current_replicas=3, observed_cpu_pct=91.0, observed_p95_ms=680.0)
        assert rec.desired_replicas == 5
        assert "OBSERVED" in rec.reason

        # Unapproved scaling is rejected
        app_ok, app_msg = sm.apply_scale(rec, user_approved=False)
        assert app_ok is False
        assert "User approval required" in app_msg

        # Approval does not make an unimplemented cluster operation succeed
        app_ok_2, app_msg_2 = sm.apply_scale(rec, user_approved=True)
        assert app_ok_2 is False and "Not scaled" in app_msg_2

        # Without an explicit approval the default is a refusal
        assert sm.apply_scale(rec)[0] is False

    def test_command_allowlist_enforcement_blocks_arbitrary_kubectl(self):
        service = KubernetesService()

        # An allowed operation passes the allowlist, but is reported as not executed (not implemented)
        res = service.execute_command_allowlist_operation("get_pods", {})
        assert res["status"] == "NOT_IMPLEMENTED"

        # Arbitrary kubectl exec/apply/delete raises PermissionError
        with pytest.raises(PermissionError, match="not in the authorized Kubernetes allowlist"):
            service.execute_command_allowlist_operation("kubectl_exec_rm_rf", {})

    def test_architecture_simulator_tradeoffs(self):
        service = KubernetesService()
        tradeoffs = service.evaluate_architecture_tradeoffs(current_mode="Docker")

        assert tradeoffs["complexity"] == "HIGH"
        assert "Docker remains optimal" in tradeoffs["recommendation"]

    def test_devops_deployment_provider_integration(self):
        provider = DeploymentProviderFactory.get_provider("Kubernetes")
        assert isinstance(provider, KubernetesProvider)
        assert provider.provider_name == "Kubernetes"

    def test_kubernetes_api_endpoints(self, client):
        status_res = client.get("/api/kubernetes/status?project_id=aiforge-demo")
        assert status_res.status_code == 200
        body = status_res.json()
        # no cluster is configured in tests: nothing about one is invented
        assert body["connected"] is False and body["mode"] == "not_connected"
        assert body["cluster_name"] is None and body["nodes_count"] is None and body["cpu_usage_pct"] is None
        assert not body["backend_pods"] and not body["frontend_pods"]
        assert client.get("/api/kubernetes/events?project_id=aiforge-demo").json() == []

        manifests_res = client.post("/api/kubernetes/manifests?project_id=aiforge-demo")
        assert manifests_res.status_code == 200
        assert manifests_res.json()["is_valid"] is True
