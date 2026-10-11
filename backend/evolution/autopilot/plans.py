"""
Improvement plans: selected findings become ordered tasks with a strategy, the files they may
touch, the checks that decide acceptance, risks and assumptions. A plan is only a proposal;
nothing runs until a person approves it.
"""

import uuid
from typing import Dict, List, Tuple

from backend.evolution.autopilot.models import Finding, FindingStatus, Plan, PlanTask

_CATEGORY_ORDER = {"security": 0, "syntax": 1, "quality": 2, "dependencies": 3, "tests": 4,
                   "maintainability": 5, "performance": 6}
# What actually performs each strategy (existing AIForge components, no new agents).
STRATEGY_AGENT = {
    "ruff_fix": "Debug Agent - deterministic fix (ruff --fix)",
    "add_requirements": "Debug Agent - repair strategy add_missing_requirements",
    "import_repair": "Debug Agent - repair strategies (missing / misplaced / shadowed imports)",
    "model": "Coding Agent - project editor (coding model, validated patch)",
    "manual": "Not automated - needs a person",
}
TEST_DIR = "tests/"
MAX_FINDINGS_PER_PLAN = 40
MAX_MODEL_FILES_PER_TASK = 3


class PlanError(ValueError):
    pass


def _task_files(f: Finding) -> List[str]:
    if f.fix_strategy == "add_requirements":
        return [p for p in (f.file, "requirements.txt") if p]
    if f.rule_id == "TESTS-NONE":
        return [TEST_DIR]
    return [f.file] if f.file else []


def build_plan(project_id: str, user_id: str, findings: List[Finding], objective: str = "") -> Plan:
    if not findings:
        raise PlanError("select at least one finding")
    if len(findings) > MAX_FINDINGS_PER_PLAN:
        raise PlanError(f"a plan can address at most {MAX_FINDINGS_PER_PLAN} findings")
    closed = [f.id for f in findings if f.status in (FindingStatus.DISMISSED, FindingStatus.RESOLVED,
                                                         FindingStatus.FIXED_VERIFIED)]
    if closed:
        raise PlanError(f"findings are not open: {', '.join(closed)}")

    ordered = sorted(findings, key=lambda f: (_CATEGORY_ORDER.get(f.category.value, 9), f.priority, f.file or ""))
    groups: Dict[Tuple[str, str], List[Finding]] = {}
    for f in ordered:
        if f.fix_strategy in ("ruff_fix", "add_requirements"):
            key = (f.fix_strategy, "*")                         # one deterministic pass for all of them
        else:
            key = (f.fix_strategy, f.file or f.rule_id)
        groups.setdefault(key, []).append(f)

    tasks: List[PlanTask] = []
    syntax_task_by_file: Dict[str, str] = {}
    for (strategy, _), group in groups.items():
        task_id = f"t{len(tasks) + 1}"
        files = sorted({p for f in group for p in _task_files(f)})
        if strategy == "model" and len([p for p in files if not p.endswith("/")]) > MAX_MODEL_FILES_PER_TASK:
            files = files[:MAX_MODEL_FILES_PER_TASK]
        rules = sorted({f.rule_id for f in group})
        title = (group[0].title if len(group) == 1 else f"{len(group)} findings: {', '.join(rules[:3])}"
                 + (" ..." if len(rules) > 3 else ""))
        depends = sorted({syntax_task_by_file[p] for p in files if p in syntax_task_by_file})
        tasks.append(PlanTask(
            id=task_id, title=title, finding_ids=[f.id for f in group], files=files, strategy=strategy,
            agent=STRATEGY_AGENT[strategy], depends_on=depends,
            modification=_modification(strategy, group),
        ))
        if any(f.category.value == "syntax" for f in group):
            for p in files:
                syntax_task_by_file.setdefault(p, task_id)

    expected = sorted({p for t in tasks if t.strategy != "manual" for p in t.files})
    strategies = {t.strategy for t in tasks}
    risks = ["Model-written changes can alter behaviour; they are kept only if no check regresses."] \
        if "model" in strategies else []
    if "add_requirements" in strategies:
        risks.append("New requirements change what gets installed; versions are left unpinned.")
    if "manual" in strategies:
        risks.append("Some findings have no safe automatic fix (e.g. committed secrets); those tasks are skipped "
                     "and stay open.")
    if any(t.files == [TEST_DIR] for t in tasks):
        risks.append("New tests may expose existing bugs; they are accepted only if the suite still passes.")
    approval = ["Apply the listed changes to the project after validation"]
    if "add_requirements" in strategies:
        approval.append("Add the listed packages to requirements.txt")
    return Plan(
        id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id,
        objective=objective.strip()[:500] or f"Resolve {len(findings)} selected finding(s)",
        finding_ids=[f.id for f in ordered], tasks=tasks, expected_files=expected,
        agents=sorted({t.agent for t in tasks}),
        checks=["python_syntax", "quality_gate", "security_static", "tests"],
        risks=risks,
        assumptions=[
            "Changes are made in an isolated copy of the project; the project itself is only written after the "
            "checks pass and none of the planned files changed meanwhile.",
            "Tests run only in the Docker sandbox. If Docker is unavailable the test check is reported as blocked, "
            "and acceptance rests on static checks only (stated in the report).",
            "Changes to files outside the expected list stop the run for approval.",
        ],
        approval_required=approval,
        completion_criteria=[
            "No check regresses against the baseline (syntax, quality-gate errors, high-severity security findings, tests).",
            "Each addressed finding is no longer detected by a fresh analysis.",
        ],
    )


def _modification(strategy: str, group: List[Finding]) -> str:
    if strategy == "ruff_fix":
        return "Remove unused imports with `ruff check --fix` (safe fixes only)."
    if strategy == "add_requirements":
        return "Declare the imported packages in requirements.txt."
    if strategy == "import_repair":
        return "Add or correct the imports reported by the quality gate."
    if strategy == "manual":
        return "No automatic change. " + group[0].remediation
    lines = [f"- {f.title}: {f.remediation}" for f in group[:8]]
    return "Model edit limited to the listed files:\n" + "\n".join(lines)


def scope_violations(plan: Plan, changed: List[str]) -> List[str]:
    """Changed files that the plan did not list (a listed folder covers new files inside it)."""
    allowed = set(plan.expected_files)
    folders = tuple(p for p in allowed if p.endswith("/"))
    return sorted(p for p in changed if p not in allowed and not p.startswith(folders))
