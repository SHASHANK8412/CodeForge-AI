"""
AIForge Day 33 — FinOps Cloud Pricing Engine
=============================================
Provides unit-cost lookup for AWS, Azure, GCP, and Local.
All prices are ESTIMATES and clearly labeled as such.
Never fabricates actual billing data.
"""
from __future__ import annotations

from backend.finops.models import ProviderEnum, CostSourceEnum


# ─────────────────────────────────────────────
# Static price catalogue (USD / month)
# Prices are approximations for representative
# instance sizes used in AIForge demo stacks.
# Source: published cloud pricing pages (2024).
# ─────────────────────────────────────────────

_AWS_PRICES: dict[str, float] = {
    # Compute
    "ec2.t3.micro":    8.50,
    "ec2.t3.small":   16.79,
    "ec2.t3.medium":  30.37,
    "ec2.t3.large":   60.74,
    "ec2.m5.xlarge": 140.16,
    "ec2.c5.2xlarge":245.28,
    # EKS node (m5.large)
    "eks.node.m5.large":  70.08,
    "eks.cluster":         73.00,  # control-plane
    # RDS PostgreSQL (db.t3.medium, Multi-AZ)
    "rds.postgres.t3.medium.singleaz": 31.00,
    "rds.postgres.t3.medium.multiaz":  62.00,
    "rds.postgres.t3.large.multiaz":  117.00,
    # Elasticache Redis (cache.t3.micro)
    "elasticache.redis.t3.micro":  12.00,
    "elasticache.redis.t3.small":  24.00,
    # Load Balancer
    "alb":  16.00,
    "nlb":  16.00,
    # Storage (per GB/month)
    "ebs.gp3.per_gb": 0.08,
    "s3.per_gb":       0.023,
    # Monitoring
    "cloudwatch.basic":   7.00,
    "cloudwatch.detailed": 15.00,
    # Data transfer (per GB)
    "egress.per_gb": 0.09,
}

_AZURE_PRICES: dict[str, float] = {
    "vm.b2s":          38.00,
    "vm.d2sv3":        96.36,
    "aks.node.d2sv3":  96.36,
    "aks.cluster":     73.00,
    "postgres.b2s":    25.00,
    "postgres.gp.d2s": 55.00,
    "redis.c0":        16.00,
    "lb":              18.00,
    "disk.p10_per_gb":  0.095,
    "monitor.basic":   10.00,
}

_GCP_PRICES: dict[str, float] = {
    "gce.e2.medium":   33.00,
    "gce.n1.standard2": 97.09,
    "gke.node.n1s2":   97.09,
    "gke.cluster":     73.00,
    "cloudsql.postgres.db-g1-small": 25.00,
    "cloudsql.postgres.db-n1s2":     60.00,
    "memorystore.redis.basic1g":     22.00,
    "lb.forwarding_rule":            18.00,
    "gcs.per_gb":                     0.020,
    "monitoring.basic":               8.00,
}

# Local / Docker Compose — no cloud cost
_LOCAL_PRICES: dict[str, float] = {}


_PROVIDER_CATALOGUE: dict[ProviderEnum, dict[str, float]] = {
    ProviderEnum.AWS:   _AWS_PRICES,
    ProviderEnum.AZURE: _AZURE_PRICES,
    ProviderEnum.GCP:   _GCP_PRICES,
    ProviderEnum.LOCAL: _LOCAL_PRICES,
}


class CloudPricingEngine:
    """Looks up estimated monthly costs for cloud resources."""

    PRICING_TIMESTAMP = "2024-Q4"

    def get_price(self, provider: ProviderEnum, resource_key: str) -> tuple[float, CostSourceEnum]:
        """Return (unit_cost, source) for a resource key.

        If the provider or key is unknown, returns (0.0, UNAVAILABLE).
        """
        catalogue = _PROVIDER_CATALOGUE.get(provider)
        if catalogue is None:
            return 0.0, CostSourceEnum.UNAVAILABLE
        if provider == ProviderEnum.LOCAL:
            return 0.0, CostSourceEnum.ESTIMATED
        price = catalogue.get(resource_key)
        if price is None:
            return 0.0, CostSourceEnum.UNAVAILABLE
        return price, CostSourceEnum.ESTIMATED

    def list_keys(self, provider: ProviderEnum) -> list[str]:
        return list(_PROVIDER_CATALOGUE.get(provider, {}).keys())

    def get_demo_stack_estimate(self, provider: ProviderEnum) -> dict[str, float]:
        """Return estimated monthly cost breakdown for a standard
        AIForge demo stack (FastAPI + PostgreSQL + Redis + K8s + Monitoring).
        """
        if provider == ProviderEnum.AWS:
            return {
                "compute":    _AWS_PRICES["ec2.t3.medium"] * 3,   # 3 nodes → $91.11
                "kubernetes": _AWS_PRICES["eks.cluster"],           # $73
                "database":   _AWS_PRICES["rds.postgres.t3.medium.singleaz"],  # $31
                "redis":      _AWS_PRICES["elasticache.redis.t3.micro"],        # $12
                "networking": _AWS_PRICES["alb"],                   # $16
                "monitoring": _AWS_PRICES["cloudwatch.basic"],      # $7
                "storage":    _AWS_PRICES["ebs.gp3.per_gb"] * 50,  # $4
            }
        elif provider == ProviderEnum.AZURE:
            return {
                "compute":    _AZURE_PRICES["vm.d2sv3"] * 2,
                "kubernetes": _AZURE_PRICES["aks.cluster"],
                "database":   _AZURE_PRICES["postgres.b2s"],
                "redis":      _AZURE_PRICES["redis.c0"],
                "networking": _AZURE_PRICES["lb"],
                "monitoring": _AZURE_PRICES["monitor.basic"],
                "storage":    _AZURE_PRICES["disk.p10_per_gb"] * 50,
            }
        elif provider == ProviderEnum.GCP:
            return {
                "compute":    _GCP_PRICES["gce.n1.standard2"] * 2,
                "kubernetes": _GCP_PRICES["gke.cluster"],
                "database":   _GCP_PRICES["cloudsql.postgres.db-g1-small"],
                "redis":      _GCP_PRICES["memorystore.redis.basic1g"],
                "networking": _GCP_PRICES["lb.forwarding_rule"],
                "monitoring": _GCP_PRICES["monitoring.basic"],
                "storage":    _GCP_PRICES["gcs.per_gb"] * 50,
            }
        else:
            return {"compute": 0.0, "database": 0.0, "redis": 0.0,
                    "networking": 0.0, "monitoring": 0.0, "storage": 0.0}
