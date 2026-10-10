"""
AIForge Day 33 — Cost Estimator
================================
Estimates infrastructure cost from Terraform config / K8s spec / provider
pricing.  All estimates are explicitly labeled ESTIMATED; actual billing
data is never fabricated.
"""
from __future__ import annotations

from backend.finops.models import (
    CostBreakdown,
    CostSourceEnum,
    InfrastructureCost,
    ProviderEnum,
)
from backend.finops.pricing import CloudPricingEngine

_pricing = CloudPricingEngine()


class CostEstimator:
    """Derives monthly cost estimates from infrastructure descriptions."""

    # -----------------------------------------------------------
    # Primary public method
    # -----------------------------------------------------------

    def estimate_from_config(
        self,
        project_id: str,
        provider: ProviderEnum = ProviderEnum.AWS,
        environment: str = "production",
        terraform_resources: dict | None = None,
        kubernetes_resources: dict | None = None,
    ) -> CostBreakdown:
        """Estimate monthly cost from Terraform/K8s config.

        If no specific resource lists are provided, falls back to the
        standard demo-stack estimate for the chosen provider.
        """
        breakdown_map = _pricing.get_demo_stack_estimate(provider)

        # Allow overrides from Terraform resource counts
        if terraform_resources:
            breakdown_map = self._override_from_terraform(
                breakdown_map, provider, terraform_resources
            )

        line_items = self._build_line_items(
            project_id, provider, environment, breakdown_map
        )
        total = sum(i.estimated_monthly_cost for i in line_items)

        return CostBreakdown(
            project_id=project_id,
            provider=provider,
            environment=environment,
            compute=breakdown_map.get("compute", 0.0),
            database=breakdown_map.get("database", 0.0),
            redis=breakdown_map.get("redis", 0.0),
            networking=breakdown_map.get("networking", 0.0),
            storage=breakdown_map.get("storage", 0.0),
            monitoring=breakdown_map.get("monitoring", 0.0),
            kubernetes=breakdown_map.get("kubernetes", 0.0),
            total_monthly_estimate=round(total, 2),
            source=CostSourceEnum.ESTIMATED,
            line_items=line_items,
        )

    # -----------------------------------------------------------
    # Kubernetes cost analysis
    # -----------------------------------------------------------

    def estimate_kubernetes_cost(
        self,
        project_id: str,
        provider: ProviderEnum = ProviderEnum.AWS,
        node_count: int = 3,
    ) -> dict:
        """Estimate Kubernetes node + control-plane costs."""
        if provider == ProviderEnum.AWS:
            node_price, _ = _pricing.get_price(provider, "eks.node.m5.large")
            cp_price, _ = _pricing.get_price(provider, "eks.cluster")
        elif provider == ProviderEnum.AZURE:
            node_price, _ = _pricing.get_price(provider, "aks.node.d2sv3")
            cp_price, _ = _pricing.get_price(provider, "aks.cluster")
        elif provider == ProviderEnum.GCP:
            node_price, _ = _pricing.get_price(provider, "gke.node.n1s2")
            cp_price, _ = _pricing.get_price(provider, "gke.cluster")
        else:
            node_price, cp_price = 0.0, 0.0

        nodes_cost = round(node_price * node_count, 2)
        total = round(nodes_cost + cp_price, 2)
        return {
            "source": CostSourceEnum.ESTIMATED,
            "provider": provider,
            "node_count": node_count,
            "node_monthly_cost": node_price,
            "nodes_total": nodes_cost,
            "control_plane": cp_price,
            "total_kubernetes_monthly": total,
            "pricing_timestamp": _pricing.PRICING_TIMESTAMP,
        }

    # -----------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------

    def _override_from_terraform(
        self,
        base: dict,
        provider: ProviderEnum,
        tf_resources: dict,
    ) -> dict:
        """Apply terraform resource count overrides to base estimate."""
        result = dict(base)
        ec2_count = tf_resources.get("ec2_instances", 0)
        if ec2_count:
            price, _ = _pricing.get_price(provider, "ec2.t3.medium")
            result["compute"] = round(price * ec2_count, 2)
        rds_count = tf_resources.get("rds_instances", 0)
        if rds_count:
            price, _ = _pricing.get_price(provider, "rds.postgres.t3.medium.singleaz")
            result["database"] = round(price * rds_count, 2)
        redis_count = tf_resources.get("redis_instances", 0)
        if redis_count:
            price, _ = _pricing.get_price(provider, "elasticache.redis.t3.micro")
            result["redis"] = round(price * redis_count, 2)
        lb_count = tf_resources.get("load_balancers", 0)
        if lb_count:
            price, _ = _pricing.get_price(provider, "alb")
            result["networking"] = round(price * lb_count, 2)
        return result

    def _build_line_items(
        self,
        project_id: str,
        provider: ProviderEnum,
        environment: str,
        breakdown: dict,
    ) -> list[InfrastructureCost]:
        labels = {
            "compute": "Application Compute",
            "kubernetes": "Kubernetes Control Plane + Nodes",
            "database": "PostgreSQL Database",
            "redis": "Redis Cache",
            "networking": "Load Balancer / Networking",
            "monitoring": "Monitoring & Observability",
            "storage": "Block & Object Storage",
        }
        items = []
        for key, amount in breakdown.items():
            if amount <= 0:
                continue
            items.append(
                InfrastructureCost(
                    id=f"{project_id}_{key}",
                    project_id=project_id,
                    provider=provider,
                    environment=environment,
                    resource_type=key.upper(),
                    resource_name=labels.get(key, key),
                    estimated_monthly_cost=round(amount, 2),
                    source=CostSourceEnum.ESTIMATED,
                    assumptions=f"Estimated using {provider} pricing ({_pricing.PRICING_TIMESTAMP}). Not actual billing data.",
                    pricing_timestamp=_pricing.PRICING_TIMESTAMP,
                )
            )
        return items
