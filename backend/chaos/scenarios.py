"""
Failure scenarios. Each one is a fixed procedure on the experiment's own sandbox:

  baseline  -> inject the failure -> observe -> restore -> wait for recovery -> verify

and a set of pass/fail criteria evaluated only from what the probe recorded. A criterion that
cannot be evaluated (no baseline, the step could not run) is "not_evaluated", never "passed".
"""

import re
import time
from dataclasses import dataclass, field
from statistics import median
from typing import Callable, Dict, List, Optional

from backend.chaos.models import Criterion, Observation, ScenarioResult, Target
from backend.chaos.sandbox import Sandbox
from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact

CONTROLLED = {502, 503, 504}           # a deliberate "dependency unavailable" answer
_TRACE = re.compile(r"Traceback \(most recent call last\)|File \"/[^\"]+\", line \d+|\w+Error: .*\n?\s*at |"
                    r"sqlalchemy\.exc\.|psycopg2\.|urllib\.error\.|ConnectionRefusedError")


class Aborted(Exception):
    pass


@dataclass
class Scenario:
    id: str
    title: str
    category: str                      # dependency | application | resource
    needs_dependency: bool
    disruptive: bool
    preconditions: List[str]
    procedure: List[str]
    max_seconds: int
    expected: List[str]
    safety: List[str]
    cleanup: List[str]
    verification: List[str]
    run: Callable = field(repr=False, default=None)


# --- observation helpers ----------------------------------------------------------------------------

def leaks_in(body: str) -> List[str]:
    """Internals in an error body: stack traces, file paths, exception text, secrets."""
    found = []
    if body and _TRACE.search(body):
        found.append("stack trace or internal exception text in the response")
    if body and redact(body) != body:
        found.append("a secret-like value in the response")
    return found


def observe(sb: Sandbox, eps: List[Target], phase: str, count: int, timeout: float, t0: float) -> Observation:
    results = sb.probe(eps, count, 1, timeout)
    per: Dict[str, Dict] = {}
    leaks: List[str] = []
    for r in results:
        e = per.setdefault(r["ep"], {"ok": 0, "total": 0, "ms": [], "codes": {}})
        e["total"] += 1
        code = r.get("status")
        key = str(code) if code is not None else (r.get("error") or "error").split(":")[0]
        e["codes"][key] = e["codes"].get(key, 0) + 1
        e["ms"].append(r["ms"])
        if code is not None and code < 400:
            e["ok"] += 1
        if code is not None and code >= 400:
            leaks += [f"{r['ep']}: {x}" for x in leaks_in(r.get("body", ""))]
    for ep, e in per.items():
        ms = e.pop("ms")
        e["success_rate"] = round(e["ok"] / e["total"] * 100, 1) if e["total"] else 0.0
        e["p50_ms"] = round(median(ms), 1) if ms else None
        e["max_ms"] = round(max(ms), 1) if ms else None
    return Observation(phase=phase, seconds_from_start=round(time.monotonic() - t0, 2), per_endpoint=per,
                       leaks=sorted(set(leaks)))


def degraded(obs: Observation, base: Observation) -> List[str]:
    return [ep for ep, e in obs.per_endpoint.items()
            if ep in base.per_endpoint and e["success_rate"] < base.per_endpoint[ep]["success_rate"]]


def recovered(obs: Observation, base: Observation) -> bool:
    return all(obs.per_endpoint.get(ep, {}).get("success_rate", 0) >= e["success_rate"]
               for ep, e in base.per_endpoint.items())


def _crit(cid, category, description, ok: Optional[bool], evidence) -> Criterion:
    return Criterion(id=cid, category=category, description=description,
                     status="not_evaluated" if ok is None else "passed" if ok else "failed", evidence=evidence)


# --- the shared procedure for dependency failures ----------------------------------------------------------

def _dependency_failure(sb: Sandbox, ctx, result: ScenarioResult, inject, restore, failure_note: str,
                        probe_timeout: float) -> None:
    eps, health, limits, step, stop = ctx["endpoints"], ctx["health"], ctx["limits"], ctx["step"], ctx["stop"]
    t0 = time.monotonic()
    base = observe(sb, eps, "baseline", 3, 10.0, t0)
    result.observations.append(base)
    step("baseline: every endpoint probed 3 times")
    if not any(e["success_rate"] == 100 for e in base.per_endpoint.values()):
        result.status = "inconclusive"
        result.error = "the app was not healthy before the failure was injected, so its effect cannot be judged"
        return
    stop()
    inject()
    t_inject = time.monotonic()
    step(failure_note)
    # time to detect: first probe round in which an endpoint answers worse than at baseline
    detect_deadline = t_inject + min(30, limits.max_scenario_seconds / 3)
    while time.monotonic() < detect_deadline:
        stop()
        probe_round = observe(sb, eps, "detect", 1, probe_timeout, t0)
        too_slow = any((e["max_ms"] or 0) > limits.timeout_budget_ms for e in probe_round.per_endpoint.values())
        if degraded(probe_round, base) or too_slow:
            result.detect_seconds = round(time.monotonic() - t_inject, 2)
            break
        time.sleep(0.5)
    failure = observe(sb, eps, "failure", 3, probe_timeout, t0)
    failure.health = _health_text(failure, health)
    failure.notes.append(f"app container: {sb.app_state()}")
    result.observations.append(failure)
    step("failure: every endpoint probed 3 times while the failure was active")
    stop()
    restore()
    t_restore = time.monotonic()
    step("restored the dependency")
    while time.monotonic() - t_restore < limits.recovery_budget_s:
        stop()
        probe_round = observe(sb, eps, "recovering", 1, 10.0, t0)
        if recovered(probe_round, base):
            result.recovery_seconds = round(time.monotonic() - t_restore, 2)
            break
        time.sleep(0.5)
    after = observe(sb, eps, "recovery", 3, 10.0, t0)
    result.observations.append(after)
    step("recovery: every endpoint probed 3 times after the restore")
    result.affected_endpoints = degraded(failure, base)
    slow = [ep for ep, e in failure.per_endpoint.items() if (e["max_ms"] or 0) > limits.timeout_budget_ms]
    result.affected_endpoints = sorted(set(result.affected_endpoints) | set(slow))
    result.unaffected_endpoints = sorted(set(base.per_endpoint) - set(result.affected_endpoints))
    _dependency_criteria(result, base, failure, after, health, limits)


def _health_text(obs: Observation, health: Target) -> Optional[str]:
    e = obs.per_endpoint.get(f"{health.method} {health.path}")
    return None if e is None else f"{health.path}: {e['success_rate']}% success, max {e['max_ms']} ms"


def _dependency_criteria(result: ScenarioResult, base, failure, after, health: Target, limits) -> None:
    hkey = f"{health.method} {health.path}"
    h = failure.per_endpoint.get(hkey)
    affected = [ep for ep in result.affected_endpoints if ep != hkey]
    state_note = next((n for n in failure.notes if n.startswith("app container")), "")
    running = "'running': True" in state_note
    result.criteria.append(_crit(
        "containment", "containment", "The app process and its health endpoint stay up; unrelated endpoints keep working",
        None if h is None else (h["success_rate"] == 100 and running and
                                all(failure.per_endpoint[ep]["success_rate"] == base.per_endpoint[ep]["success_rate"]
                                    for ep in result.unaffected_endpoints if ep in failure.per_endpoint)),
        f"health during failure: {h and h['success_rate']}% success; {state_note}; affected: {affected or 'none'}; "
        f"unaffected: {result.unaffected_endpoints}"))
    slow = {ep: failure.per_endpoint[ep]["max_ms"] for ep in failure.per_endpoint
            if (failure.per_endpoint[ep]["max_ms"] or 0) > limits.timeout_budget_ms}
    result.criteria.append(_crit(
        "fails_fast", "timeout", f"Every request answers within the {limits.timeout_budget_ms} ms budget while the dependency fails",
        not slow, f"slowest answers during failure: {slow}" if slow else
        f"all answers under {limits.timeout_budget_ms} ms (max {max((e['max_ms'] or 0) for e in failure.per_endpoint.values())} ms)"))
    uncontrolled = {ep: failure.per_endpoint[ep]["codes"] for ep in affected
                    if any(c not in {str(x) for x in CONTROLLED} and not c.startswith("2")
                           for c in failure.per_endpoint[ep]["codes"])}
    result.criteria.append(_crit(
        "controlled_errors", "error_handling",
        "Affected endpoints answer with a degraded success (2xx) or a deliberate 502/503/504 - not 500s, resets or hangs",
        None if not affected else not uncontrolled,
        f"status codes during failure: {uncontrolled}" if uncontrolled else
        ("no endpoint was affected" if not affected else
         f"affected endpoints answered {[failure.per_endpoint[ep]['codes'] for ep in affected]}")))
    result.criteria.append(_crit(
        "no_internal_details", "error_handling", "Error responses do not expose stack traces, internal exceptions or secrets",
        not failure.leaks, "; ".join(failure.leaks) if failure.leaks else "no internals found in error bodies"))
    degraded_ok = [ep for ep in affected if any(c.startswith("2") for c in failure.per_endpoint[ep]["codes"])]
    result.criteria.append(_crit(
        "graceful_degradation", "degradation",
        "Endpoints that use the dependency still serve what they can (2xx with partial data) while it fails",
        None if not affected else len(degraded_ok) == len(affected),
        "no endpoint was affected" if not affected else
        f"degraded successfully: {degraded_ok or 'none'}; failed outright: {sorted(set(affected) - set(degraded_ok))}"))
    result.criteria.append(_crit(
        "recovers", "recovery", f"Every endpoint answers as at baseline within {limits.recovery_budget_s}s of the restore",
        result.recovery_seconds is not None,
        f"recovered after {result.recovery_seconds}s" if result.recovery_seconds is not None
        else f"not recovered within {limits.recovery_budget_s}s"))
    result.criteria.append(_crit(
        "post_recovery_correct", "post_recovery", "After recovery, success rates match the baseline",
        recovered(after, base), f"after recovery: { {ep: e['success_rate'] for ep, e in after.per_endpoint.items()} }"))


# --- scenario implementations -------------------------------------------------------------------------------

def run_dependency_unavailable(sb: Sandbox, ctx, result: ScenarioResult) -> None:
    dep = ctx["dependency"]
    _dependency_failure(sb, ctx, result, lambda: sb.stop_dependency(dep), lambda: sb.start_dependency(dep),
                        f"stopped the stub dependency '{dep}' (connections refused / name not resolvable)", 15.0)


def run_dependency_errors(sb: Sandbox, ctx, result: ScenarioResult) -> None:
    dep = ctx["dependency"]
    _dependency_failure(sb, ctx, result, lambda: sb.control(dep, "error"), lambda: sb.control(dep, "ok"),
                        f"switched '{dep}' to answer every request with HTTP 500", 15.0)


def run_dependency_slow(sb: Sandbox, ctx, result: ScenarioResult) -> None:
    dep, limits = ctx["dependency"], ctx["limits"]
    delay = min(20_000, limits.timeout_budget_ms * 2)
    _dependency_failure(sb, ctx, result, lambda: sb.control(dep, "slow", delay), lambda: sb.control(dep, "ok"),
                        f"switched '{dep}' to delay every answer by {delay} ms", delay / 1000 + 10)


def run_malformed_response(sb: Sandbox, ctx, result: ScenarioResult) -> None:
    dep = ctx["dependency"]
    _dependency_failure(sb, ctx, result, lambda: sb.control(dep, "malformed"), lambda: sb.control(dep, "ok"),
                        f"switched '{dep}' to answer with invalid JSON", 15.0)


def run_app_restart(sb: Sandbox, ctx, result: ScenarioResult) -> None:
    eps, health, limits, step, stop = ctx["endpoints"], ctx["health"], ctx["limits"], ctx["step"], ctx["stop"]
    t0 = time.monotonic()
    base = observe(sb, eps, "baseline", 3, 10.0, t0)
    result.observations.append(base)
    step("baseline: every endpoint probed 3 times")
    if not any(e["success_rate"] == 100 for e in base.per_endpoint.values()):
        result.status, result.error = "inconclusive", "the app was not healthy before the restart"
        return
    stop()
    sb.restart_app()
    t_restart = time.monotonic()
    step("restarted the app container (docker restart, 2 s grace period)")
    result.recovery_seconds = sb.wait_healthy(health, limits.recovery_budget_s)
    step(f"health check answered after {result.recovery_seconds}s" if result.recovery_seconds is not None
         else f"health check did not answer within {limits.recovery_budget_s}s")
    after = observe(sb, eps, "recovery", 3, 10.0, t0)
    after.notes.append(f"app container: {sb.app_state()}; restart issued {round(t_restart - t0, 2)}s into the scenario")
    result.observations.append(after)
    result.criteria.append(_crit("recovers", "recovery", f"The app answers its health check within {limits.recovery_budget_s}s of a restart",
                                 result.recovery_seconds is not None,
                                 f"healthy after {result.recovery_seconds}s" if result.recovery_seconds is not None
                                 else "never became healthy within the budget"))
    result.criteria.append(_crit("post_recovery_correct", "post_recovery", "After the restart, success rates match the baseline",
                                 recovered(after, base),
                                 f"after restart: { {ep: e['success_rate'] for ep, e in after.per_endpoint.items()} }"))
    result.criteria.append(_crit("data_integrity", "data_integrity", "Data written before the restart is still there after it",
                                 None, "not evaluated: no write/read endpoint pair was configured for this project"))


def run_request_burst(sb: Sandbox, ctx, result: ScenarioResult) -> None:
    eps, health, limits, step, stop = ctx["endpoints"], ctx["health"], ctx["limits"], ctx["step"], ctx["stop"]
    t0 = time.monotonic()
    base = observe(sb, eps, "baseline", 3, 10.0, t0)
    result.observations.append(base)
    step("baseline: every endpoint probed 3 times")
    stop()
    per_ep = max(1, limits.max_burst_requests // max(1, len(eps)))
    raw = sb.probe(eps, per_ep, limits.max_concurrency, limits.timeout_budget_ms / 1000 * 3)
    step(f"burst: {per_ep * len(eps)} requests with {limits.max_concurrency} concurrent connections")
    burst = Observation(phase="burst", seconds_from_start=round(time.monotonic() - t0, 2))
    codes: Dict[str, int] = {}
    for r in raw:
        k = str(r.get("status")) if r.get("status") is not None else (r.get("error") or "error").split(":")[0]
        codes[k] = codes.get(k, 0) + 1
    total = len(raw)
    bad = sum(v for k, v in codes.items() if not k.startswith("2") and k not in ("429", "503"))
    ms = sorted(r["ms"] for r in raw)
    cpu, mem = sb.app_stats()
    state = sb.app_state()
    burst.notes += [f"status codes: {codes}", f"p95 {ms[int(len(ms) * 0.95) - 1] if ms else None} ms",
                    f"app after burst: cpu {cpu}%, memory {mem} MB, {state}"]
    result.observations.append(burst)
    stop()
    result.recovery_seconds = sb.wait_healthy(health, limits.recovery_budget_s)
    after = observe(sb, eps, "recovery", 3, 10.0, t0)
    result.observations.append(after)
    result.criteria.append(_crit("survives_burst", "containment", "The app process survives the burst (not killed, not out of memory)",
                                 bool(state.get("running")) and not state.get("oom_killed"), f"container state: {state}"))
    result.criteria.append(_crit("burst_errors", "error_handling",
                                 "Under the burst, at most 1% of requests fail other than with a deliberate 429/503",
                                 (bad / total * 100 <= 1.0) if total else None,
                                 f"{bad} of {total} requests failed uncontrolled; codes {codes}"))
    result.criteria.append(_crit("recovers", "recovery", f"Healthy again within {limits.recovery_budget_s}s after the burst",
                                 result.recovery_seconds is not None, f"healthy after {result.recovery_seconds}s"))
    result.criteria.append(_crit("post_recovery_correct", "post_recovery", "After the burst, success rates match the baseline",
                                 recovered(after, base), f"after: { {ep: e['success_rate'] for ep, e in after.per_endpoint.items()} }"))


_COMMON_SAFETY = ["runs only inside a Docker network created for this experiment, with no route to the host or "
                  "internet", "only this experiment's own containers are stopped, restarted or reconfigured",
                  "the app runs non-root with all capabilities dropped and CPU/memory/process limits"]
_COMMON_CLEANUP = ["the dependency is restored and the app checked", "all containers, the network and the volume "
                   "of the experiment are removed, also after errors or an abort"]

SCENARIOS: Dict[str, Scenario] = {s.id: s for s in [
    Scenario("dependency_unavailable", "Dependency unavailable", "dependency", True, True,
             ["a stub dependency is configured and the app reads its URL from the given env var",
              "the app answers its endpoints at baseline"],
             ["probe baseline", "stop the stub dependency container", "probe until an endpoint degrades (time to detect)",
              "probe the failure state", "start the dependency", "probe until baseline is restored (time to recover)",
              "probe the recovered state"], 120,
             ["the health endpoint and unrelated endpoints keep working", "dependent endpoints fail fast with a "
              "controlled error or degraded data", "no internals in error responses", "full recovery after the restore"],
             _COMMON_SAFETY, _COMMON_CLEANUP, ["baseline, failure and recovery probes", "container state"],
             run_dependency_unavailable),
    Scenario("dependency_errors", "Dependency returns errors", "dependency", True, True,
             ["a stub dependency is configured"], ["probe baseline", "switch the stub to HTTP 500", "probe failure",
                                                   "switch back", "verify recovery"], 120,
             ["controlled errors or degraded data", "no internals exposed", "recovery"], _COMMON_SAFETY,
             _COMMON_CLEANUP, ["probes before, during and after"], run_dependency_errors),
    Scenario("dependency_slow", "Dependency is slow (timeout behaviour)", "dependency", True, True,
             ["a stub dependency is configured"],
             ["probe baseline", "delay every stub answer by 2x the timeout budget", "probe failure", "remove the delay",
              "verify recovery"], 150,
             ["requests answer within the timeout budget (the app has its own timeout)", "recovery"], _COMMON_SAFETY,
             _COMMON_CLEANUP, ["per-request latency during the delay"], run_dependency_slow),
    Scenario("malformed_response", "Dependency returns malformed data", "application", True, True,
             ["a stub dependency is configured"], ["probe baseline", "make the stub answer invalid JSON", "probe failure",
                                                   "restore", "verify recovery"], 120,
             ["a controlled error or degraded data instead of a 500", "no internals exposed"], _COMMON_SAFETY,
             _COMMON_CLEANUP, ["status codes and bodies during the failure"], run_malformed_response),
    Scenario("app_restart", "Application container restart", "application", False, True,
             ["the app answers its health endpoint"], ["probe baseline", "docker restart the app container",
                                                        "wait for the health check (time to recover)", "probe again"], 90,
             ["healthy again within the recovery budget", "same answers as before the restart"], _COMMON_SAFETY,
             _COMMON_CLEANUP, ["time to healthy", "post-restart probes"], run_app_restart),
    Scenario("request_burst", "Bounded request burst", "resource", False, False,
             ["the app answers its endpoints at baseline"],
             ["probe baseline", "send a bounded burst (max requests x max concurrency from the limits)",
              "record codes, latency, container CPU/memory/state", "wait for health", "probe again"], 120,
             ["the process survives (no OOM kill)", "at most 1% uncontrolled errors", "recovery"],
             _COMMON_SAFETY + ["the burst size and concurrency are capped by the limits (at most 1000 x 32)"],
             _COMMON_CLEANUP, ["codes, p95, container state and resources"], run_request_burst),
]}
NEEDS_DEPENDENCY = [s.id for s in SCENARIOS.values() if s.needs_dependency]


def describe(s: Scenario) -> Dict:
    return {k: v for k, v in s.__dict__.items() if k != "run"}


def run_scenario(sb: Sandbox, scenario_id: str, ctx) -> ScenarioResult:
    s = SCENARIOS[scenario_id]
    result = ScenarioResult(scenario=scenario_id, status="running", started_at=now_iso())

    def step(text):
        result.procedure.append(f"{now_iso()} {text}")
        ctx["on_step"](scenario_id, text)
    budget = min(s.max_seconds, ctx["limits"].max_scenario_seconds)
    deadline = time.monotonic() + budget

    def stop():
        if ctx["should_stop"]():
            raise Aborted("abort requested")
        if time.monotonic() > deadline:
            raise TimeoutError(f"exceeded its {budget}s limit")
    try:
        s.run(sb, {**ctx, "step": step, "stop": stop}, result)
    except TimeoutError as e:
        result.status, result.error = "inconclusive", f"stopped at the scenario's time limit: {e}"
    finally:
        result.app_logs_tail = sb.app_logs(60)
        result.finished_at = now_iso()
    if result.status == "running":
        statuses = {c.status for c in result.criteria}
        result.status = "failed" if "failed" in statuses else "passed" if "passed" in statuses else "not_evaluated"
    return result
