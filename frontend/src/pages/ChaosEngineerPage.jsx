import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { FaBomb, FaCheck, FaChevronDown, FaChevronRight, FaPlay, FaShieldAlt, FaStop, FaTimes } from 'react-icons/fa';
import {
  abortChaosAssessment, approveChaosAssessment, compareChaosAssessments, createChaosAssessment, createChaosPlan,
  getChaosAssessment, getChaosGate, listChaosAssessments, listChaosFindings, listChaosScenarios, runChaosPreflight,
} from '../services/chaos';
import { decidePlan, executePlan, listAutopilotProjects, listExecutions, listPlans } from '../services/evolutionAutopilot';

const TONE = {
  passed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  improved: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  verified: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  approved: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  done: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  confirmed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  failed: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  regressed: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  rejected: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  refused: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  critical: 'bg-rose-500/20 text-rose-200 border-rose-500/40',
  high: 'bg-orange-500/15 text-orange-200 border-orange-500/30',
  medium: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  low: 'bg-sky-500/10 text-sky-200 border-sky-500/25',
  probable: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  inconclusive: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  not_evaluated: 'bg-slate-700/50 text-slate-300 border-slate-600',
  not_measured: 'bg-slate-700/50 text-slate-300 border-slate-600',
  aborted: 'bg-slate-700/50 text-slate-300 border-slate-600',
  unconfirmed_hypothesis: 'bg-slate-700/50 text-slate-300 border-slate-600',
  awaiting_approval: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
  reproduced: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  static_suspicion: 'bg-slate-700/50 text-slate-300 border-slate-600',
  planned: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
};
const ACTIVE = new Set(['queued', 'preflight', 'running', 'recovering', 'evaluating']);
const label = (s) => String(s ?? '').replace(/_/g, ' ');
const Badge = ({ value }) => (
  <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${TONE[value] || (ACTIVE.has(value) ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30' : 'border-slate-700 bg-slate-800 text-slate-400')}`}>
    {ACTIVE.has(value) && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}{label(value)}
  </span>
);
function Card({ title, actions, children }) {
  return (
    <section className="rounded-2xl border border-border-dark bg-surface-card p-4">
      {(title || actions) && <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        {title && <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">{title}</h2>}{actions}</div>}
      {children}
    </section>
  );
}
const Btn = ({ tone = 'neutral', className = '', ...props }) => {
  const tones = { primary: 'bg-accent-blue text-white hover:bg-indigo-500', good: 'bg-emerald-600 text-white hover:bg-emerald-500',
    bad: 'bg-rose-600/90 text-white hover:bg-rose-500', neutral: 'border border-border-dark text-text-secondary hover:bg-surface-hover' };
  return <button {...props} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-40 ${tones[tone]} ${className}`} />;
};
const inputCls = 'rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-xs text-text-primary outline-none';
const Field = ({ name, children }) => <label className="flex flex-col gap-0.5 text-[10px] uppercase tracking-wide text-text-muted">{name}{children}</label>;
const Pre = ({ children }) => <pre className="max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-black/50 p-3 font-mono text-[11px] text-slate-300">{children}</pre>;

// --- setup ------------------------------------------------------------------------------------------------

function Setup({ projectId, scenarios, onCreated, onError, busy, setBusy }) {
  const [chosen, setChosen] = useState(['dependency_unavailable', 'dependency_slow', 'app_restart']);
  const [dep, setDep] = useState({ name: 'inventory', env_var: 'INVENTORY_URL', routes: '{"/stock": {"A1": 5}}' });
  const [useDep, setUseDep] = useState(true);
  const [limits, setLimits] = useState({ memory_mb: 512, cpus: 1, max_scenario_seconds: 120, max_burst_requests: 300, max_concurrency: 16, timeout_budget_ms: 3000, recovery_budget_s: 30 });
  const [endpoints, setEndpoints] = useState('');
  const [checks, setChecks] = useState(null);
  const [open, setOpen] = useState('');
  const config = () => {
    let routes = {};
    try { routes = JSON.parse(dep.routes || '{}'); } catch { throw new Error('Stub routes must be JSON, e.g. {"/stock": {"A1": 5}}'); }
    return {
      environment: 'sandbox', scenarios: chosen,
      dependencies: useDep ? [{ name: dep.name.trim(), env_var: dep.env_var.trim(), routes }] : [],
      endpoints: endpoints.split('\n').map((l) => l.trim()).filter(Boolean).map((l) => { const [m, ...r] = l.split(/\s+/); return r.length ? { method: m, path: r.join(' ') } : { method: 'GET', path: m }; }),
      limits: Object.fromEntries(Object.entries(limits).map(([k, v]) => [k, Number(v)])),
    };
  };
  const act = async (fn) => { setBusy(true); try { await fn(); } catch (e) { onError(e?.error || e?.message || 'Request failed.'); } finally { setBusy(false); } };
  const needsDep = chosen.some((id) => scenarios.find((s) => s.id === id)?.needs_dependency);
  return (
    <Card title="Assessment setup">
      <div className="space-y-3 text-xs text-text-secondary">
        <div className="flex flex-wrap items-center gap-3">
          <Field name="Environment"><select className={inputCls} value="sandbox" onChange={() => {}}>
            <option value="sandbox">Isolated sandbox (disposable Docker network, no external route)</option>
            <option value="production" disabled>Production — never targeted</option>
          </select></Field>
        </div>
        <div>
          <p className="mb-1 text-[10px] uppercase tracking-wide text-text-muted">Scenarios</p>
          <ul className="grid gap-1.5 md:grid-cols-2">{scenarios.map((s) => (
            <li key={s.id} className="rounded-lg border border-border-subtle bg-bg-base/40 px-3 py-2">
              <div className="flex items-start gap-2">
                <input type="checkbox" className="mt-0.5" checked={chosen.includes(s.id)} onChange={(e) => setChosen(e.target.checked ? [...chosen, s.id] : chosen.filter((x) => x !== s.id))} />
                <div className="min-w-0 flex-1">
                  <p className="text-text-primary">{s.title} {s.disruptive && <span className="text-[10px] text-amber-300">· disruptive</span>} {s.needs_dependency && <span className="text-[10px] text-text-muted">· needs a stub dependency</span>}</p>
                  <button className="text-[10px] text-text-muted underline" onClick={() => setOpen(open === s.id ? '' : s.id)}>{open === s.id ? 'hide' : 'procedure, safety, cleanup'}</button>
                  {open === s.id && <div className="mt-1 space-y-0.5 text-[11px]">
                    <p><span className="text-text-muted">Preconditions: </span>{s.preconditions.join('; ')}</p>
                    <p><span className="text-text-muted">Procedure: </span>{s.procedure.join(' → ')}</p>
                    <p><span className="text-text-muted">Max duration: </span>{s.max_seconds}s</p>
                    <p><span className="text-text-muted">Expected: </span>{s.expected.join('; ')}</p>
                    <p><span className="text-text-muted">Safety: </span>{s.safety.join('; ')}</p>
                    <p><span className="text-text-muted">Cleanup: </span>{s.cleanup.join('; ')}</p>
                  </div>}
                </div>
              </div>
            </li>
          ))}</ul>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex items-center gap-1.5 self-center"><input type="checkbox" checked={useDep} onChange={(e) => setUseDep(e.target.checked)} /> stub dependency</label>
          {useDep && <>
            <Field name="Name (host inside the sandbox)"><input className={`${inputCls} w-32`} value={dep.name} onChange={(e) => setDep({ ...dep, name: e.target.value })} /></Field>
            <Field name="App env var with its URL"><input className={`${inputCls} w-40 font-mono`} value={dep.env_var} onChange={(e) => setDep({ ...dep, env_var: e.target.value })} /></Field>
            <Field name="Stub routes (JSON: path → response)"><input className={`${inputCls} w-72 font-mono`} value={dep.routes} onChange={(e) => setDep({ ...dep, routes: e.target.value })} /></Field>
          </>}
          {needsDep && !useDep && <span className="text-amber-200">The selected dependency scenarios need a stub dependency.</span>}
        </div>
        <div className="flex flex-wrap items-end gap-2">
          {[['memory_mb', 'Memory MB'], ['cpus', 'CPUs'], ['max_scenario_seconds', 'Max s / scenario'], ['max_burst_requests', 'Burst requests'],
            ['max_concurrency', 'Concurrency'], ['timeout_budget_ms', 'Timeout budget ms'], ['recovery_budget_s', 'Recovery budget s']].map(([k, n]) => (
            <Field key={k} name={n}><input type="number" className={`${inputCls} w-24`} value={limits[k]} onChange={(e) => setLimits({ ...limits, [k]: e.target.value })} /></Field>
          ))}
          <Field name="Endpoints (optional, one per line)"><textarea rows={1} className={`${inputCls} w-56 font-mono`} value={endpoints} onChange={(e) => setEndpoints(e.target.value)} placeholder="default: from /openapi.json" /></Field>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Btn disabled={busy || !chosen.length} onClick={() => act(async () => setChecks(await runChaosPreflight(projectId, config())))}><FaShieldAlt className="h-2.5 w-2.5" /> Safety preflight</Btn>
          <Btn tone="primary" disabled={busy || !chosen.length} onClick={() => act(async () => onCreated((await createChaosAssessment(projectId, config())).assessment))}>Create assessment</Btn>
        </div>
        {checks && <ul className="space-y-0.5">{checks.checks.map((c) => <li key={c.check}>{c.passed ? <span className="text-emerald-300">✓</span> : <span className="text-rose-300">✗</span>} {c.check} <span className="text-text-muted">— {c.detail}</span></li>)}</ul>}
      </div>
    </Card>
  );
}

// --- report ------------------------------------------------------------------------------------------------

function ScenarioCard({ r }) {
  const [open, setOpen] = useState(r.status === 'failed');
  return (
    <li className="rounded-xl border border-border-subtle bg-bg-base/40">
      <button className="flex w-full items-center gap-2 px-3 py-2 text-left" onClick={() => setOpen((v) => !v)}>
        {open ? <FaChevronDown className="h-2.5 w-2.5 text-text-muted" /> : <FaChevronRight className="h-2.5 w-2.5 text-text-muted" />}
        <span className="text-xs text-text-primary">{label(r.scenario)}</span><Badge value={r.status} />
        <span className="text-[10px] text-text-muted">detect {r.detect_seconds ?? '—'} s · recover {r.recovery_seconds ?? '—'} s · affected: {r.affected_endpoints.join(', ') || 'none observed'}</span>
      </button>
      {open && (
        <div className="space-y-2 border-t border-border-subtle px-3 py-2 text-xs text-text-secondary">
          {r.error && <p className="text-amber-200">{r.error}</p>}
          <table className="w-full text-left text-[11px]"><tbody>{r.criteria.map((c) => (
            <tr key={c.id} className="border-t border-border-subtle align-top"><td className="py-1 pr-2"><Badge value={c.status} /></td><td className="pr-2 text-text-primary">{c.description}<p className="text-[10px] text-text-muted">{label(c.category)}</p></td><td className="break-words">{c.evidence}</td></tr>
          ))}</tbody></table>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-[11px]">
              <thead className="text-[10px] uppercase tracking-wide text-text-muted"><tr><th className="py-1 pr-2">Phase</th><th className="pr-2">t (s)</th><th>Per endpoint (success · median · max · codes)</th></tr></thead>
              <tbody>{r.observations.map((o, i) => (
                <tr key={i} className="border-t border-border-subtle align-top"><td className="py-1 pr-2 text-text-primary">{o.phase}</td><td className="pr-2">{o.seconds_from_start}</td>
                  <td>{Object.entries(o.per_endpoint).map(([ep, e]) => <p key={ep}><span className="font-mono">{ep}</span>: {e.success_rate}% · {e.p50_ms} ms · {e.max_ms} ms · {JSON.stringify(e.codes)}</p>)}
                    {o.notes.map((n, j) => <p key={j} className="text-text-muted">{n}</p>)}{o.leaks.map((l, j) => <p key={`l${j}`} className="text-rose-300">{l}</p>)}</td></tr>
              ))}</tbody>
            </table>
          </div>
          <details><summary className="cursor-pointer text-[11px] text-text-muted">Procedure (audit) and app log</summary><Pre>{r.procedure.join('\n')}</Pre><Pre>{r.app_logs_tail || 'no log output'}</Pre></details>
        </div>
      )}
    </li>
  );
}

function Report({ a }) {
  const s = a.score || {};
  return (
    <div className="space-y-4">
      <Card title="Resilience report" actions={<Badge value={a.status} />}>
        <div className="space-y-3 text-xs text-text-secondary">
          {a.error && <p className="text-amber-200">{a.error}</p>}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
            {[['Score', s.overall ?? '—'], ['Passed', s.scenarios_passed ?? 0], ['Failed', s.scenarios_failed ?? 0], ['Not evaluated', s.scenarios_not_evaluated ?? 0], ['Slowest recovery', s.max_recovery_seconds != null ? `${s.max_recovery_seconds} s` : '—']].map(([n, v]) => (
              <div key={n} className="rounded-xl bg-bg-base/60 px-3 py-2"><p className="text-[10px] uppercase tracking-wide text-text-muted">{n}</p><p className="mt-0.5 text-sm font-semibold text-text-primary">{v}</p></div>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">{Object.entries(s.categories || {}).map(([c, v]) => (
            <span key={c} className="rounded-lg border border-border-subtle px-2 py-1 text-[11px]">{label(c)}: <span className="text-text-primary">{v.score ?? 'not evaluated'}</span> <span className="text-text-muted">({v.passed}✓ {v.failed}✗ {v.not_evaluated}–)</span></span>
          ))}</div>
          <p className="text-[10px] text-text-muted">{s.method}</p>
          <ul className="space-y-1.5">{a.results.map((r) => <ScenarioCard key={r.scenario} r={r} />)}</ul>
        </div>
      </Card>
      {a.impact?.dependencies?.length > 0 && (
        <Card title="Dependency impact (Digital Twin vs observed)">
          {a.impact.dependencies.map((d) => (
            <div key={d.dependency} className="space-y-0.5 text-xs text-text-secondary">
              <p><span className="text-text-muted">Origin of '{d.dependency}' ({d.env_var}): </span><span className="font-mono">{d.origin_files.join(', ') || 'not found in the code'}</span></p>
              <p><span className="text-text-muted">Direct dependents: </span><span className="font-mono">{d.direct_dependents.join(', ') || 'none'}</span></p>
              <p><span className="text-text-muted">Potentially affected routes (graph): </span>{d.potentially_affected_routes.join(', ') || 'none'}</p>
              <p><span className="text-text-muted">Observed affected: </span><span className="text-text-primary">{d.observed_affected.join(', ') || 'none'}</span> · recovered: {d.recovered.join(', ') || 'none'} · remained unhealthy: {d.remained_unhealthy.join(', ') || 'none'}</p>
              <p className="text-[10px] text-text-muted">{d.note}</p>
            </div>
          ))}
        </Card>
      )}
      <Card title={`Audit log (${a.audit.length})`}><Pre>{a.audit.map((x) => `${x.at} ${x.action}${Object.entries(x).filter(([k]) => !['at', 'action'].includes(k)).map(([k, v]) => ` ${k}=${v}`).join('')}`).join('\n')}</Pre></Card>
    </div>
  );
}

// --- repair ---------------------------------------------------------------------------------------------------

function Repair({ projectId, findings, onChanged, onError }) {
  const [plans, setPlans] = useState([]);
  const [execs, setExecs] = useState([]);
  const [gates, setGates] = useState({});
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try {
      const [p, e] = await Promise.all([listPlans(projectId), listExecutions(projectId)]);
      const chaosPlans = (p.plans || []).filter((x) => x.origin === 'chaos');
      setPlans(chaosPlans);
      const ex = (e.executions || []).filter((x) => chaosPlans.some((pl) => pl.id === x.plan_id));
      setExecs(ex);
      const g = {};
      for (const x of ex.filter((y) => !ACTIVE.has(y.status))) {
        try { g[x.id] = (await getChaosGate(projectId, x.id)).gate; } catch { /* no gate ran (e.g. correctness rejected first) */ }
      }
      setGates(g);
    } catch (err) { onError(err?.error || 'Could not load repairs.'); }
  }, [projectId, onError]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!execs.some((x) => ACTIVE.has(x.status))) return undefined;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [execs, load]);
  const act = async (fn) => { setBusy(true); try { await fn(); await load(); onChanged(); } catch (e) { onError(e?.error || 'Request failed.'); } finally { setBusy(false); } };
  const reproduced = findings.filter((f) => f.kind === 'reproduced');
  const statics = findings.filter((f) => f.kind !== 'reproduced');
  return (
    <Card title="Findings and repairs">
      <div className="space-y-3 text-xs text-text-secondary">
        <ul className="space-y-1.5">{reproduced.map((f) => (
          <li key={f.id} className="rounded-xl border border-border-subtle bg-bg-base/40 px-3 py-2">
            <div className="flex flex-wrap items-center gap-1.5"><Badge value={f.severity} /><Badge value={f.kind} /><span className="text-[10px] uppercase text-text-muted">{label(f.category)} · root cause</span><Badge value={f.root_cause_level} />{f.status !== 'open' && <Badge value={f.status} />}</div>
            <p className="mt-1 text-text-primary">{f.component}: {f.expected}</p>
            <p><span className="text-text-muted">Observed: </span>{f.observed}</p>
            <p><span className="text-text-muted">Cause: </span>{f.root_cause}</p>
            <p><span className="text-text-muted">Reproduction: </span>{f.reproduction}</p>
            {f.status === 'open' && f.file && <Btn className="mt-1" tone="primary" disabled={busy} onClick={() => act(() => createChaosPlan(projectId, f.id))}>Propose repair</Btn>}
          </li>
        ))}</ul>
        {statics.length > 0 && <details><summary className="cursor-pointer text-[11px] text-text-muted">Static suspicions — not reproduced ({statics.length})</summary>
          <ul className="mt-1 space-y-0.5">{statics.map((f) => <li key={f.id}><span className="font-mono">{f.file}:{f.line}</span> {f.title} — {f.evidence}</li>)}</ul></details>}
        {plans.map((p) => {
          const ex = execs.filter((x) => x.plan_id === p.id).sort((a, b) => (b.started_at || '').localeCompare(a.started_at || ''))[0];
          const g = ex && gates[ex.id];
          return (
            <div key={p.id} className="rounded-xl border border-border-dark p-3">
              <div className="flex flex-wrap items-center gap-2"><span className="text-text-primary">{p.objective}</span><Badge value={p.status} />{ex && <><span>execution</span><Badge value={ex.status} /></>}</div>
              <p className="mt-1">{p.tasks[0]?.modification} <span className="text-text-muted">· files: {p.expected_files.join(', ')}</span></p>
              <div className="mt-2 flex flex-wrap gap-2">
                {p.status === 'awaiting_approval' && <><Btn tone="good" disabled={busy} onClick={() => act(() => decidePlan(projectId, p.id, 'approve'))}><FaCheck className="h-2.5 w-2.5" /> Approve</Btn>
                  <Btn tone="bad" disabled={busy} onClick={() => act(() => decidePlan(projectId, p.id, 'reject'))}><FaTimes className="h-2.5 w-2.5" /> Reject</Btn></>}
                {p.status === 'approved' && <Btn tone="primary" disabled={busy} onClick={() => act(() => executePlan(projectId, p.id, true))}><FaPlay className="h-2.5 w-2.5" /> Repair in an isolated copy and re-run the experiment</Btn>}
              </div>
              {ex && <div className="mt-2 space-y-0.5 text-[11px]">
                {ex.stages.map((s) => <p key={s.name}><Badge value={s.status} /> {s.name} <span className="text-text-muted">{(s.detail || '').slice(0, 220)}</span></p>)}
                {ex.error && <p className="text-amber-200">{ex.error}</p>}
                <p><span className="text-text-muted">Rollback: </span>{ex.applied_to_project ? 'not needed — applied after the correctness checks and the chaos gate passed' : ACTIVE.has(ex.status) ? 'in progress' : 'nothing applied; the isolated copy was discarded'}</p>
              </div>}
              {g && <div className="mt-2 text-[11px]">
                <p className="flex items-center gap-2"><span className="text-text-muted">Before/after experiment:</span><Badge value={g.decision} /></p>
                {g.reasons.map((r, i) => <p key={i}>• {r}</p>)}
                <div className="mt-1 grid gap-2 md:grid-cols-2">
                  {[['Original', g.results], ['Changed copy', g.candidate_results]].map(([n, rs]) => (
                    <div key={n}><p className="text-text-muted">{n}</p>{(rs || []).map((r) => r.criteria.map((c) => <p key={c.id}><Badge value={c.status} /> {c.id}: <span className="text-text-muted">{c.evidence.slice(0, 140)}</span></p>))}</div>
                  ))}
                </div>
              </div>}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// --- page ------------------------------------------------------------------------------------------------------

/**
 * AIForge Chaos Engineer: controlled failure experiments against a disposable copy of a project in an
 * isolated sandbox, an evidence-based resilience report, and verified repairs. Everything shown comes
 * from recorded experiments; criteria that could not be evaluated are shown as such.
 */
export default function ChaosEngineerPage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [scenarios, setScenarios] = useState([]);
  const [history, setHistory] = useState([]);
  const [selected, setSelected] = useState('');
  const [assessment, setAssessment] = useState(null);
  const [findings, setFindings] = useState([]);
  const [compareWith, setCompareWith] = useState('');
  const [comparison, setComparison] = useState(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const onError = useCallback((m) => setError(m), []);

  useEffect(() => {
    listChaosScenarios().then((r) => setScenarios(r.scenarios || [])).catch((e) => setError(e?.error || 'Could not load scenarios.'));
    listAutopilotProjects().then((r) => {
      setProjects(r.projects || []);
      const preferred = (r.projects || []).find((p) => p.project_id === activeProjectId);
      setProjectId((cur) => cur || preferred?.project_id || r.projects?.[0]?.project_id || '');
    }).catch((e) => setError(e?.error || 'Could not load projects.'));
  }, [activeProjectId]);

  const refresh = useCallback(async () => {
    if (!projectId) return;
    try {
      const [h, f] = await Promise.all([listChaosAssessments(projectId), listChaosFindings(projectId)]);
      setHistory(h.assessments || []); setFindings(f.items || []);
      setSelected((cur) => cur || h.assessments?.[0]?.id || '');
    } catch (e) { setError(e?.error || 'Could not load chaos data.'); }
  }, [projectId]);
  useEffect(() => { setHistory([]); setSelected(''); setAssessment(null); setFindings([]); setComparison(null); setError(''); refresh(); }, [projectId, refresh]);
  const loadAssessment = useCallback(async () => {
    if (!selected) { setAssessment(null); return; }
    try { setAssessment((await getChaosAssessment(projectId, selected)).assessment); } catch (e) { setError(e?.error || 'Could not load the assessment.'); }
  }, [projectId, selected]);
  useEffect(() => { setConsent(false); loadAssessment(); }, [loadAssessment]);
  useEffect(() => {
    if (!assessment || !ACTIVE.has(assessment.status)) return undefined;
    const t = setInterval(async () => { await loadAssessment(); }, 2500);
    return () => clearInterval(t);
  }, [assessment, loadAssessment]);
  useEffect(() => { if (assessment && !ACTIVE.has(assessment.status)) refresh(); }, [assessment?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (fn) => { setBusy(true); setError(''); try { await fn(); } catch (e) { setError(e?.error || 'Request failed.'); } finally { setBusy(false); } };
  const disruptive = useMemo(() => (assessment?.config?.scenarios || []).filter((id) => scenarios.find((s) => s.id === id)?.disruptive), [assessment, scenarios]);
  const live = assessment && ACTIVE.has(assessment.status);

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaBomb className="h-4 w-4" /> Chaos Engineer</h1>
          <p className="text-xs text-text-muted">Controlled failures against a disposable copy of the app in an isolated sandbox; evidence-based resilience and verified repairs.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {projectId && (<>
        <Setup projectId={projectId} scenarios={scenarios} busy={busy} setBusy={setBusy} onError={onError}
               onCreated={(a) => { setSelected(a.id); setAssessment(a); refresh(); }} />

        {assessment && (
          <Card title="Experiment" actions={<Badge value={assessment.status} />}>
            <div className="space-y-2 text-xs text-text-secondary">
              <p>{assessment.config.scenarios.map(label).join(', ')} · created {new Date(assessment.created_at).toLocaleString()}{assessment.approved_by ? ` · approved by ${assessment.approved_by}` : ''}</p>
              <ul className="space-y-0.5">{assessment.preflight.map((c) => <li key={c.check}>{c.passed ? <span className="text-emerald-300">✓</span> : <span className="text-rose-300">✗</span>} {c.check} <span className="text-text-muted">— {c.detail}</span></li>)}</ul>
              {assessment.status === 'awaiting_approval' && (
                <div className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2">
                  <label className="flex items-center gap-1.5 text-amber-100"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                    I approve running {disruptive.length ? `the disruptive scenarios (${disruptive.map(label).join(', ')})` : 'these scenarios'} against a disposable copy in the isolated sandbox</label>
                  <Btn tone="good" disabled={busy || !consent} onClick={() => act(async () => setAssessment((await approveChaosAssessment(projectId, assessment.id)).assessment))}><FaPlay className="h-2.5 w-2.5" /> Approve and run</Btn>
                  <Btn disabled={busy} onClick={() => act(async () => { await abortChaosAssessment(projectId, assessment.id); await loadAssessment(); })}>Cancel</Btn>
                </div>
              )}
              {live && (
                <div className="flex flex-wrap items-center gap-2">
                  <span>Running: <span className="text-text-primary">{label(assessment.current) || 'setting up'}</span></span>
                  <Btn tone="bad" disabled={busy || assessment.abort_requested} onClick={() => act(async () => { await abortChaosAssessment(projectId, assessment.id); await loadAssessment(); })}><FaStop className="h-2.5 w-2.5" /> {assessment.abort_requested ? 'Aborting…' : 'Abort'}</Btn>
                </div>
              )}
              {live && <Pre>{assessment.audit.slice(-12).map((x) => `${x.at.slice(11, 19)} ${x.action}`).join('\n')}</Pre>}
            </div>
          </Card>
        )}
        {assessment && !live && assessment.results.length > 0 && <Report a={assessment} />}
        {findings.length > 0 && <Repair projectId={projectId} findings={findings} onChanged={refresh} onError={onError} />}

        {history.length > 0 && (
          <Card title="Experiment history">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-[11px] text-text-secondary">
                <thead className="text-[10px] uppercase tracking-wide text-text-muted"><tr><th className="py-1 pr-2">When</th><th className="pr-2">Status</th><th className="pr-2">Score</th><th className="pr-2">Failed</th><th className="pr-2">Passed</th><th className="pr-2">Not evaluated</th><th /></tr></thead>
                <tbody>{history.map((h) => (
                  <tr key={h.id} className={`border-t border-border-subtle ${h.id === selected ? 'bg-accent-blue/5' : ''}`}>
                    <td className="py-1 pr-2">{new Date(h.created_at).toLocaleString()}</td><td className="pr-2"><Badge value={h.status} /></td><td className="pr-2 text-text-primary">{h.score ?? '—'}</td>
                    <td className="pr-2">{h.failed.map(label).join(', ') || '—'}</td><td className="pr-2">{h.passed.map(label).join(', ') || '—'}</td><td className="pr-2">{h.not_evaluated.map(label).join(', ') || '—'}</td>
                    <td className="space-x-1"><Btn onClick={() => setSelected(h.id)}>Open</Btn>{selected && h.id !== selected && <Btn onClick={() => { setCompareWith(h.id); act(async () => setComparison(await compareChaosAssessments(projectId, h.id, selected))); }}>Compare</Btn>}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            {comparison && compareWith && (
              <div className="mt-3 text-[11px] text-text-secondary">
                <p className="mb-1">Score {comparison.first.score ?? '—'} → {comparison.second.score ?? '—'}</p>
                {comparison.scenarios.map((r) => <p key={r.scenario}>{label(r.scenario)}: <Badge value={r.first} /> → <Badge value={r.second} /> · recovery {r.first_recovery_s ?? '—'}s → {r.second_recovery_s ?? '—'}s{r.changed.length ? ` · changed: ${r.changed.join(', ')}` : ''}</p>)}
              </div>
            )}
          </Card>
        )}
      </>)}
    </div>
  );
}
