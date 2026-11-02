"""
AIForge Benchmark Lab — Report Generator
========================================
Generates publication-ready markdown and structured JSON benchmark reports
documenting configuration rankings, objective metrics, trade-offs, and evidence.
"""

from typing import Dict, Any, List
from backend.benchmark_lab.models import BenchmarkRun


class BenchmarkReporter:
    """
    Renders comprehensive markdown and JSON benchmark reports.
    """

    def generate_markdown_report(self, run: BenchmarkRun, comparison: Dict[str, Any]) -> str:
        ranked_configs: List[Dict[str, Any]] = comparison.get("ranked_configurations", [])
        trade_offs: List[Dict[str, Any]] = comparison.get("trade_offs", [])

        total_tasks = len(run.results)
        completed_tasks = sum(1 for r in run.results if r.status == "COMPLETED")
        failed_tasks = sum(1 for r in run.results if r.status == "FAILED")
        timed_out_tasks = sum(1 for r in run.results if r.status == "TIMED_OUT")
        cancelled_tasks = sum(1 for r in run.results if r.status == "CANCELLED")
        not_run_tasks = sum(1 for r in run.results if r.status == "NOT_RUN")

        md = []
        md.append(f"# 🧪 AIForge Benchmark Lab — Evaluation Report")
        md.append(f"**Run Identifier:** `{run.id}`  ")
        md.append(f"**Run Name:** {run.name}  ")
        md.append(f"**Execution Status:** `{run.status}`  ")
        md.append(f"**Timestamp:** {run.created_at}  ")
        md.append(f"**Optimization Priority:** `{run.priority.value if hasattr(run.priority, 'value') else str(run.priority)}`  ")
        md.append(f"**Iterations per Task:** {run.repeated_runs}  ")
        md.append("\n---\n")

        # 1. Executive Summary
        md.append("## 1. Executive Summary\n")
        md.append(f"- **Evaluated Tasks:** {total_tasks} total executions")
        md.append(f"- **Successful Completions:** {completed_tasks} ({(completed_tasks/max(1, total_tasks)*100):.1f}%)")
        md.append(f"- **Not validated (not run):** {not_run_tasks}")
        md.append(f"- **Failed Tasks:** {failed_tasks}")
        md.append(f"- **Timeouts / Cancelled:** {timed_out_tasks + cancelled_tasks}")
        md.append(f"- **Configurations Compared:** {len(run.configurations)}")
        if ranked_configs:
            top = ranked_configs[0]
            md.append(f"- **Top Recommended Configuration:** **{top['config_name']}** (Score: {top['composite_score']}/100)")
        md.append("\n---\n")

        # 2. Configuration Ranking Table
        md.append("## 2. Configuration Ranking & Comparative Metrics\n")
        md.append("| Rank | Configuration | Model | Workflow | Test Pass Rate | Build Rate | Quality | Avg Duration | Score |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for cfg in ranked_configs:
            md.append(
                f"| #{cfg['rank']} | **{cfg['config_name']}** | `{cfg['model_name']}` | {cfg['workflow']} | "
                f"{cfg['test_pass_rate']}% | {cfg['build_success_rate']}% | {cfg['mean_quality']}% | "
                f"{cfg['mean_duration_seconds']}s (±{cfg.get('std_duration', 0.0)}s) | **{cfg['composite_score']}** |"
            )
        md.append("\n---\n")

        # 3. Trade-off Analysis
        md.append("## 3. Trade-off Analysis\n")
        if trade_offs:
            for to in trade_offs:
                md.append(f"### {to['comparison']}")
                md.append(f"> {to['analysis']}")
                md.append("")
        else:
            md.append("Single configuration evaluated or insufficient variation for comparative trade-off analysis.\n")
        md.append("\n---\n")

        # 4. Detailed Task-by-Task Execution Breakdown
        md.append("## 4. Task-Level Objective Results\n")
        md.append("| Task | Configuration | Status | Tests Passed | Adherence | Code Quality | Duration | Repairs |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for r in run.results:
            tests_display = f"{r.metrics.tests_passed}/{r.metrics.tests_total}" if r.metrics.tests_total > 0 else "N/A"
            md.append(
                f"| **{r.task_name}** | `{r.config_id}` | `{r.status}` | {tests_display} | "
                f"{r.metrics.requirement_adherence}% | {r.metrics.code_quality}% | {r.metrics.duration_seconds}s | {r.metrics.repair_attempts} |"
            )
        md.append("\n---\n")

        # 5. Recommendations
        md.append("## 5. Evidence-Backed Engineering Recommendations\n")
        for rec in run.recommendations:
            md.append(f"### 💡 {rec.get('title', 'Recommendation')}")
            md.append(f"- **Recommended Configuration:** `{rec.get('recommended_configuration')}`")
            md.append(f"- **Target Scenario:** {rec.get('target_scenario')}")
            md.append(f"- **Observed Evidence:** {rec.get('evidence')}")
            md.append(f"- **Trade-offs:** {rec.get('trade_offs')}")
            md.append(f"- **Confidence:** {rec.get('confidence')} (Evaluated across {rec.get('sample_size')} runs)")
            md.append("- **Action Policy:** *Review and approval required prior to modifying production pipelines.*")
            md.append("")

        # 6. Known Limitations
        md.append("\n---\n")
        md.append("## 6. Benchmark Methodology & Known Limitations\n")
        md.append("1. **Local Model Loading & Warmup:** Execution durations include initial model memory load latency on cold starts.")
        md.append("2. **Hardware Constraints:** All benchmarks executed sequentially under single-worker concurrency to prevent GPU memory saturation.")
        md.append("3. **Isolated Sandboxing:** Code executed with environment credentials strictly scrubbed to guarantee safety.")

        return "\n".join(md)


global_benchmark_reporter = BenchmarkReporter()
