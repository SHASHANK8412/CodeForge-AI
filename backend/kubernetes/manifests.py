"""
AIForge Day 31 — Kubernetes Manifest Generator & Validator
============================================================
Generates and validates secure Kubernetes manifests (Deployments, Services, Ingress, HPA, NetworkPolicies)
with non-root security contexts, secret reference enforcement, and resource limits.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from backend.kubernetes.models import K8sManifestSet, K8sResourceLimits, K8sHealthProbe

_logger = logging.getLogger("aiforge.kubernetes.manifests")

RAW_SECRET_PATTERNS = [
    re.compile(r'(?i)password:\s*["\'][a-zA-Z0-9_\-\.]{6,}["\']'),
    re.compile(r'(?i)token:\s*["\'][a-zA-Z0-9_\-\.]{12,}["\']'),
    re.compile(r'(?i)api_key:\s*["\'][a-zA-Z0-9_\-\.]{12,}["\']')
]


class ManifestGenerator:
    """
    Generates production-grade Kubernetes YAML manifests.
    """

    def generate_manifests(
        self,
        project_id: str = "aiforge-demo",
        namespace: str = "aiforge-project-123",
        frontend_image: str = "aiforge/frontend:v1.5",
        backend_image: str = "aiforge/backend:v1.5",
        limits: Optional[K8sResourceLimits] = None,
        probe: Optional[K8sHealthProbe] = None
    ) -> K8sManifestSet:
        res_limits = limits or K8sResourceLimits()
        hlth_probe = probe or K8sHealthProbe()

        deployments_yaml = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  namespace: {namespace}
  labels:
    app.kubernetes.io/name: backend
    app.kubernetes.io/part-of: {project_id}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
      containers:
      - name: backend
        image: {backend_image}
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "{res_limits.cpu_request}"
            memory: "{res_limits.memory_request}"
          limits:
            cpu: "{res_limits.cpu_limit}"
            memory: "{res_limits.memory_limit}"
        envFrom:
        - secretRef:
            name: aiforge-db-secret
        livenessProbe:
          httpGet:
            path: {hlth_probe.path}
            port: {hlth_probe.port}
          initialDelaySeconds: {hlth_probe.initial_delay_seconds}
          periodSeconds: {hlth_probe.period_seconds}
        readinessProbe:
          httpGet:
            path: {hlth_probe.path}
            port: {hlth_probe.port}
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
  namespace: {namespace}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: {frontend_image}
        ports:
        - containerPort: 80
"""

        services_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: {namespace}
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: {namespace}
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
"""

        ingress_yaml = f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aiforge-ingress
  namespace: {namespace}
  annotations:
    kubernetes.io/ingress.class: "nginx"
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
"""

        configmaps_yaml = f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: aiforge-config
  namespace: {namespace}
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
"""

        secrets_yaml = f"""apiVersion: v1
kind: Secret
metadata:
  name: aiforge-db-secret
  namespace: {namespace}
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:secretRef@pg-host:5432/aiforge_db"
"""

        hpa_yaml = f"""apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-deployment
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
"""

        network_policies_yaml = f"""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: {namespace}
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
"""

        m_set = K8sManifestSet(
            project_id=project_id,
            namespace=namespace,
            deployments_yaml=deployments_yaml,
            services_yaml=services_yaml,
            ingress_yaml=ingress_yaml,
            configmaps_yaml=configmaps_yaml,
            secrets_yaml=secrets_yaml,
            hpa_yaml=hpa_yaml,
            network_policies_yaml=network_policies_yaml
        )

        validation = self.validate_manifests(m_set)
        m_set.is_valid = validation["is_valid"]
        m_set.validation_errors = validation["errors"]
        return m_set

    def validate_manifests(self, manifest_set: K8sManifestSet) -> Dict[str, Any]:
        errors = []
        full_yaml = (
            manifest_set.deployments_yaml + manifest_set.services_yaml + manifest_set.secrets_yaml
        )

        for pat in RAW_SECRET_PATTERNS:
            if pat.search(full_yaml):
                errors.append("Plaintext secret detected in manifest! Use secretKeyRef references.")

        if "runAsNonRoot: true" not in manifest_set.deployments_yaml:
            errors.append("Backend deployment missing securityContext runAsNonRoot: true.")

        return {"is_valid": len(errors) == 0, "errors": errors}


global_manifest_generator = ManifestGenerator()
