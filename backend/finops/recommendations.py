"""
AIForge Day 33 — Architecture Cost Comparison & Recommendations
===============================================================
Compares architectural options (Docker, K8s, Serverless) on cost,
performance, reliability, security, and operational complexity.
Does NOT recommend based on cost alone.
"""
from __future__ import annotations

from backend.finops.models import (
    ArchitectureCostComparison,
    ArchitectureOption,
    CostSourceEnum,
)


# ─────────────────────────────────────────────
# Preset architecture templates
# ─────────────────────────────────────────────

_ARCHITECTURES: list[dict] = [
    {
        "name": "Architecture A — Docker + Managed PostgreSQL",
        "description": "Docker Compose with managed PostgreSQL (no K8s). Simple, low operational overhead.",
        "cost_label": "LOW",
        "complexity_label": "LOW",
        "scalability_label": "MEDIUM",
        "reliability_label": "MEDIUM",
        "security_label": "HIGH",
        "estimated_monthly_cost": 60.0,
    },
    {
        "name": "Architecture B — Kubernetes + PostgreSQL + Redis",
        "description": "Full Kubernetes orchestration with managed PostgreSQL and Redis cache.",
        "cost_label": "HIGH",
        "complexity_label": "HIGH",
        "scalability_label": "HIGH",
        "reliability_label": "HIGH",
        "security_label": "HIGH",
        "estimated_monthly_cost": 234.0,
    },
    {
        "name": "Architecture C — Serverless + Managed PostgreSQL",
        "description": "Serverless backend (Lambda/Cloud Run) with managed PostgreSQL. Pay-per-use.",
        "cost_label": "MEDIUM",
        "complexity_label": "MEDIUM",
        "scalability_label": "HIGH",
        "reliability_label": "HIGH",
        "security_label": "HIGH",
        "estimated_monthly_cost": 45.0,
    },
]


class ArchitectureComparator:
    """Compares architectural options on multiple dimensions."""

    def compare(self, project_id: str, question: str = "Which architecture should I choose?") -> ArchitectureCostComparison:
        options = [
            ArchitectureOption(
                **a,
                source=CostSourceEnum.ESTIMATED,
            )
            for a in _ARCHITECTURES
        ]
        return ArchitectureCostComparison(
            project_id=project_id,
            question=question,
            options=options,
            recommended="Architecture A — Docker + Managed PostgreSQL",
            reasoning=(
                "For a typical AIForge project with moderate traffic and a small "
                "service footprint, Architecture A offers the best engineering "
                "trade-off: lower cost, lower operational complexity, and adequate "
                "reliability. Kubernetes (Architecture B) is justified only when "
                "scaling requirements, multi-service orchestration, or traffic "
                "variability specifically require it."
            ),
            note=(
                "Recommendation is based on cost, operational complexity, "
                "scalability, reliability, and security — not cost alone. "
                "Architecture A costs are ESTIMATED."
            ),
        )

    def cost_performance_tradeoff(self, project_id: str) -> dict:
        """Show cost/performance efficiency score for architectural options."""
        return {
            "project_id": project_id,
            "source": CostSourceEnum.ESTIMATED,
            "options": [
                {
                    "name": "Option A — Small EC2 cluster",
                    "estimated_monthly_cost": 100.0,
                    "p95_latency_ms": 400,
                    "cost_efficiency_score": 72,
                    "note": "Lower cost, acceptable latency for most workloads.",
                },
                {
                    "name": "Option B — K8s with auto-scaling",
                    "estimated_monthly_cost": 160.0,
                    "p95_latency_ms": 180,
                    "cost_efficiency_score": 85,
                    "note": "Higher cost but measured better performance. Justified if P95 < 200ms is a requirement.",
                },
            ],
            "analysis": (
                "Option B costs 60% more but provides 55% lower P95 latency. "
                "AIForge does not declare one universally better. The right choice "
                "depends on your latency SLA and traffic profile."
            ),
        }

    def simulate_cost_change(self, project_id: str, scenario: str, current_monthly: float) -> dict:
        """Simulate 'what-if' cost scenarios. Always labeled SIMULATED."""
        scenarios = {
            "double_traffic": {
                "label": "Traffic doubles",
                "multiplier": 1.8,
                "note": "Assumes proportional replica and node scaling.",
            },
            "add_redis": {
                "label": "Add Redis cache",
                "addition": 12.0,
                "multiplier": 1.0,
                "note": "Redis Elasticache t3.micro estimate.",
            },
            "add_kubernetes": {
                "label": "Migrate to Kubernetes",
                "addition": 143.0,
                "multiplier": 1.0,
                "note": "EKS control plane + 2 m5.large nodes.",
            },
            "reduce_replicas": {
                "label": "Reduce replicas by 2",
                "multiplier": 0.75,
                "note": "Assumes t3.medium compute nodes.",
            },
        }
        cfg = scenarios.get(scenario, {"label": scenario, "multiplier": 1.0, "note": ""})
        simulated = round(
            current_monthly * cfg.get("multiplier", 1.0) + cfg.get("addition", 0.0),
            2,
        )
        return {
            "project_id": project_id,
            "scenario": cfg["label"],
            "current_estimate": current_monthly,
            "simulated_estimate": simulated,
            "delta": round(simulated - current_monthly, 2),
            "label": "SIMULATED",
            "note": cfg.get("note", ""),
            "source": CostSourceEnum.ESTIMATED,
        }
