"""
AIForge Day 33 — FinOps Service
=================================
Central orchestrator for all FinOps operations.
Integrates with: Flight Recorder, Engineering Memory, Evolution Engine,
                 Architecture Simulator, Terraform, GitHub, Copilot.
"""
from __future__ import annotations

import logging
from datetime import datetime

from backend.finops.analyzer import CostAnomalyDetector, CostChangeAnalyzer, CostForecaster
from backend.finops.budget import BudgetManager
from backend.finops.estimator import CostEstimator
from backend.finops.models import (
    ArchitectureCostComparison,
    CostAnomaly,
    CostBreakdown,
    CostForecast,
    CostRecommendation,
    CostSourceEnum,
    KubernetesJustification,
    ProjectBudget,
    ProviderEnum,
    WasteItem,
)
from backend.finops.optimizer import KubernetesJustificationEngine, RightsizingEngine, WasteDetector
from backend.finops.recommendations import ArchitectureComparator

logger = logging.getLogger("aiforge.finops")

# ─────────────────────────────────────────────
# Flight Recorder integration (optional import)
# ─────────────────────────────────────────────
try:
    from backend.flight_recorder.recorder import flight_recorder
    _has_recorder = True
except Exception:
    _has_recorder = False


def _record(event: str, data: dict) -> None:
    if _has_recorder:
        try:
            flight_recorder.record(event, data)
        except Exception:
            pass
    logger.info("[FinOps] %s — %s", event, data)


# ─────────────────────────────────────────────
# Engineering Memory integration (optional)
# ─────────────────────────────────────────────
try:
    from backend.memory.engineering_memory import EngineeringMemory
    _memory = EngineeringMemory()
    _has_memory = True
except Exception:
    _has_memory = False


def _store_lesson(project_id: str, lesson: str) -> None:
    if _has_memory:
        try:
            _memory.store(
                project_id=project_id,
                category="FINOPS_LESSON",
                content=lesson,
                timestamp=datetime.utcnow().isoformat(),
            )
        except Exception:
            pass
    logger.info("[FinOps Memory] %s: %s", project_id, lesson)


class FinOpsService:
    """Central AI FinOps service answering cost intelligence questions."""

    def __init__(self) -> None:
        self._estimator = CostEstimator()
        self._waste = WasteDetector()
        self._rightsizing = RightsizingEngine()
        self._k8s_engine = KubernetesJustificationEngine()
        self._comparator = ArchitectureComparator()
        self._change_analyzer = CostChangeAnalyzer()
        self._anomaly = CostAnomalyDetector()
        self._forecaster = CostForecaster()
        self._budget_mgr = BudgetManager()

    # ──────────────────────────────────────────
    # Core estimation
    # ──────────────────────────────────────────

    def analyze_cost(self, project_id: str, provider: str = "AWS", environment: str = "production") -> CostBreakdown:
        _record("cost_analysis_started", {"project_id": project_id})
        prov = ProviderEnum(provider) if provider in ProviderEnum.__members__ else ProviderEnum.AWS
        result = self._estimator.estimate_from_config(project_id, prov, environment)
        _record("cost_analysis_completed", {"project_id": project_id, "total": result.total_monthly_estimate})
        return result

    def estimate_cost(self, project_id: str, provider: str = "AWS", tf_resources: dict | None = None) -> CostBreakdown:
        _record("cost_estimate_created", {"project_id": project_id, "provider": provider})
        prov = ProviderEnum(provider) if provider in ProviderEnum.__members__ else ProviderEnum.AWS
        return self._estimator.estimate_from_config(project_id, prov, terraform_resources=tf_resources)

    # ──────────────────────────────────────────
    # Waste & rightsizing
    # ──────────────────────────────────────────

    def detect_waste(self, project_id: str, utilization: list[dict] | None = None) -> list[WasteItem]:
        return self._waste.detect(project_id, utilization)

    def generate_recommendations(
        self,
        project_id: str,
        utilization: list[dict] | None = None,
        policy: str = "BALANCED",
    ) -> list[CostRecommendation]:
        waste = self._waste.detect(project_id, utilization)
        recs = self._rightsizing.recommend(project_id, waste, policy)
        if recs:
            _store_lesson(
                project_id,
                f"FinOps detected {len(recs)} potential waste items under {policy} policy.",
            )
        return recs

    # ──────────────────────────────────────────
    # Architecture comparison
    # ──────────────────────────────────────────

    def compare_architectures(self, project_id: str, question: str = "") -> ArchitectureCostComparison:
        return self._comparator.compare(project_id, question or "Which architecture should I choose?")

    def cost_performance_tradeoff(self, project_id: str) -> dict:
        return self._comparator.cost_performance_tradeoff(project_id)

    def simulate_cost_change(self, project_id: str, scenario: str, current_monthly: float) -> dict:
        return self._comparator.simulate_cost_change(project_id, scenario, current_monthly)

    # ──────────────────────────────────────────
    # Kubernetes justification
    # ──────────────────────────────────────────

    def evaluate_kubernetes(
        self,
        project_id: str,
        service_count: int = 1,
        avg_rps: float = 10.0,
        scaling_needed: bool = False,
        multi_region: bool = False,
    ) -> dict:
        return self._k8s_engine.evaluate(
            project_id, service_count, avg_rps, scaling_needed, multi_region
        )

    # ──────────────────────────────────────────
    # Cost change analysis
    # ──────────────────────────────────────────

    def analyze_cost_change(
        self,
        project_id: str,
        previous: float,
        current: float,
        resource_changes: list[dict] | None = None,
    ) -> dict:
        return self._change_analyzer.analyze_change(project_id, previous, current, resource_changes)

    def build_trend(self, project_id: str) -> dict:
        return self._change_analyzer.build_trend(project_id)

    # ──────────────────────────────────────────
    # Budget
    # ──────────────────────────────────────────

    def calculate_budget(
        self,
        project_id: str,
        environment: str = "production",
        monthly_limit: float = 250.0,
        current_estimate: float = 0.0,
    ) -> ProjectBudget:
        budget = self._budget_mgr.create(project_id, environment, monthly_limit, current_estimate=current_estimate)
        if budget.status.value in ("WARNING", "CRITICAL"):
            _record(
                "budget_warning" if budget.status.value == "WARNING" else "budget_exceeded",
                {"project_id": project_id, "percent_used": budget.percent_used},
            )
        return budget

    # ──────────────────────────────────────────
    # Anomaly detection
    # ──────────────────────────────────────────

    def detect_anomaly(self, project_id: str, baseline: float, observed: float) -> CostAnomaly:
        anomaly = self._anomaly.detect(project_id, baseline, observed)
        if anomaly.multiplier >= 1.5:
            _record("cost_anomaly_detected", {
                "project_id": project_id,
                "baseline": baseline,
                "observed": observed,
                "severity": anomaly.severity,
            })
        return anomaly

    # ──────────────────────────────────────────
    # Forecasting
    # ──────────────────────────────────────────

    def forecast_cost(self, project_id: str, current_monthly: float) -> CostForecast:
        return self._forecaster.forecast(project_id, current_monthly)

    # ──────────────────────────────────────────
    # Copilot queries
    # ──────────────────────────────────────────

    def answer_copilot(self, project_id: str, question: str) -> dict:
        """Answer natural language cost questions from Codebase Copilot."""
        q = question.lower()

        # Forecast check first (before generic "cost" to avoid misrouting)
        if any(w in q for w in ("forecast", "next month", "predict", "next 30", "next 90")):
            bd = self.analyze_cost(project_id)
            forecast = self.forecast_cost(project_id, bd.total_monthly_estimate)
            return {"answer": _format_forecast_answer(forecast), "forecast": forecast.model_dump()}

        if any(w in q for w in ("increase", "why", "change", "went up", "higher")):
            analysis = self.analyze_cost_change(project_id, 137.0, 184.0)
            return {"answer": _format_change_answer(analysis), "analysis": analysis}

        if any(w in q for w in ("cheaper", "reduce", "optimize", "save", "less")):
            recs = self.generate_recommendations(project_id)
            return {
                "answer": (
                    f"AIForge identified {len(recs)} potential optimization "
                    "opportunities. All require manual review and approval "
                    "before any Terraform changes are applied."
                ),
                "recommendations": [r.model_dump() for r in recs],
            }

        if any(w in q for w in ("kubernetes", "k8s", "need k8s", "worth")):
            return self.evaluate_kubernetes(project_id)

        if any(w in q for w in ("architecture", "option", "compare", "serverless", "docker")):
            comparison = self.compare_architectures(project_id, question)
            return {
                "answer": comparison.reasoning,
                "comparison": comparison.model_dump(),
            }

        if any(w in q for w in ("cost", "much", "expensive", "price", "spend")):
            bd = self.analyze_cost(project_id)
            return {
                "answer": (
                    f"The estimated monthly infrastructure cost for project "
                    f"'{project_id}' is ${bd.total_monthly_estimate:.2f} "
                    f"({bd.source}). This includes compute, database, Redis, "
                    "networking, and monitoring. All figures are ESTIMATED — "
                    "no actual billing data is available."
                ),
                "breakdown": bd.model_dump(),
            }

        return {
            "answer": (
                "I can help with infrastructure cost questions such as: "
                "'What does this architecture cost?', 'Why did cost increase?', "
                "'Can we reduce cost?', 'Do we need Kubernetes?', "
                "'What is the forecast for next month?', or "
                "'Which architecture is cheaper?'"
            )
        }





# ─────────────────────────────────────────────
# Formatting helpers
# ─────────────────────────────────────────────

def _format_change_answer(analysis: dict) -> str:
    delta = analysis["delta"]
    pct = analysis["change_pct"]
    contributors = analysis.get("possible_contributors", [])
    lines = [f"Infrastructure cost increased by ${delta:.2f} (+{pct}%)."]
    if contributors:
        lines.append("Possible contributors (ESTIMATED):")
        for c in contributors:
            lines.append(f"  • {c['resource']}: {c.get('change', '')} ≈ {c.get('estimated_impact', '')}")
    lines.append(analysis.get("note", ""))
    return "\n".join(lines)


def _format_forecast_answer(forecast: CostForecast) -> str:
    if not forecast.forecast_available:
        return "FORECAST UNAVAILABLE — insufficient cost data."
    return (
        f"FORECAST (ESTIMATED): Next 30 days ≈ ${forecast.next_30_days:.2f}, "
        f"Next 90 days ≈ ${forecast.next_90_days:.2f} "
        f"(assuming ~{forecast.trend_pct}% monthly growth). "
        f"{forecast.note}"
    )


# ─────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────

global_finops_service = FinOpsService()
