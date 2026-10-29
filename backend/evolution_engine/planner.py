"""
Experiment planning: hypothesis, baseline, candidate strategies, environment, required tests, metrics,
thresholds, limits and cleanup - decided before any candidate exists. A plan whose acceptance criteria
cannot be evaluated reliably is rejected with the reasons (it is never run).
"""

from pathlib import Path
from typing import Dict, List, Optional

from backend.evolution_engine.discovery import data_access
from backend.evolution_engine.memory import guide
from backend.evolution_engine.models import ExperimentPlan, Opportunity, Strategy, Weights
from backend.performance.engineer.models import Endpoint, Thresholds, Workload

MAX_CANDIDATES = 3
KEEP = ("Keep the response exactly the same for every request: the same fields, the same order of items, and items "
        "that have no related rows must still appear (with an empty list). Do not change routes, parameters or status "
        "codes. Use bound query parameters, never string formatting, for SQL. Do not add dependencies.")

STRATEGIES: Dict[str, List[Strategy]] = {
    "raw_sql": [
        Strategy(id="join_query", title="One JOIN query, grouped in Python",
                 instructions="Replace the query inside the loop with a single LEFT JOIN query that returns every parent "
                              "row with its related rows, then group the rows in Python. " + KEEP),
        Strategy(id="batch_in_query", title="Two queries: parents, then all related rows with IN (...)",
                 instructions="Load the parent rows once, then load all related rows in one query using "
                              "WHERE parent_id IN (?, ?, ...) with one bound parameter per id, and attach them in Python. " + KEEP),
        Strategy(id="single_query_aggregate", title="One query with a JSON/aggregate column",
                 instructions="Use a single query that aggregates the related rows per parent (for example GROUP BY with "
                              "json_group_array in SQLite) and decode it in Python. " + KEEP),
    ],
    "sqlalchemy": [
        Strategy(id="eager_selectinload", title="Eager loading with selectinload",
                 instructions="Load the relationship with sqlalchemy.orm.selectinload in the parent query so that the "
                              "loop no longer triggers a query per row. " + KEEP),
        Strategy(id="eager_joinedload", title="Eager loading with joinedload",
                 instructions="Load the relationship with sqlalchemy.orm.joinedload (use .unique() where SQLAlchemy "
                              "requires it). " + KEEP),
        Strategy(id="batch_in_query", title="Two queries: parents, then related rows with in_()",
                 instructions="Query all related rows once with Column.in_(ids) and attach them in Python. " + KEEP),
    ],
}


def plan_experiment(opportunity: Opportunity, project: Path, max_candidates: int = 2, weights: Optional[Weights] = None,
                    thresholds: Optional[Thresholds] = None, overrides: Optional[Dict[str, str]] = None,
                    workload: Optional[Workload] = None) -> ExperimentPlan:
    reasons: List[str] = []
    if not opportunity.experimentable:
        reasons.append(opportunity.not_experimentable_reason or "this opportunity cannot be experimented on")
    if not 1 <= max_candidates <= MAX_CANDIDATES:
        reasons.append(f"between 1 and {MAX_CANDIDATES} candidates can be generated per experiment")
    source = ""
    if opportunity.file:
        try:
            source = (Path(project) / opportunity.file).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            reasons.append(f"{opportunity.file} could not be read as UTF-8 text")
    access = data_access(source)
    available = STRATEGIES.get(access, [])
    if not available and not reasons:
        reasons.append(f"no candidate strategies exist for data access '{access}'")
    strategies, suppressed = guide([s.model_copy() for s in available], opportunity.history, overrides or {})
    strategies = strategies[:max(1, min(max_candidates, MAX_CANDIDATES))]
    if available and not strategies:
        reasons.append("every known strategy failed here before; give a new justification to try one again")
    target = opportunity.endpoint or ""
    method, _, path = target.partition(" ")
    endpoints = [Endpoint(method=method or "GET", path=path or "/")]
    # 5 repetitions of 150 requests: short repetitions gave medians too noisy to confirm a real 60-70% gain
    load = workload or Workload(endpoints=endpoints, requests_per_endpoint=150, concurrency=2, warmup_requests=30,
                                repetitions=5, max_seconds_per_endpoint=30.0)
    if not load.endpoints:
        load.endpoints = endpoints
    if load.repetitions < 2:
        reasons.append("at least 2 repetitions are needed to know the run-to-run variation")
    t = thresholds or Thresholds(min_improvement_pct=10.0, max_regression_pct=15.0, noise_factor=2.0)
    return ExperimentPlan(
        hypothesis=opportunity.hypothesis,
        baseline="the project as it is (source revision recorded when the experiment starts), measured in the same run",
        strategies=strategies,
        environment=("each candidate in its own copy of one frozen snapshot of the project; tests in the Docker sandbox "
                     "(no network, non-root); all versions measured side by side in hardened containers with "
                     "alternating repetitions"),
        required_tests=["the project's own test suite (must not regress)", "Security Guardian static re-check "
                        "(no new critical/high findings)", "syntax and quality gate"],
        metrics=[f"median latency of {target} (target)", "p95 latency", "error rate", "throughput",
                 "peak memory and average CPU of the container", "changed lines and branch count (maintainability)"],
        workload=load, thresholds=t, target_endpoints=[target] if target else [],
        weights=weights or Weights(), allowed_files=[opportunity.file] if opportunity.file else [],
        safety=["the original project is never modified during the experiment",
                "generated code runs only in containers (no network for tests, non-root, read-only root for the app)",
                "the model sees no secret values (secret lines are hidden and restored)",
                "a candidate may change only the listed file"],
        max_seconds=3600, resource_limits={"app container": "1 CPU, 1 GB memory, 128 processes",
                                          "tests": "Docker sandbox defaults (no network)"},
        cleanup=["candidate and snapshot workspaces are deleted", "measurement containers and volumes are removed",
                 "test containers are removed by the sandbox"],
        rejected_reasons=reasons, suppressed_strategies=suppressed,
        context={"data_access": access, "file": opportunity.file, "endpoint": opportunity.endpoint})
