"""
AIForge Day 31 — Kubernetes Data Models
=======================================
Pydantic models for K8s Clusters, Pod Statuses, Manifest Sets, Resource Limits, Health Probes, HPA Scaling, and Event Logs.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PodPhaseEnum(str, Enum):
    RUNNING = "Running"
    PENDING = "Pending"
    CRASH_LOOP_BACK_OFF = "CrashLoopBackOff"
    OOM_KILLED = "OOMKilled"
    FAILED = "Failed"


class K8sResourceLimits(BaseModel):
    cpu_request: str = "250m"
    cpu_limit: str = "500m"
    memory_request: str = "256Mi"
    memory_limit: str = "512Mi"


class K8sHealthProbe(BaseModel):
    path: str = "/health"
    port: int = 8000
    initial_delay_seconds: int = 10
    period_seconds: int = 5
    failure_threshold: int = 3


class K8sPodStatus(BaseModel):
    name: str
    component: str  # frontend, backend, redis, postgresql
    status: PodPhaseEnum = PodPhaseEnum.RUNNING
    ready: bool = True
    restarts: int = 0
    cpu_percent: float = 24.5
    memory_mb: float = 284.0
    version: str = "v1.5"
    image: str = "aiforge/backend:v1.5"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class K8sClusterStatus(BaseModel):
    """What is known about the cluster. Nothing is filled in that was not read from a real cluster."""
    connected: bool = False
    cluster_name: Optional[str] = None
    namespace: str = ""
    project_id: str = ""
    nodes_count: Optional[int] = None
    k8s_version: Optional[str] = None
    frontend_pods: List[K8sPodStatus] = Field(default_factory=list)
    backend_pods: List[K8sPodStatus] = Field(default_factory=list)
    redis_pods: List[K8sPodStatus] = Field(default_factory=list)
    other_pods: List[K8sPodStatus] = Field(default_factory=list)
    cpu_usage_pct: Optional[float] = None       # not measured
    memory_usage_pct: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    error_rate_pct: Optional[float] = None
    mode: str = "not_connected"                 # not_connected | read_only (a real cluster; only reads are implemented)
    note: str = ""


class K8sManifestSet(BaseModel):
    project_id: str
    namespace: str
    deployments_yaml: str
    services_yaml: str
    ingress_yaml: str
    configmaps_yaml: str
    secrets_yaml: str
    hpa_yaml: str
    network_policies_yaml: str
    is_valid: bool = True
    validation_errors: List[str] = Field(default_factory=list)


class K8sScaleRequest(BaseModel):
    project_id: str = "aiforge-demo"
    component: str = "backend"
    current_replicas: int = 3
    desired_replicas: int = 5
    reason: str = "Observed high CPU utilization (91%) and elevated P95 latency (680ms)"


class K8sDeploymentEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    component: str = "backend"
    event_type: str = "ScalingOccurred"
    message: str = "Scaled backend replicas from 3 to 5"
    severity: str = "INFO"  # INFO, WARNING, ERROR


class K8sRollbackResult(BaseModel):
    success: bool = False
    project_id: str = ""
    previous_version: Optional[str] = None
    target_version: Optional[str] = None
    message: str = ""
    status: str = "NOT_EXECUTED"
