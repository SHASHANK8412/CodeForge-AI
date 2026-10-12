"""
AIForge Reality Simulator REST API (project access is checked as for Autopilot).

  GET  /api/projects/{id}/reality/model                         the application model (Digital Twin evidence)
  POST /api/projects/{id}/reality/simulations                   {"scenario": {...}, "run_load": bool, "approved": bool}
  GET  /api/projects/{id}/reality/simulations
  GET  /api/projects/{id}/reality/simulations/{sid}
  POST /api/projects/{id}/reality/simulations/{sid}/cancel
  GET  /api/projects/{id}/reality/simulations/{sid}/report?format=markdown|json
  GET  /api/reality/calibration                                 prediction accuracy by comparable group
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.evolution.autopilot.redact import redact
from backend.evolution.routes import _project_dir, _user_id
from backend.reality.models import Scenario
from backend.reality.service import Busy, SimulationError, application_model, global_reality_simulator

reality_router = APIRouter(tags=["AIForge Reality Simulator"])
BASE = "/api/projects/{project_id}/reality"


def _sim():
    return global_reality_simulator


class StartRequest(BaseModel):
    scenario: Scenario
    run_load: bool = False
    approved: bool = False


@reality_router.get(BASE + "/model")
def model(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return {"model": application_model(_project_dir(project_id, user))}


@reality_router.post(BASE + "/simulations", status_code=202)
def start(project_id: str, body: StartRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    path = _project_dir(project_id, user)
    try:
        s = _sim().start(project_id, path, _user_id(user), body.scenario, body.run_load, body.approved)
    except SimulationError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Busy as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return {"simulation": s.model_dump(mode="json")}


@reality_router.get(BASE + "/simulations")
def simulations(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    items = sorted(_sim().store.list(project_id, "simulations"), key=lambda s: s.created_at, reverse=True)
    return {"simulations": [{"id": s.id, "name": s.scenario.name, "status": s.status, "run_load": s.run_load,
                             "created_at": s.created_at, "recommendation": s.recommendation.get("recommendation")}
                            for s in items[:50]], "active": _sim().active(project_id)}


def _get(project_id: str, sid: str):
    s = _sim().store.get(project_id, "simulations", sid)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Simulation not found.")
    return s


@reality_router.get(BASE + "/simulations/{sid}")
def simulation(project_id: str, sid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    return {"simulation": _get(project_id, sid).model_dump(mode="json")}


@reality_router.post(BASE + "/simulations/{sid}/cancel")
def cancel(project_id: str, sid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    _project_dir(project_id, user)
    _get(project_id, sid)
    s = _sim().cancel(project_id, sid)
    return {"simulation": {"id": s.id, "status": s.status, "cancel_requested": s.cancel_requested}}


@reality_router.get(BASE + "/simulations/{sid}/report")
def report(project_id: str, sid: str, format: str = Query("markdown", pattern="^(markdown|json)$"),
           user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    s = _get(project_id, sid)
    if format == "json":
        return json.loads(redact(s.model_dump_json()))
    lines = [f"# Reality Simulator report - {s.scenario.name}", "", f"Simulation `{s.id}` ({s.status}), revision `{(s.revision or '')[:12]}`.",
             "", "Predictions are analytical estimates; only the 'measured' sections come from runs against isolated copies.", "",
             "## Scenario (your assumptions)", "", f"- traffic: {s.scenario.traffic.model_dump()}"]
    lines += [f"- assumption: {a}" for a in s.scenario.assumptions]
    lines += ["", "## Baseline (measured)", ""] + [f"- {k}: median {v['median_ms']} ms (repetitions {v['rep_medians_ms']})"
                                                   for k, v in (s.baseline.get("endpoints") or {}).items()]
    for alt in s.scenario.alternatives:
        p, m, c = s.predictions.get(alt.id) or {}, s.measurements.get(alt.id) or {}, s.comparisons.get(alt.id) or {}
        lines += ["", f"## {alt.title} ({alt.id}) - {alt.resources.model_dump()}"
                  + (f", dependency +{alt.dependency_latency_ms} ms" if alt.dependency_latency_ms is not None else ""), "",
                  f"- predicted ({p.get('method', '-')}): utilisation {p.get('utilization')}, throughput {p.get('throughput_rps')} rps, "
                  f"mean {p.get('mean_ms')} ms, p95 {p.get('p95_ms')} ms, bounds {p.get('bounds')}" + (f" - {p.get('note')}" if p.get("note") else ""),
                  "- calibrated estimate: " + ("; ".join(f"{k} {v['value']} (x{v['factor']} from {v['records']} runs)" if v.get("value") is not None
                                                         else f"{k}: {v['note']}" for k, v in (p.get("calibrated") or {}).items()) or "n/a"),
                  f"- measured: {('throughput ' + str(m.get('throughput_rps')) + ' rps, mean ' + str(m.get('mean_ms')) + ' ms, p95 ' + str(m.get('p95_ms')) + ' ms, errors ' + str(m.get('error_rate_pct')) + '%') if m.get('status') == 'measured' and 'mean_ms' in m else (m.get('status') or 'not run')}"]
        for r in c.get("rows", []):
            lines.append(f"- {r['metric']}: predicted {r['predicted']} vs observed {r['observed']} ({r['error_pct']:+}%)")
        lines += [f"- {x}" for x in c.get("explanation", [])] + ([f"- not compared: {c['reason']}"] if c.get("reason") else [])
    lines += ["", "## Bottlenecks", ""] + [f"- [{b['label']}] {b.get('alternative', b.get('endpoint', ''))}: {b['detail']}" for b in s.bottlenecks]
    r = s.recommendation
    lines += ["", "## Recommendation", "", f"- {r.get('recommendation')} ({r.get('basis')}): {r.get('reason')}"]
    lines += [f"- next: {x}" for x in r.get("recommended_experiments", [])]
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in s.limitations]
    lines += ["- model assumptions: " + "; ".join((next(iter(s.predictions.values()), {}) or {}).get("assumptions", []))]
    return PlainTextResponse(redact("\n".join(lines)), media_type="text/markdown",
                             headers={"Content-Disposition": f'attachment; filename="reality-{sid}.md"'})


@reality_router.get("/api/reality/calibration")
def calibration(user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    return _sim().calibration()
