import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { FaCheck, FaChevronDown, FaChevronRight, FaPlay, FaStop, FaSync, FaTimes, FaTachometerAlt } from 'react-icons/fa';
import {
  cancelPerfRun, createPerfPlan, getLatestPerfAnalysis, getPerfReport, listPerfFindings, listPerfPlans, listPerfRuns,
  startPerfAnalysis,
} from '../services/performanceEngineer';
import { cancelExecution, decidePlan, executePlan, listAutopilotProjects } from '../services/evolutionAutopilot';

const TONE = {
  completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  measured: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  improved: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  verified: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  approved: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  done: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  passed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  faster: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  regressed: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  rejected: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  failed: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  slower: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  high: 'bg-rose-500/15 text-rose-200 border-rose-500/30',
  inconclusive: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  not_measured: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  unavailable: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  not_improved: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  no_clear_change: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  awaiting_approval: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  medium: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  blocked: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  cancelled: 'bg-slate-700/50 text-slate-300 border-slate-600',
  running: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  queued: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  planned: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
  low: 'bg-sky-500/10 text-sky-200 border-sky-500/25',
};
const ACTIVE = new Set(['queued', 'running']);
const label = (s) => String(s ?? '').replace(/_/g, ' ');
const ms = (v) => (v == null ? '—' : `${v} ms`);
const num = (v, unit = '') => (v == null ? '—' : `${v}${unit}`);

const Badge = ({ value, tone }) => (
  <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${tone || TONE[value] || 'border-slate-700 bg-slate-800 text-slate-400'}`}>
    {ACTIVE.has(value) && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
    {label(value)}
  </span>
);

function Card({ title, actions, children }) {
  return (
    <section className="rounded-2xl border border-border-dark bg-surface-card p-4">
      {(title || actions) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          {title && <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">{title}</h2>}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

const Btn = ({ tone = 'neutral', className = '', ...props }) => {
  const tones = {
    primary: 'bg-accent-blue text-white hover:bg-indigo-500',
    good: 'bg-emerald-600 text-white hover:bg-emerald-500',
    bad: 'bg-rose-600/90 text-white hover:bg-rose-500',
    neutral: 'border border-border-dark text-text-secondary hover:bg-surface-hover',
  };
  return <button {...props} className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-40 ${tones[tone]} ${className}`} />;
};

const Field = ({ name, children }) => (
  <label className="flex flex-col gap-0.5 text-[10px] uppercase tracking-wide text-text-muted">{name}{children}</label>
);
const inputCls = 'rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-xs normal-case tracking-normal text-text-primary outline-none';
const Pre = ({ children }) => <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-black/50 p-3 font-mono text-[11px] text-slate-300">{children}</pre>;

// --- measurements -------------------------------------------------------------------------------------

function EndpointTable({ endpoints }) {
  if (!endpoints?.length) return <p className="text-xs text-text-muted">No endpoint measurements.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left text-[11px]">
        <thead className="text-[10px] uppercase tracking-wide text-text-muted">
          <tr><th className="py-1 pr-2">Endpoint</th><th className="pr-2">Requests</th><th className="pr-2">Median</th><th className="pr-2">p95</th><th className="pr-2">p99</th><th className="pr-2">Req/s</th><th className="pr-2">Errors</th><th>Run-to-run spread</th></tr>
        </thead>
        <tbody>{endpoints.map((e) => (
          <tr key={`${e.method} ${e.path}`} className="border-t border-border-subtle text-text-secondary">
            <td className="py-1 pr-2 font-mono text-text-primary">{e.method} {e.path}</td><td className="pr-2">{e.requests}</td>
            <td className="pr-2">{ms(e.median_ms)}</td><td className="pr-2">{ms(e.p95_ms)}</td><td className="pr-2">{ms(e.p99_ms)}</td>
            <td className="pr-2">{num(e.throughput_rps)}</td><td className="pr-2">{e.errors} ({e.error_rate_pct}%)</td>
            <td title={`per-repetition medians: ${e.rep_medians_ms.join(', ')} ms`}>{num(e.spread_pct, '%')}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function EnvironmentInfo({ env, m }) {
  if (!env) return null;
  return (
    <div className="grid gap-2 text-[11px] text-text-secondary md:grid-cols-2">
      <div>
        <p><span className="text-text-muted">Method: </span>{env.method}</p>
        <p><span className="text-text-muted">Image / limits: </span>{env.image} · {Object.entries(env.limits || {}).map(([k, v]) => `${k} ${v}`).join(', ')}</p>
        <p><span className="text-text-muted">Load: </span>{env.load_generator}</p>
        <p><span className="text-text-muted">Host: </span>{env.host?.platform} · {env.host?.cpu_count} CPUs</p>
      </div>
      <div>
        {(env.notes || []).map((n, i) => <p key={i}>• {n}</p>)}
        <p className="text-text-muted">• {env.profiling}</p>
        {m && <p>• startup {num(m.startup_seconds, ' s')} (container start → {m.readiness_probe || 'no readiness answer'}; dependency install excluded)</p>}
        {m?.resources && <p>• CPU avg {num(m.resources.cpu_avg_pct, '%')} / max {num(m.resources.cpu_max_pct, '%')}, memory avg {num(m.resources.mem_avg_mb, ' MB')} / max {num(m.resources.mem_max_mb, ' MB')} ({m.resources.samples} samples)</p>}
      </div>
    </div>
  );
}

// --- findings ---------------------------------------------------------------------------------------------

function FindingRow({ f, all, onPlan, busy }) {
  const [open, setOpen] = useState(false);
  const linked = (f.linked || []).map((id) => all.find((x) => x.id === id)).filter(Boolean);
  const plannable = f.status === 'open' && f.file && f.file.endsWith('.py');
  return (
    <li className="rounded-xl border border-border-subtle bg-bg-base/40">
      <div className="flex items-start gap-2 px-3 py-2">
        <button onClick={() => setOpen((v) => !v)} className="mt-1 text-text-muted hover:text-text-primary">
          {open ? <FaChevronDown className="h-2.5 w-2.5" /> : <FaChevronRight className="h-2.5 w-2.5" />}
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge value={f.severity} /><span className="text-[10px] uppercase tracking-wide text-text-muted">{label(f.evidence_kind)} · {label(f.category)} · confidence {f.confidence}</span>
            {f.status !== 'open' && <Badge value={f.status} />}
          </div>
          <p className="mt-1 text-xs text-text-primary">{f.title}</p>
          <p className="font-mono text-[10px] text-text-muted">{f.file}{f.line ? `:${f.line}` : ''}{f.endpoint ? ` · ${f.endpoint}` : ''}</p>
        </div>
        {plannable && <Btn tone="primary" disabled={busy} onClick={() => onPlan(f)}>Plan optimization</Btn>}
      </div>
      {open && (
        <div className="space-y-1.5 border-t border-border-subtle px-3 py-2 text-xs text-text-secondary">
          <Pre>{f.evidence}</Pre>
          <p><span className="text-text-muted">Detected by: </span>{f.detection}</p>
          <p><span className="text-text-muted">Potential impact: </span>{f.impact}</p>
          <p><span className="text-text-muted">Recommendation: </span>{f.recommendation}</p>
          <p><span className="text-text-muted">How to validate: </span>{f.validation}</p>
          {linked.length > 0 && <p><span className="text-text-muted">Linked: </span>{linked.map((l) => `${l.title} (${label(l.evidence_kind)})`).join('; ')}</p>}
          {!plannable && f.status === 'open' && <p className="text-amber-200">Only Python backend changes can be verified by measurement for now.</p>}
        </div>
      )}
    </li>
  );
}

// --- plan, execution and report ----------------------------------------------------------------------------

function PlanDetail({ projectId, plan, onChanged, onError }) {
  const [report, setReport] = useState(null);
  const [runTests, setRunTests] = useState(true);
  const [showDiff, setShowDiff] = useState(false);
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try { setReport((await getPerfReport(projectId, plan.id)).report); } catch (e) { onError(e?.error || 'Could not load the report.'); }
  }, [projectId, plan.id, onError]);
  useEffect(() => { load(); }, [load]);
  const exe = report?.execution;
  useEffect(() => {
    if (!exe || !ACTIVE.has(exe.status)) return undefined;
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [exe, load]);
  const act = async (fn) => { setBusy(true); try { await fn(); await load(); onChanged(); } catch (e) { onError(e?.error || 'Request failed.'); } finally { setBusy(false); } };
  const status = report?.autopilot_plan_status;
  const cmp = report?.comparison;
  return (
    <div className="space-y-4">
      <Card title="Optimization plan" actions={status && <Badge value={status} />}>
        <div className="grid gap-3 text-xs text-text-secondary md:grid-cols-2">
          <div className="space-y-1.5">
            <p className="text-sm text-text-primary">{plan.problem}</p>
            <p><span className="text-text-muted">Proposed change: </span>{plan.proposed_change}</p>
            <p><span className="text-text-muted">Expected benefit: </span>{plan.expected_benefit}</p>
            <p><span className="text-text-muted">Files: </span><span className="font-mono">{plan.files.join(', ')}</span></p>
            <p><span className="text-text-muted">Tests: </span><span className="font-mono">{plan.tests.join(', ') || 'none linked'}</span></p>
            <p><span className="text-text-muted">Rank: </span>{plan.rank_score} ({plan.rank_reasons.join('; ')})</p>
          </div>
          <div className="space-y-1.5">
            <p><span className="text-text-muted">Judged on: </span><span className="font-mono">{plan.target_endpoints.join(', ')}</span></p>
            <p><span className="text-text-muted">Workload: </span>{plan.workload.endpoints.map((e) => `${e.method} ${e.path}`).join(', ')} · up to {plan.workload.requests_per_endpoint} req or {plan.workload.max_seconds_per_endpoint}s per endpoint × {plan.workload.repetitions} reps, concurrency {plan.workload.concurrency}</p>
            <p><span className="text-text-muted">Thresholds: </span>improve ≥ {plan.thresholds.min_improvement_pct}% beyond {plan.thresholds.noise_factor}× noise; regress &gt; {plan.thresholds.max_regression_pct}% latency, +{plan.thresholds.max_error_rate_increase_pp}pp errors, +{plan.thresholds.max_memory_increase_pct}% memory, −{plan.thresholds.max_throughput_drop_pct}% throughput</p>
            <p><span className="text-text-muted">Risks: </span>{plan.risks.join(' ')}</p>
            <p><span className="text-text-muted">Rollback: </span>{plan.rollback}</p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border-subtle pt-3">
          {status === 'awaiting_approval' && (<>
            <Btn tone="good" disabled={busy} onClick={() => act(() => decidePlan(projectId, plan.autopilot_plan_id, 'approve'))}><FaCheck className="h-2.5 w-2.5" /> Approve</Btn>
            <Btn tone="bad" disabled={busy} onClick={() => act(() => decidePlan(projectId, plan.autopilot_plan_id, 'reject'))}><FaTimes className="h-2.5 w-2.5" /> Reject</Btn>
          </>)}
          {status === 'approved' && (<>
            <label className="flex items-center gap-1.5 text-[11px] text-text-secondary"><input type="checkbox" checked={runTests} onChange={(e) => setRunTests(e.target.checked)} /> run tests (Docker sandbox)</label>
            <Btn tone="primary" disabled={busy} onClick={() => act(() => executePlan(projectId, plan.autopilot_plan_id, runTests))}><FaPlay className="h-2.5 w-2.5" /> Optimize in an isolated copy</Btn>
          </>)}
          {exe && ACTIVE.has(exe.status) && <Btn tone="bad" disabled={busy || exe.cancel_requested} onClick={() => act(() => cancelExecution(projectId, exe.id))}><FaStop className="h-2.5 w-2.5" /> {exe.cancel_requested ? 'Cancelling…' : 'Cancel'}</Btn>}
        </div>
      </Card>

      {exe && (
        <Card title="Execution" actions={<Badge value={exe.status} />}>
          <ol className="grid gap-1.5 text-xs sm:grid-cols-2 lg:grid-cols-4">
            {exe.stages.map((s) => (
              <li key={s.name} className="rounded-lg bg-bg-base/60 px-3 py-2">
                <div className="flex items-center justify-between gap-2"><span className="text-text-primary">{s.name}</span><Badge value={s.status} /></div>
                {s.detail && <p className="mt-1 break-words text-[10px] text-text-muted">{s.detail}</p>}
              </li>
            ))}
          </ol>
          {exe.error && <p className="mt-2 text-xs text-rose-300">{exe.error}</p>}
          {report?.correctness && (
            <div className="mt-3 text-[11px] text-text-secondary">
              <p className="mb-1 text-[10px] uppercase tracking-wide text-text-muted">Correctness checks (before → after)</p>
              {report.correctness.after.map((c) => {
                const b = report.correctness.before.find((x) => x.check_id === c.check_id);
                return <p key={c.check_id}>{c.label}: {b ? <Badge value={b.status} /> : '—'} → <Badge value={c.status} /> <span className="text-text-muted">{c.environment}</span></p>;
              })}
            </div>
          )}
        </Card>
      )}

      {cmp && (
        <Card title="Before and after" actions={<Badge value={cmp.decision} />}>
          <div className="space-y-3 text-xs text-text-secondary">
            <ul className="list-disc pl-4">{cmp.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-[11px]">
                <thead className="text-[10px] uppercase tracking-wide text-text-muted">
                  <tr><th className="py-1 pr-2">Endpoint</th><th className="pr-2">Median before → after</th><th className="pr-2">p95 before → after</th><th className="pr-2">Req/s before → after</th><th className="pr-2">Errors</th><th className="pr-2">Change</th><th>Verdict</th></tr>
                </thead>
                <tbody>{cmp.per_endpoint.map((r) => (
                  <tr key={r.endpoint} className="border-t border-border-subtle align-top">
                    <td className="py-1 pr-2 font-mono text-text-primary">{r.endpoint}</td>
                    <td className="pr-2">{ms(r.before.median_ms)} → {ms(r.after.median_ms)}</td>
                    <td className="pr-2">{ms(r.before.p95_ms)} → {ms(r.after.p95_ms)}</td>
                    <td className="pr-2">{num(r.before.throughput_rps)} → {num(r.after.throughput_rps)}</td>
                    <td className="pr-2">{r.before.error_rate_pct}% → {r.after.error_rate_pct}%</td>
                    <td className="pr-2">{num(r.median_change_pct, '%')} <span className="text-text-muted">(noise {r.noise_pct}%)</span></td>
                    <td title={r.reason}><Badge value={r.verdict} /></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            <p>Resources: peak memory {num(cmp.resources?.before?.mem_max_mb, ' MB')} → {num(cmp.resources?.after?.mem_max_mb, ' MB')} ({num(cmp.resources?.peak_memory_change_pct, '%')}), average CPU {num(cmp.resources?.before?.cpu_avg_pct, '%')} → {num(cmp.resources?.after?.cpu_avg_pct, '%')}</p>
            <EnvironmentInfo env={cmp.environment} />
            <p><span className="text-text-muted">Rollback status: </span>{report.rollback_status}</p>
            {report.diff && <div><Btn onClick={() => setShowDiff((v) => !v)}>{showDiff ? 'Hide' : 'Show'} diff</Btn>{showDiff && <div className="mt-2"><Pre>{report.diff}</Pre></div>}</div>}
          </div>
        </Card>
      )}
      {report && (
        <Card title="Next steps">
          <ul className="list-disc pl-4 text-xs text-text-secondary">{report.next_steps.map((s, i) => <li key={i}>{s}</li>)}</ul>
          <p className="mt-2 text-[11px] text-text-muted">{report.measured_vs_estimated}</p>
        </Card>
      )}
    </div>
  );
}

// --- page ------------------------------------------------------------------------------------------------------

/**
 * AIForge Performance Engineer: static findings, a measured baseline of the app running in the Docker
 * sandbox, approved optimizations and measured before/after comparisons. Every number shown comes from
 * a run that happened; a metric that could not be measured is shown as "—".
 */
export default function PerformanceEngineerPage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [latest, setLatest] = useState(null);
  const [findings, setFindings] = useState([]);
  const [runs, setRuns] = useState([]);
  const [plans, setPlans] = useState([]);
  const [planId, setPlanId] = useState('');
  const [measure, setMeasure] = useState(true);
  const [wl, setWl] = useState({ requests_per_endpoint: 200, concurrency: 4, repetitions: 3, max_seconds_per_endpoint: 20, endpoints: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const onError = useCallback((m) => setError(m), []);

  useEffect(() => {
    listAutopilotProjects().then((r) => {
      setProjects(r.projects || []);
      const preferred = (r.projects || []).find((p) => p.project_id === activeProjectId);
      setProjectId((cur) => cur || preferred?.project_id || r.projects?.[0]?.project_id || '');
    }).catch((e) => setError(e?.error || 'Could not load projects.'));
  }, [activeProjectId]);

  const refresh = useCallback(async () => {
    if (!projectId) return;
    try {
      const [l, f, r, p] = await Promise.all([getLatestPerfAnalysis(projectId), listPerfFindings(projectId), listPerfRuns(projectId), listPerfPlans(projectId)]);
      setLatest(l); setFindings(f.items || []); setRuns(r.runs || []); setPlans(p.plans || []);
    } catch (e) { setError(e?.error || 'Could not load performance data.'); }
  }, [projectId]);
  useEffect(() => { setLatest(null); setFindings([]); setRuns([]); setPlans([]); setPlanId(''); setError(''); refresh(); }, [projectId, refresh]);
  const active = latest?.active_job || runs.some((r) => ACTIVE.has(r.status));
  useEffect(() => {
    if (!active) return undefined;
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [active, refresh]);

  const workload = () => {
    const endpoints = wl.endpoints.split('\n').map((l) => l.trim()).filter(Boolean).map((l) => {
      const [method, ...rest] = l.split(/\s+/);
      return rest.length ? { method: method.toUpperCase(), path: rest.join(' ') } : { method: 'GET', path: method };
    });
    return { requests_per_endpoint: Number(wl.requests_per_endpoint), concurrency: Number(wl.concurrency),
      repetitions: Number(wl.repetitions), max_seconds_per_endpoint: Number(wl.max_seconds_per_endpoint), endpoints };
  };
  const analyze = async () => {
    setBusy(true); setError('');
    try { await startPerfAnalysis(projectId, { measure, workload: workload() }); await refresh(); }
    catch (e) { setError(e?.error || 'Could not start the analysis.'); } finally { setBusy(false); }
  };
  const plan = async (f) => {
    setBusy(true); setError('');
    try { const p = (await createPerfPlan(projectId, { finding_id: f.id })).plan; await refresh(); setPlanId(p.id); }
    catch (e) { setError(e?.error || 'Could not create the plan.'); } finally { setBusy(false); }
  };
  const a = latest?.analysis;
  const baseline = latest?.baseline;
  const measured = findings.filter((f) => f.evidence_kind === 'measured');
  const staticOnes = findings.filter((f) => f.evidence_kind !== 'measured');
  const selectedPlan = useMemo(() => plans.find((p) => p.id === planId), [plans, planId]);
  const runningRun = runs.find((r) => ACTIVE.has(r.status));
  const project = projects.find((p) => p.project_id === projectId);

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaTachometerAlt className="h-4 w-4" /> Performance Engineer</h1>
          <p className="text-xs text-text-muted">Measured bottlenecks, approved optimizations, and before/after results from real runs in the Docker sandbox.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {projectId && (<>
        <Card title="Performance analysis" actions={a && <Badge value={a.status} />}>
          <div className="space-y-3">
            {a && <p className="text-xs text-text-secondary">Stack: {(a.stack || []).join(', ') || project?.name} · {a.support_reason}</p>}
            <div className="flex flex-wrap items-end gap-2">
              <label className="flex items-center gap-1.5 self-center text-[11px] text-text-secondary"><input type="checkbox" checked={measure} onChange={(e) => setMeasure(e.target.checked)} /> measure a baseline (Docker)</label>
              <Field name="Requests / endpoint"><input type="number" min="10" max="2000" value={wl.requests_per_endpoint} onChange={(e) => setWl({ ...wl, requests_per_endpoint: e.target.value })} className={`${inputCls} w-24`} /></Field>
              <Field name="Concurrency"><input type="number" min="1" max="16" value={wl.concurrency} onChange={(e) => setWl({ ...wl, concurrency: e.target.value })} className={`${inputCls} w-20`} /></Field>
              <Field name="Repetitions"><input type="number" min="1" max="5" value={wl.repetitions} onChange={(e) => setWl({ ...wl, repetitions: e.target.value })} className={`${inputCls} w-20`} /></Field>
              <Field name="Max s / endpoint"><input type="number" min="1" max="120" value={wl.max_seconds_per_endpoint} onChange={(e) => setWl({ ...wl, max_seconds_per_endpoint: e.target.value })} className={`${inputCls} w-20`} /></Field>
              <Field name="Endpoints (optional, one per line)"><textarea rows={1} value={wl.endpoints} onChange={(e) => setWl({ ...wl, endpoints: e.target.value })} placeholder="GET /api/items  (default: from /openapi.json)" className={`${inputCls} w-72 font-mono`} /></Field>
              <Btn tone="primary" disabled={busy || !!latest?.active_job} onClick={analyze}><FaSync className={`h-2.5 w-2.5 ${latest?.active_job ? 'animate-spin' : ''}`} /> Analyze performance</Btn>
            </div>
            {runningRun && (
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-text-secondary">
                <Badge value={runningRun.status} />
                {runningRun.stages.map((s) => <span key={s.name}>{s.name}: {s.status}</span>)}
                <Btn tone="bad" onClick={() => cancelPerfRun(projectId, runningRun.id).then(refresh).catch((e) => onError(e?.error))}><FaStop className="h-2.5 w-2.5" /> Cancel</Btn>
              </div>
            )}
            {a?.error && <p className="text-xs text-rose-300">{a.error}</p>}
          </div>
        </Card>

        {baseline && (
          <Card title="Baseline measurement" actions={<Badge value={baseline.measurement?.status || baseline.status} />}>
            {baseline.error && <p className="mb-2 text-xs text-amber-200">{baseline.error}</p>}
            {baseline.measurement?.status === 'measured' && <EndpointTable endpoints={baseline.measurement.endpoints} />}
            <div className="mt-3"><EnvironmentInfo env={baseline.environment} m={baseline.measurement} /></div>
            {baseline.measurement?.logs_tail && baseline.measurement.status !== 'measured' && <div className="mt-2"><Pre>{baseline.measurement.logs_tail}</Pre></div>}
          </Card>
        )}

        {findings.length > 0 && (
          <Card title={`Findings (${findings.length})`}>
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <p className="mb-1.5 text-[10px] uppercase tracking-wide text-text-muted">Measured bottlenecks ({measured.length})</p>
                {measured.length ? <ul className="space-y-1.5">{measured.map((f) => <FindingRow key={f.id} f={f} all={findings} onPlan={plan} busy={busy} />)}</ul>
                  : <p className="text-xs text-text-muted">{baseline?.measurement?.status === 'measured' ? 'No endpoint crossed the slow/error thresholds in the baseline.' : 'Nothing measured yet.'}</p>}
              </div>
              <div>
                <p className="mb-1.5 text-[10px] uppercase tracking-wide text-text-muted">Static warnings and hypotheses ({staticOnes.length}) — not measured</p>
                <ul className="space-y-1.5">{staticOnes.map((f) => <FindingRow key={f.id} f={f} all={findings} onPlan={plan} busy={busy} />)}</ul>
              </div>
            </div>
          </Card>
        )}

        {plans.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-xs text-text-secondary">
            <span className="text-[10px] uppercase tracking-wide text-text-muted">Plans (ranked)</span>
            {plans.map((p) => (
              <button key={p.id} onClick={() => setPlanId(p.id)} className={`rounded-lg border px-2 py-1 ${p.id === planId ? 'border-accent-blue bg-accent-blue/10' : 'border-border-dark hover:bg-surface-hover'}`}>
                <span className="max-w-[16rem] truncate">{p.problem}</span> <span className="text-text-muted">· rank {p.rank_score} · {new Date(p.created_at).toLocaleTimeString()}</span>
              </button>
            ))}
          </div>
        )}
        {selectedPlan && <PlanDetail key={selectedPlan.id} projectId={projectId} plan={selectedPlan} onChanged={refresh} onError={onError} />}
      </>)}
    </div>
  );
}
