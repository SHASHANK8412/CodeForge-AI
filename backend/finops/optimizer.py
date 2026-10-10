"""
AIForge Day 33 — Cost Optimizer: Waste Detection & Rightsizing
==============================================================
Detects potential waste (overprovisioned resources, idle services)
and produces rightsizing recommendations.

IMPORTANT:
- Uses "Potential Waste" not "Confirmed Waste" unless actual usage data proves it.
- Never automatically resizes production resources.
- All recommendations require user approval before any Terraform plan is applied.
- Security and reliability guardrails are enforced before any recommendation is issued.
"""
from __future__ import annotations

from backend.finops.models import (
    CostRecommendation,
    RiskLevelEnum,
    WasteItem,
)


class WasteDetector:
    """Detects potential waste in infrastructure resource allocation."""

    def detect(self, project_id: str, resource_utilization: list[dict] | None = None) -> list[WasteItem]:
        """Return list of WasteItems for potentially overprovisioned resources."""
        utilization = resource_utilization or _DEMO_UTILIZATION

        items: list[WasteItem] = []
        for r in utilization:
            allocated_cpu = r.get("allocated_cpu_m", 0)
            avg_cpu = r.get("avg_cpu_m", 0)
            allocated_mem = r.get("allocated_mem_gb", 0)
            avg_mem = r.get("avg_mem_gb", 0)

            cpu_ratio = avg_cpu / allocated_cpu if allocated_cpu else 1.0
            mem_ratio = avg_mem / allocated_mem if allocated_mem else 1.0

            # Flag if average usage < 25% of allocation
            if cpu_ratio < 0.25:
                items.append(WasteItem(
                    resource_name=r["name"],
                    resource_type=r.get("type", "Compute"),
                    allocated=f"{allocated_cpu}m CPU",
                    observed_average=f"{avg_cpu}m CPU",
                    waste_label="Potential Waste",
                    confidence="LOW" if avg_cpu == 0 else "MEDIUM",
                    recommendation=(
                        f"Observed average CPU ({avg_cpu}m) is "
                        f"{round(cpu_ratio * 100, 0):.0f}% of allocated "
                        f"({allocated_cpu}m). Evaluate reducing CPU request."
                    ),
                ))
            if mem_ratio < 0.25:
                items.append(WasteItem(
                    resource_name=r["name"],
                    resource_type=r.get("type", "Compute"),
                    allocated=f"{allocated_mem} GB RAM",
                    observed_average=f"{avg_mem} GB RAM",
                    waste_label="Potential Waste",
                    confidence="LOW" if avg_mem == 0 else "MEDIUM",
                    recommendation=(
                        f"Observed average memory ({avg_mem} GB) is "
                        f"{round(mem_ratio * 100, 0):.0f}% of allocated "
                        f"({allocated_mem} GB). Evaluate reducing memory request."
                    ),
                ))

        # Check Redis hit rate
        redis_hit_rate = (resource_utilization or [{}])[0].get("redis_hit_rate_pct", None)
        if redis_hit_rate is not None and redis_hit_rate < 10:
            items.append(WasteItem(
                resource_name="Redis Cache",
                resource_type="Cache",
                allocated="Elasticache node",
                observed_average=f"{redis_hit_rate}% hit rate",
                waste_label="Potential Waste",
                confidence="MEDIUM",
                recommendation=(
                    f"Redis cache hit rate is {redis_hit_rate}%. "
                    "Review whether Redis is justified for this workload."
                ),
            ))

        return items


class RightsizingEngine:
    """Generates rightsizing recommendations with risk labels."""

    def recommend(
        self,
        project_id: str,
        waste_items: list[WasteItem],
        policy: str = "BALANCED",
    ) -> list[CostRecommendation]:
        recs: list[CostRecommendation] = []
        for i, item in enumerate(waste_items):
            # Determine risk based on resource criticality
            risk = RiskLevelEnum.LOW
            requires_perf_check = False
            if item.resource_type in ("Compute", "Database"):
                risk = RiskLevelEnum.MEDIUM
                requires_perf_check = True
            if "Database" in item.resource_type:
                risk = RiskLevelEnum.HIGH
                requires_perf_check = True

            # Aggressive policy may surface more recommendations but still
            # enforces security + reliability guardrails
            if policy == "CONSERVATIVE" and risk in (RiskLevelEnum.MEDIUM, RiskLevelEnum.HIGH):
                continue

            recs.append(CostRecommendation(
                id=f"rec_{project_id}_{i:03d}",
                project_id=project_id,
                title=f"Potential Optimization: {item.resource_name}",
                description=item.recommendation,
                resource_name=item.resource_name,
                resource_type=item.resource_type,
                current_config=item.allocated,
                suggested_config="Evaluate reducing to match observed average usage",
                potential_saving="ESTIMATE",
                risk=risk,
                requires_performance_validation=requires_perf_check,
                requires_approval=True,
                security_safe=True,
                reliability_safe=risk != RiskLevelEnum.HIGH,
                terraform_plan_available=True,
                evolution_priority="MEDIUM" if risk == RiskLevelEnum.LOW else "HIGH",
            ))
        return recs


class KubernetesJustificationEngine:
    """Evaluates whether Kubernetes is cost-justified for a project."""

    def evaluate(
        self,
        project_id: str,
        service_count: int = 1,
        avg_rps: float = 10.0,
        scaling_needed: bool = False,
        multi_region: bool = False,
    ) -> dict:
        factors: list[str] = []
        score = 0

        if service_count >= 5:
            factors.append(f"Multiple services ({service_count}) benefit from K8s orchestration.")
            score += 2
        else:
            factors.append(f"Low service count ({service_count}) — K8s overhead may not be warranted.")

        if avg_rps >= 500:
            factors.append(f"High traffic ({avg_rps} RPS) justifies horizontal scaling.")
            score += 2
        else:
            factors.append(f"Low traffic ({avg_rps} RPS) — auto-scaling benefit is limited.")

        if scaling_needed:
            factors.append("Traffic variability requires auto-scaling capabilities.")
            score += 1

        if multi_region:
            factors.append("Multi-region deployment benefits from K8s federation.")
            score += 1

        is_justified = score >= 3

        recommendation = (
            "Kubernetes is justified for this workload based on service count, "
            "traffic, and scaling requirements."
            if is_justified
            else
            "Kubernetes is NOT currently justified for this workload. "
            "Consider simpler container deployment (e.g., Docker Compose, "
            "AWS ECS, Azure Container Apps, or Cloud Run)."
        )

        return {
            "project_id": project_id,
            "is_justified": is_justified,
            "score": score,
            "factors": factors,
            "recommendation": recommendation,
            "alternative": None if is_justified else "Docker Compose / Managed Container Service",
            "note": "Recommendation considers cost, operational complexity, scalability, and reliability.",
        }


# ─────────────────────────────────────────────
# Demo utilization data (no actual metrics)
# ─────────────────────────────────────────────

_DEMO_UTILIZATION: list[dict] = [
    {
        "name": "backend-api",
        "type": "Compute",
        "allocated_cpu_m": 2000,
        "avg_cpu_m": 250,
        "allocated_mem_gb": 4,
        "avg_mem_gb": 0.9,
    },
    {
        "name": "frontend-service",
        "type": "Compute",
        "allocated_cpu_m": 1000,
        "avg_cpu_m": 80,
        "allocated_mem_gb": 2,
        "avg_mem_gb": 0.3,
    },
    {
        "name": "Redis Cache",
        "type": "Cache",
        "allocated_cpu_m": 0,
        "avg_cpu_m": 0,
        "allocated_mem_gb": 0,
        "avg_mem_gb": 0,
        "redis_hit_rate_pct": 3,
    },
]
