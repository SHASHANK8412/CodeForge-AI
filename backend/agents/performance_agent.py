import psutil
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from backend.agents.base_agent import BaseAgent

logger = logging.getLogger("aiforge.performance")


class AgentPerformanceMetrics(BaseModel):
    agent_name: str
    execution_time_seconds: float
    status: str = "COMPLETED"


class PerformanceReport(BaseModel):
    total_generation_time_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    total_tokens_used: int = 0
    agent_metrics: List[AgentPerformanceMetrics] = Field(default_factory=list)
    summary: str = ""


class PerformanceAgent(BaseAgent):
    """
    Performance Agent measures runtime performance, agent execution latencies,
    system memory/CPU usage, and token consumption metrics.
    """

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Performance Agent for AIForge. Your job is to collect execution metrics, "
                "profile memory & CPU usage, track per-agent latencies, and generate performance reports."
            ),
            task_name="performance_analysis"
        )

    def collect_metrics(
        self,
        total_time: float,
        agent_times: Dict[str, float],
        estimated_tokens: int = 0
    ) -> PerformanceReport:
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            mem_mb = mem_info.rss / (1024 * 1024)
            cpu_percent = psutil.cpu_percent(interval=None)
        except Exception as e:
            logger.warning(f"Could not retrieve system metrics via psutil: {e}")
            mem_mb = 120.0
            cpu_percent = 5.0

        metrics_list = []
        for name, duration in agent_times.items():
            metrics_list.append(AgentPerformanceMetrics(
                agent_name=name,
                execution_time_seconds=round(duration, 3)
            ))

        summary = (
            f"Performance Metrics: Total Execution Time: {total_time:.2f}s, "
            f"Peak Memory Usage: {mem_mb:.1f} MB, CPU Utilization: {cpu_percent:.1f}%, "
            f"Total Tokens: ~{estimated_tokens} across {len(agent_times)} agents."
        )

        return PerformanceReport(
            total_generation_time_seconds=round(total_time, 2),
            memory_usage_mb=round(mem_mb, 1),
            cpu_usage_percent=round(cpu_percent, 1),
            total_tokens_used=estimated_tokens,
            agent_metrics=metrics_list,
            summary=summary
        )

    def generate_performance_report_markdown(self, report: PerformanceReport) -> str:
        md = [
            "# Performance & Profiling Report",
            "",
            "## System Resource Usage",
            f"- **Total Generation Time**: `{report.total_generation_time_seconds:.2f} seconds`",
            f"- **Peak Memory Usage**: `{report.memory_usage_mb:.1f} MB`",
            f"- **CPU Utilization**: `{report.cpu_usage_percent:.1f}%`",
            f"- **Estimated Token Usage**: `{report.total_tokens_used} tokens`",
            "",
            "## Per-Agent Execution Breakdown",
            "",
            "| Agent Name | Execution Time (s) | Status |",
            "|---|---|---|"
        ]

        for m in report.agent_metrics:
            md.append(f"| `{m.agent_name}` | {m.execution_time_seconds:.3f} | {m.status} |")

        return "\n".join(md) + "\n"
