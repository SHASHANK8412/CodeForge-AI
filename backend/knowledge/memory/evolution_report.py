import logging
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

_logger = logging.getLogger("aiforge.knowledge")
NOT_RECORDED = "not recorded"


class EvolutionReportGenerator:
    """
    The self-evolution report, computed from the project-memory database (backend/knowledge/memory/project_memory.py):
    projects remembered, their stacks, and the bugs and lessons recorded for them. Metrics the database does not hold
    (review scores, test pass rates, stage timings) are reported as not recorded - never estimated.
    """

    def __init__(self, db_path: str = None) -> None:
        if db_path is None:
            db_path = str(Path(__file__).resolve().parents[1] / "memory" / "knowledge.db")
        self.db_path = Path(db_path)

    def _rows(self, sql: str) -> List[tuple]:
        if not self.db_path.is_file():
            return []
        try:
            with sqlite3.connect(str(self.db_path)) as con:
                return con.execute(sql).fetchall()
        except sqlite3.Error as e:          # a table that does not exist yet simply has no rows
            _logger.info("evolution report: %s", e)
            return []

    def generate_report(self) -> Dict[str, Any]:
        projects = self._rows("SELECT frontend, backend, database_name FROM projects")
        bugs = self._rows("SELECT category, description FROM bugs")
        lessons = self._rows("SELECT worked, failed FROM lessons")
        stacks = Counter(" + ".join(x for x in row if x) for row in projects if any(row))
        bug_kinds = Counter((cat or desc or "uncategorised") for cat, desc in bugs)
        failed = [f for _, f in lessons if f]
        report_data: Dict[str, Any] = {
            "total_projects": len(projects),
            "average_review_score": None,       # review scores are not stored in the project memory
            "test_pass_rate": None,             # test results are not stored in the project memory
            "most_common_architecture": stacks.most_common(1)[0][0] if stacks else None,
            "most_common_bugs": [{"bug": b, "count": n} for b, n in bug_kinds.most_common(5)],
            "performance_trends": None,         # stage timings are not stored in the project memory
            "recommendations": [f"Avoid: {f}" for f in failed[-3:]],
            "source": str(self.db_path.name),
        }

        report_dir = self.db_path.parent / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "self_evolution_report.md"

        def show(v: Optional[Any]) -> str:
            return NOT_RECORDED if v is None else str(v)
        md = ["# AIForge Self-Evolution Report", "", f"Computed from `{report_data['source']}`.", "",
              "## Summary", "",
              f"* **Projects remembered**: {report_data['total_projects']}",
              f"* **Most common stack**: {show(report_data['most_common_architecture'])}",
              f"* **Average review score**: {NOT_RECORDED}",
              f"* **Test pass rate**: {NOT_RECORDED}", "",
              "## Most common recorded bugs", ""]
        md += [f"{i}. **{b['bug']}** (seen {b['count']} times)" for i, b in enumerate(report_data["most_common_bugs"], 1)] or ["None recorded."]
        md += ["", "## Lessons recorded as failures", ""] + ([f"* {r}" for r in report_data["recommendations"]] or ["None recorded."])
        try:
            report_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        except OSError as e:
            _logger.error(f"Failed to write self_evolution_report.md: {e}")
        return report_data
