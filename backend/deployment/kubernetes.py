import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.deployment.kubernetes")


class KubernetesGenerator:
    """
    KubernetesGenerator creates production-ready Kubernetes manifests:
    - deployment.yaml (Frontend & Backend Deployments)
    - service.yaml (ClusterIP / NodePort Services)
    - ingress.yaml (Ingress Routing)
    """

    def generate_deployment_yaml(self, app_name: str = "app") -> str:
        safe_name = app_name.lower().replace(" ", "-")
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {safe_name}-backend
  labels:
    app: {safe_name}-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {safe_name}-backend
  template:
    metadata:
      labels:
        app: {safe_name}-backend
    spec:
      containers:
      - name: backend
        image: {safe_name}-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {safe_name}-secrets
              key: database-url
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {safe_name}-frontend
  labels:
    app: {safe_name}-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {safe_name}-frontend
  template:
    metadata:
      labels:
        app: {safe_name}-frontend
    spec:
      containers:
      - name: frontend
        image: {safe_name}-frontend:latest
        ports:
        - containerPort: 80
"""

    def generate_service_yaml(self, app_name: str = "app") -> str:
        safe_name = app_name.lower().replace(" ", "-")
        return f"""apiVersion: v1
kind: Service
metadata:
  name: {safe_name}-backend-service
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
  selector:
    app: {safe_name}-backend
---
apiVersion: v1
kind: Service
metadata:
  name: {safe_name}-frontend-service
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
  selector:
    app: {safe_name}-frontend
"""

    def generate_ingress_yaml(self, app_name: str = "app") -> str:
        safe_name = app_name.lower().replace(" ", "-")
        return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {safe_name}-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: {safe_name}-backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {safe_name}-frontend-service
            port:
              number: 80
"""


# Global KubernetesGenerator Instance
global_kubernetes_generator = KubernetesGenerator()
