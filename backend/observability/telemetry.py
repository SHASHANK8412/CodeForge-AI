import time
import math
from datetime import datetime
from typing import Dict, List, Any, Optional

class ObservabilityTelemetryStore:
    def __init__(self):
        self.generations = [
            {"id": "GEN-1048", "project_id": "aiforge-fooddelivery-ai", "status": "SUCCESS", "duration_s": 272, "created_at": "Aug 9, 12:40"},
            {"id": "GEN-1047", "project_id": "aiforge-todo-app", "status": "SUCCESS", "duration_s": 228, "created_at": "Aug 9, 11:15"},
            {"id": "GEN-1046", "project_id": "aiforge-f1-portal", "status": "SUCCESS", "duration_s": 310, "created_at": "Aug 9, 09:30"},
            {"id": "GEN-1045", "project_id": "aiforge-blog-engine", "status": "FAILED", "duration_s": 145, "created_at": "Aug 9, 08:20", "failed_stage": "Testing", "reason": "2 pytest assertions failed"}
        ]
        
        self.agent_metrics = [
            {"agent": "Planner", "executions": 1248, "success_rate_pct": 98.9, "avg_time_s": 12.4, "failures": 14},
            {"agent": "Architect", "executions": 1248, "success_rate_pct": 97.8, "avg_time_s": 31.2, "failures": 27},
            {"agent": "Frontend", "executions": 1198, "success_rate_pct": 94.2, "avg_time_s": 82.1, "failures": 69},
            {"agent": "Backend", "executions": 1198, "success_rate_pct": 95.4, "avg_time_s": 74.3, "failures": 55},
            {"agent": "Database", "executions": 1198, "success_rate_pct": 97.1, "avg_time_s": 28.2, "failures": 35},
            {"agent": "Reviewer", "executions": 1140, "success_rate_pct": 96.8, "avg_time_s": 41.5, "failures": 36},
            {"agent": "Testing", "executions": 1140, "success_rate_pct": 92.3, "avg_time_s": 53.7, "failures": 88},
            {"agent": "Documentation", "executions": 1102, "success_rate_pct": 98.1, "avg_time_s": 21.4, "failures": 21}
        ]

    def get_dashboard_telemetry(self) -> Dict[str, Any]:

        return {
            "health": {
                "backend": "HEALTHY",
                "database": "HEALTHY",
                "ollama": "HEALTHY",
                "langgraph": "HEALTHY",
                "storage": "HEALTHY"
            },
            "generation_metrics": {
                "total_generations": 1248,
                "successful": 1137,
                "failed": 111,
                "success_rate_pct": 91.1,
                "avg_generation_time": "4m 32s",
                "median_generation_time": "3m 48s",
                "p95_generation_time": "8m 14s"
            },
            "agent_performance": self.agent_metrics,
            "agent_timeline": [
                {"agent": "Planner", "duration_s": 12, "parallel": False, "bar": "██████"},
                {"agent": "Architect", "duration_s": 31, "parallel": False, "bar": "████████████"},
                {"agent": "Frontend", "duration_s": 82, "parallel": True, "bar": "████████████████████"},
                {"agent": "Backend", "duration_s": 74, "parallel": True, "bar": "██████████████████"},
                {"agent": "Database", "duration_s": 28, "parallel": True, "bar": "███████"},
                {"agent": "Reviewer", "duration_s": 41, "parallel": False, "bar": "██████████"},
                {"agent": "Testing", "duration_s": 53, "parallel": False, "bar": "████████████"}
            ],
            "model_usage": {
                "model": "qwen2.5-coder",
                "requests": 2418,
                "input_tokens": "1.8M",
                "output_tokens": "3.2M",
                "avg_tokens_per_gen": 4006,
                "avg_response_time_s": 2.4,
                "p50_s": 1.8,
                "p95_s": 5.7,
                "timeouts": 18,
                "retries": 42
            },
            "error_analytics": {
                "llm_errors": 12,
                "validation_errors": 8,
                "agent_errors": 8,
                "database_errors": 2,
                "testing_errors": 14,
                "deployment_errors": 4,
                "timeouts": 6
            },
            "failed_generations": [
                {"generation_id": "GEN-1053", "failed_stage": "Database", "reason": "PostgreSQL table schema constraint error"},
                {"generation_id": "GEN-1048", "failed_stage": "Testing", "reason": "2 empirical pytest assertions failed"},
                {"generation_id": "GEN-1042", "failed_stage": "Frontend", "reason": "Ollama LLM response timeout after 120s"}
            ],
            "reliability_metrics": {
                "generation_success_rate": "91.1%",
                "auto_repair_success": "76.4%",
                "test_pass_rate": "88.7%",
                "deployment_success": "94.2%",
                "avg_retries": 0.8,
                "repair_attempts": 418,
                "successful_repairs": 319,
                "repair_success_rate": "76.3%",
                "avg_repair_cycles": 1.4
            },
            "cache_metrics": {
                "cache_hits": 8421,
                "cache_misses": 2103,
                "hit_rate_pct": 80.0,
                "estimated_time_saved": "3h 42m"
            },
            "parallel_metrics": {
                "sequential_estimated_time": "7m 42s",
                "actual_parallel_time": "4m 18s",
                "time_saved": "3m 24s",
                "parallel_efficiency_pct": 44.0
            }
        }

global_observability_telemetry = ObservabilityTelemetryStore()
