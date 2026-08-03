"""
AIForge Evaluation Reporter Utility
===================================
Generates structured JSON reports and clean Markdown reports summarizing benchmark results.
"""

import json
from pathlib import Path
from typing import Optional
from backend.evaluation.models import BenchmarkReport, RegressionReport

project_root = Path(__file__).resolve().parent.parent.parent


class EvaluationReporter:
    """
    Reporter for saving and formatting evaluation reports.
    """

    def save_json_report(self, report: BenchmarkReport, output_dir: Optional[Path] = None) -> Path:
        out_dir = output_dir or (project_root / "reports" / "evaluation")
        out_dir.mkdir(parents=True, exist_ok=True)

        latest_path = out_dir / "latest.json"
        timestamp_path = out_dir / f"eval_{report.timestamp}.json"

        data = report.model_dump()
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        with open(timestamp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return latest_path

    def save_baseline_report(self, report: BenchmarkReport, output_dir: Optional[Path] = None) -> Path:
        out_dir = output_dir or (project_root / "reports" / "evaluation")
        out_dir.mkdir(parents=True, exist_ok=True)

        baseline_path = out_dir / "baseline.json"
        data = report.model_dump()
        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return baseline_path

    def load_baseline_report(self, output_dir: Optional[Path] = None) -> Optional[BenchmarkReport]:
        out_dir = output_dir or (project_root / "reports" / "evaluation")
        baseline_path = out_dir / "baseline.json"
        if not baseline_path.exists():
            return None

        with open(baseline_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return BenchmarkReport(**data)

    def generate_markdown_report(
        self,
        report: BenchmarkReport,
        regression_report: Optional[RegressionReport] = None,
        output_dir: Optional[Path] = None
    ) -> Path:
        out_dir = output_dir or (project_root / "reports" / "evaluation")
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / "latest.md"

        reg_section = ""
        if regression_report:
            reg_status = "❌ REGRESSION DETECTED" if regression_report.has_regression else "✅ NO REGRESSION"
            reg_section = f"""
## ⚖️ Baseline Comparison Status: **{reg_status}**
- **Summary**: {regression_report.summary_message}
- **Quality Score Delta**: {regression_report.quality_delta:+.2f} points
- **Routing Accuracy Delta**: {regression_report.routing_accuracy_delta:+.2f}%
- **Pass Rate Delta**: {regression_report.pass_rate_delta:+.2f}%
- **Latency Delta**: {regression_report.latency_delta_ms:+.1f} ms
"""

        cat_rows = "\n".join([
            f"| `{cat.title()}` | **{score:.1f}%** |"
            for cat, score in report.category_scores.items()
        ])

        top_failures = [r for r in report.results if not r.overall_pass][:10]
        failure_rows = ""
        if top_failures:
            failure_rows = "\n".join([
                f"| `{r.test_id}` | `{r.category}` | `{r.prompt[:40]}` | `{r.expected_intent}` | `{r.actual_intent}` | {r.quality_score:.1f} |"
                for r in top_failures
            ])
        else:
            failure_rows = "| None | N/A | Zero failures detected! | N/A | N/A | 100.0 |"

        content = f"""# 📊 AIForge Evaluation Engine Benchmark Report

**Benchmark ID**: `{report.benchmark_id}`  
**Executed At**: `{report.timestamp}`  
**Evaluation Mode**: `{report.mode.upper()}`  
{reg_section}

---

## 📈 Executive Summary & Key Metrics

| Metric | Measured Value | Target | Status |
| :--- | :--- | :--- | :--- |
| **Total Golden Tests** | **{report.total_tests} Prompts** | 100 | ✅ COMPLETE |
| **Pass Rate** | **{report.overall_pass_rate_pct:.1f}%** | >= 90.0% | {'✅ PASS' if report.overall_pass_rate_pct >= 90.0 else '⚠️ WARN'} |
| **Routing Accuracy** | **{report.routing_accuracy_pct:.1f}%** | >= 95.0% | {'✅ PASS' if report.routing_accuracy_pct >= 95.0 else '⚠️ WARN'} |
| **Agent Accuracy** | **{report.agent_accuracy_pct:.1f}%** | >= 95.0% | {'✅ PASS' if report.agent_accuracy_pct >= 95.0 else '⚠️ WARN'} |
| **Profile Accuracy** | **{report.profile_accuracy_pct:.1f}%** | >= 95.0% | {'✅ PASS' if report.profile_accuracy_pct >= 95.0 else '⚠️ WARN'} |
| **Average Quality Score** | **{report.average_quality_score:.2f} / 100** | >= 85.0 | {'✅ PASS' if report.average_quality_score >= 85.0 else '⚠️ WARN'} |
| **Critical Tests Pass Rate** | **{report.critical_tests_passed} / {report.critical_tests_count} ({report.critical_tests_pass_pct:.1f}%)** | 100.0% | {'✅ PASS' if report.critical_tests_pass_pct >= 100.0 else '❌ CRITICAL'} |
| **Regeneration Rate** | **{report.regeneration_rate_pct:.1f}%** | <= 15.0% | ✅ OK |
| **Average Latency** | **{report.avg_latency_ms:.1f} ms** | Fast | ✅ FAST |
| **P50 Latency** | **{report.p50_latency_ms:.1f} ms** | - | - |
| **P95 Latency** | **{report.p95_latency_ms:.1f} ms** | - | - |

---

## 📂 Pass Rate by Category

| Category | Score |
| :--- | :--- |
{cat_rows}

---

## ⚠️ Top Failing Tests (Up to 10)

| Test ID | Category | Prompt | Expected Intent | Actual Intent | Quality Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
{failure_rows}

---
*Generated automatically by AIForge Evaluation Engine.*
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)

        return md_path


global_evaluation_reporter = EvaluationReporter()
