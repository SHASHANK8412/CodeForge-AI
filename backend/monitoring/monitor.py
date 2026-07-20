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

            # 5. Root Cause Analysis
            diagnostics = self.root_cause_analyzer.analyze(
                incidents=[i.model_dump() for i in detected_incidents],
                metrics=metrics,
                health=health
            )

            # 6. Self-Healing Loop
            success = False
            attempts = 0
            max_attempts = sre_settings.retry_count
            strategy_tried = "None"
            exec_time = 0.0

            while not success and attempts < max_attempts:
                attempts += 1
                strategy_tried, duration = self.recovery_engine.execute_recovery(
                    signature=primary_incident.signature,
                    recommendation=diagnostics,
                    attempt_number=attempts
                )
                exec_time += duration

                # Validate
                success, validation_log = await self.validator.validate_recovery()
                
                # Register in KB memory
                self.knowledge_base.add_record(
                    signature=primary_incident.signature,
                    root_cause=diagnostics.get("root_cause", "Unknown"),
                    strategy=strategy_tried,
                    success=success,
                    duration_seconds=exec_time,
                    confidence=diagnostics.get("confidence", 0.5)
                )

                if success:
                    # Clear active incident
                    self.active_incidents = []
                    # Dispatch success alert
                    self.alert_manager.dispatch_alert(
                        incident_signature=primary_incident.signature,
                        severity=primary_incident.severity,
                        affected_service=primary_incident.service,
                        details=f"Self-healing successfully resolved incident. Strategy: {strategy_tried}",
                        recovery_status="Resolved",
                        mttr_seconds=exec_time
                    )
                    break
            
            if not success:
                _logger.error(f"SRE self-healing failed for signature '{primary_incident.signature}' after {attempts} attempts.")
                # Dispatch critical failure alert
                self.alert_manager.dispatch_alert(
                    incident_signature=primary_incident.signature,
                    severity="Emergency",
                    affected_service=primary_incident.service,
                    details=f"Self-healing failed after {attempts} attempts. Manual intervention requested.",
                    recovery_status="Failed"
                )

            recovery_summary = {
                "success": success,
                "strategy": strategy_tried,
                "attempts": attempts,
                "duration_seconds": exec_time,
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
