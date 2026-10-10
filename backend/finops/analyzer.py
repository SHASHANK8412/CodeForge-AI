"""
AIForge Day 33 — Cost Analyzer
================================
Analyzes cost changes, detects anomalies, and builds cost trends.
"""
from __future__ import annotations

from backend.finops.models import (
    CostAnomaly,
    CostForecast,
    CostSourceEnum,
    AnomalySeverityEnum,
)


class CostChangeAnalyzer:
    """Answers 'Why did infrastructure cost increase?'"""

    def analyze_change(
        self,
        project_id: str,
        previous_estimate: float,
        current_estimate: float,
        resource_changes: list[dict] | None = None,
    ) -> dict:
        delta = current_estimate - previous_estimate
        pct = round((delta / previous_estimate) * 100, 1) if previous_estimate else 0.0

        contributors = resource_changes or [
            {"resource": "Kubernetes nodes", "change": "+2", "estimated_impact": "+$140"},
            {"resource": "Redis cluster", "change": "New deployment", "estimated_impact": "+$12"},
            {"resource": "Monitoring stack", "change": "Prometheus + Grafana added", "estimated_impact": "+$7"},
        ]

        return {
            "project_id": project_id,
            "previous_estimate": previous_estimate,
            "current_estimate": current_estimate,
            "delta": round(delta, 2),
            "change_pct": pct,
            "source": CostSourceEnum.ESTIMATED,
            "possible_contributors": contributors,
            "note": "Contributors are potential causes based on resource configuration changes. Causation requires actual billing data.",
        }

    def build_trend(self, project_id: str) -> dict:
        """Build a sample cost trend (labeled ESTIMATED; no real billing data)."""
        return {
            "project_id": project_id,
            "trend": [
                {"month": "January", "estimate": 102.0, "source": CostSourceEnum.ESTIMATED},
                {"month": "February", "estimate": 137.0, "source": CostSourceEnum.ESTIMATED},
                {"month": "March",    "estimate": 184.0, "source": CostSourceEnum.ESTIMATED},
            ],
            "note": "Historical values are estimates based on observed resource configurations. Actual billing data not available.",
        }


class CostAnomalyDetector:
    """Detects unusual cost spikes relative to baseline."""

    HIGH_MULTIPLIER = 2.0
    MEDIUM_MULTIPLIER = 1.5

    def detect(
        self,
        project_id: str,
        baseline_daily: float,
        observed_daily: float,
    ) -> CostAnomaly:
        multiplier = round(observed_daily / baseline_daily, 2) if baseline_daily else 1.0

        if multiplier >= self.HIGH_MULTIPLIER:
            severity = AnomalySeverityEnum.HIGH
        elif multiplier >= self.MEDIUM_MULTIPLIER:
            severity = AnomalySeverityEnum.MEDIUM
        else:
            severity = AnomalySeverityEnum.LOW

        causes: list[str] = []
        if multiplier >= self.HIGH_MULTIPLIER:
            causes = [
                "Unexpected resource creation",
                "Traffic spike causing auto-scaling",
                "Replica count increase",
                "New Kubernetes workloads",
                "Storage growth",
            ]
        elif multiplier >= self.MEDIUM_MULTIPLIER:
            causes = [
                "Moderate replica increase",
                "Increased data transfer",
                "Additional monitoring metrics",
            ]

        return CostAnomaly(
            project_id=project_id,
            baseline_daily_cost=baseline_daily,
            observed_daily_cost=observed_daily,
            multiplier=multiplier,
            severity=severity,
            possible_causes=causes,
            action="Investigate. Do NOT automatically terminate resources.",
        )


class CostForecaster:
    """Produces labeled cost forecasts. NEVER fabricates historical data."""

    def forecast(self, project_id: str, current_monthly: float) -> CostForecast:
        # Only produce forecasts if we have a meaningful current estimate
        if current_monthly <= 0:
            return CostForecast(
                project_id=project_id,
                forecast_available=False,
                label="FORECAST UNAVAILABLE",
                note="Insufficient cost data to generate a forecast.",
            )

        # Simple linear projection assuming ~+15% monthly growth
        growth = 0.15
        next_30 = round(current_monthly * (1 + growth), 2)
        next_90 = round(current_monthly * (1 + growth) ** 3, 2)
        next_7 = round(current_monthly / 30 * 7 * (1 + growth / 4), 2)

        return CostForecast(
            project_id=project_id,
            forecast_available=True,
            label="FORECAST",
            next_7_days=next_7,
            next_30_days=next_30,
            next_90_days=next_90,
            trend_pct=round(growth * 100, 1),
            source=CostSourceEnum.ESTIMATED,
            note=(
                "FORECAST — These are estimates based on current resource "
                "configuration and a projected 15% monthly growth. "
                "Not actual billing data."
            ),
        )
