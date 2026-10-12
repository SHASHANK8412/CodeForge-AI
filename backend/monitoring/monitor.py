import time
import logging
import asyncio
from typing import Dict, Any, List, Optional
from backend.monitoring.config import sre_settings
from backend.monitoring.metrics_collector import MetricsCollector
from backend.monitoring.health_checker import HealthChecker
from backend.monitoring.incident_detector import IncidentDetector, Incident
from backend.monitoring.root_cause import RootCauseAnalyzer
from backend.monitoring.recovery_engine import RecoveryEngine
from backend.monitoring.validator import RecoveryValidator
from backend.monitoring.autoscaler import AutoScaler
from backend.monitoring.predictor import FailurePredictor
from backend.monitoring.alert_manager import AlertManager
from backend.monitoring.knowledge_base import IncidentKnowledgeBase
from backend.monitoring.analytics import OperationsAnalytics

_logger = logging.getLogger("aiforge.sre")

class OpsMonitor:
    """
    Main SRE operations orchestrator combining metrics gathering, anomaly checks,
    automatic healing execution, alerting, scaling, and analytics.
    """

    def __init__(
        self,
        ollama_url: str = "http://127.0.0.1:11434",
        kb_file_path: str = None
    ) -> None:
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker(ollama_url=ollama_url)
        self.incident_detector = IncidentDetector()
        self.root_cause_analyzer = RootCauseAnalyzer()
        
        self.knowledge_base = IncidentKnowledgeBase(file_path=kb_file_path)
        self.recovery_engine = RecoveryEngine(knowledge_base=self.knowledge_base)
        self.validator = RecoveryValidator(health_checker=self.health_checker)
        
        self.autoscaler = AutoScaler(
            cpu_threshold=sre_settings.scaling_cpu_threshold,
            mem_threshold=sre_settings.scaling_mem_threshold,
            queue_threshold=sre_settings.scaling_queue_threshold
        )
        self.predictor = FailurePredictor(prediction_window_seconds=sre_settings.prediction_window)
        self.alert_manager = AlertManager(active_channels=sre_settings.alert_channels)
        self.analytics = OperationsAnalytics()

        self.scaling_events: List[Dict[str, Any]] = []
        self.active_incidents: List[Incident] = []
        self.latest_health_check: Dict[str, Any] = {}
        self.latest_metrics: Dict[str, Any] = {}

    async def execute_operations_step(self) -> Dict[str, Any]:
        """
        Executes a single step of the SRE loop: checks telemetry, scale metrics, runs healing if needed.
        """
        # 1. Telemetry & Health Checks
        metrics = self.metrics_collector.collect_metrics()
        self.latest_metrics = metrics
        
        health = await self.health_checker.run_comprehensive_check()
        self.latest_health_check = health

        # 2. Check scaling thresholds
        scaling_decisions = self.autoscaler.evaluate_scaling(metrics)
        if scaling_decisions:
            self.scaling_events.extend(scaling_decisions)

        # 3. Forecast failures
        predictions = self.predictor.predict_failures(self.metrics_collector.get_history())

        # 4. Incident Detection
        detected_incidents = self.incident_detector.detect_incidents(metrics, health)
        self.active_incidents = detected_incidents

        recovery_summary: Optional[Dict[str, Any]] = None

        if detected_incidents:
            primary_incident = detected_incidents[0]
            _logger.warning(f"SRE active incident detected: {primary_incident.description}")
            
            # Dispatch Initial alert
            self.alert_manager.dispatch_alert(
                incident_signature=primary_incident.signature,
                severity=primary_incident.severity,
                affected_service=primary_incident.service,
                details=primary_incident.description,
                recovery_status="Triggered"
            )

            # 5. Root Cause Analysis (blocking LLM call - must stay off the event loop)
            if sre_settings.llm_root_cause_enabled:
                diagnostics = await asyncio.to_thread(
                    self.root_cause_analyzer.analyze,
                    incidents=[i.model_dump() for i in detected_incidents],
                    metrics=metrics,
                    health=health,
                )
            else:
                diagnostics = {
                    "incident": primary_incident.description,
                    "severity": primary_incident.severity,
                    "service": primary_incident.service,
                    "root_cause": f"Threshold rule '{primary_incident.signature}' triggered (LLM RCA disabled)",
                    "affected_components": [primary_incident.service],
                    "confidence": 0.5,
                    "recommended_action": "None",
                }

            # 6. Recovery: no recovery executor is connected (RecoveryEngine only describes what it would
            # run), so nothing is executed and the incident is not reported as resolved.
            strategy = self.recovery_engine.recommend(primary_incident.signature, diagnostics)
            recovery_summary = {
                "executed": False,
                "success": None,
                "recommended_strategy": strategy,
                "note": "no recovery action was executed: AIForge has no recovery executor connected; "
                        "the incident stays open until the metrics recover",
            }

        # Calculate latest analytics
        analytics_report = self.analytics.calculate_metrics(
            history_records=self.knowledge_base.get_records(),
            scaling_events_count=len(self.scaling_events)
        )

        return {
            "timestamp": time.time(),
            "health_score": health.get("health_score", 100),
            "active_incidents": [i.model_dump() for i in self.active_incidents],
            "scaling_events": scaling_decisions,
            "predictions": predictions,
            "recovery_summary": recovery_summary,
            "analytics": analytics_report,
        }
