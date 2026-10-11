"""
What-if simulation: a read-only impact report for a proposed change (and optional alternatives).

Nothing is executed and nothing is written to the project. The project's file fingerprint is
taken before and after the simulation; the report records whether it changed (it can only change
if something else edited the project meanwhile).
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.twin import impact, risk
from backend.twin.graph import project_fingerprint
from backend.twin.index import GraphIndex
from backend.twin.models import GraphAnalysis, Prediction

_logger = logging.getLogger("aiforge.twin")
MAX_ALTERNATIVES = 3


def tooling() -> Dict[str, bool]:
    from backend.execution.docker_test_sandbox import docker_available
    from backend.validation.quality_gate import _oxlint
    try:
        import bandit  # noqa: F401
        has_bandit = True
    except ImportError:
        has_bandit = False
    try:
        docker = bool(docker_available())
    except Exception:  # noqa: BLE001 - an unreachable daemon counts as unavailable
        docker = False
    return {"docker": docker, "oxlint": bool(_oxlint()), "bandit": has_bandit}


def simulate(project: Path, graph: GraphAnalysis, request: str, *, target_files: Optional[List[str]] = None,
             alternatives: Optional[List[str]] = None, generate: Optional[Callable[[str, str], str]] = None,
             history: Optional[Dict[str, Any]] = None, tools: Optional[Dict[str, bool]] = None
             ) -> Tuple[List[Prediction], Dict[str, Any], List[str], List[str], int]:
    """(options, planner info, assumptions, limitations, files changed during the simulation)."""
    project = Path(project).resolve()
    before = project_fingerprint(project)
    index = GraphIndex(graph)
    index.project_root = project                        # lets test selection read test files (read-only)
    tools = tools if tools is not None else tooling()
    targets = [t for t in (target_files or []) if t in index.files]
    bad_targets = [t for t in (target_files or []) if t not in index.files]
    planner = {"used": bool(generate), "status": "not requested"}
    options: List[Prediction] = []
    texts = [("Requested change", request)] + [(f"Alternative {chr(66 + i)}", a)
                                                for i, a in enumerate((alternatives or [])[:MAX_ALTERNATIVES]) if a.strip()]
    for label, text in texts:
        seeds = [{"path": t, "source": "chosen by you", "certainty": "established",
                  "reason": "selected as a file to change"} for t in targets]
        create: List[str] = []
        kinds_from_model: List[str] = []
        uncertainties: List[str] = []
        if generate is not None:
            try:
                model_seeds, create, kinds_from_model, notes = impact.planner_proposal(index, text, generate)
                seeds += [s for s in model_seeds if s["path"] not in {x["path"] for x in seeds}]
                planner = {"used": True, "status": "ok", "notes": notes}
            except Exception as e:  # noqa: BLE001 - the planner is optional; the rules still run
                planner = {"used": True, "status": f"unavailable ({type(e).__name__})"}
                uncertainties.append("the planner model was unavailable; targets come from keyword matching only")
        unmatched: List[str] = []
        if not seeds:
            kw, unmatched = impact.keyword_seeds(index, text)
            seeds = kw
        kinds = sorted(set(impact.change_kinds(text, index, [s["path"] for s in seeds])) | set(kinds_from_model))
        pred = impact.predict(index, text, label, seeds, create, kinds)

        risk.select_tests(pred, index)
        risk.assess(pred, index, history)
        if pred.risk in ("high", "critical"):
            risk.select_tests(pred, index)                # adds the broad regression run
        risk.validation_steps(pred, tools)

        if not pred.seeds:
            uncertainties.append("no project file matches the request; the change probably adds new code whose "
                                 "location the analysis cannot determine - choose the target files explicitly")
        elif all(s["certainty"] == "inferred" for s in pred.seeds):
            uncertainties.append("the target files were inferred (keyword or model match), not chosen; check the "
                                 "modification scope before approving")
        if unmatched:
            uncertainties.append(f"the request mentions {', '.join(unmatched[:6])}, which do not appear in the "
                                 "project: new code or dependencies are likely and their impact is not modelled")
        inferred = [d["path"] for d in pred.direct + pred.transitive if d["certainty"] == "inferred"]
        if inferred:
            uncertainties.append(f"{len(inferred)} dependent file(s) are linked only by inferred edges "
                                 f"(e.g. {inferred[0]})")
        area = set(pred.modify_scope) | {d["path"] for d in pred.direct}
        unresolved = [u for u in graph.unresolved if u.get("file") in area]
        if unresolved:
            uncertainties.append(f"{len(unresolved)} import(s) in the affected area could not be resolved "
                                 f"(e.g. {unresolved[0]['file']}:{unresolved[0].get('line')}: {unresolved[0]['reason']})")
        if bad_targets:
            uncertainties.append(f"chosen file(s) not in the graph and ignored: {', '.join(bad_targets[:5])}")
        if not tools.get("docker"):
            uncertainties.append("Docker is not available: the selected tests cannot run in the sandbox here")
        pred.uncertainties = uncertainties
        options.append(pred)

    assumptions = [
        "Dependencies are read from the source as it was when the graph was built; runtime behaviour "
        "(dynamic imports, reflection, configuration-driven wiring, network calls) is not modelled.",
        "A file is 'affected' when it imports, uses, renders or calls something in a changed file, directly "
        f"or through up to {impact.MAX_DEPTH} levels.",
        "The risk category is a rule-based ranking for review effort, not a measured probability of failure.",
        "No detected impact does not mean the change is safe: only the checks after implementation show that.",
    ]
    limitations = list(graph.limits)
    after = project_fingerprint(project)
    changed = 0 if before == after else 1
    if changed:
        limitations.append("the project's files changed while the simulation ran (another editor or process); "
                           "the report may not match the current code")
    return options, planner, assumptions, limitations, changed
