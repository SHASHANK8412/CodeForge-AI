import React, { useCallback, useEffect, useState } from 'react';
import { FaCheck, FaChevronDown, FaChevronRight, FaDna, FaFlask, FaPlay, FaRocket, FaSearch, FaStop } from 'react-icons/fa';
import {
  abortExperiment, approveCandidate, discoverOpportunities, getEngineeringMemory, getExperiment, listExperiments,
  listOpportunities, planExperiment, promoteExperiment, runExperiment,
} from '../services/evolutionEngine';
import { listAutopilotProjects } from '../services/evolutionAutopilot';

const GOOD = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
const BAD = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
const WARN = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
const GREY = 'bg-slate-700/50 text-slate-300 border-slate-600';
const TONE = {
  validated_improvement: GOOD, improved: GOOD, promoted: GOOD, won: GOOD, passed: GOOD, eligible: GOOD, evaluated: GOOD, completed: GOOD,
  strong: GOOD, direct: GOOD, awaiting_approval: 'bg-violet-500/15 text-violet-300 border-violet-500/30', approved: GOOD,
  regression: BAD, regressed: BAD, failed: BAD, rejected: BAD, rolled_back: BAD, candidate_defect: BAD,
  no_improvement: WARN, inconclusive: WARN, moderate: WARN, related: WARN, flaky: WARN, infrastructure: WARN, stale: WARN,
  planned: GREY, weak: GREY, insufficient: GREY, not_measured: GREY, not_evaluated: GREY, cancelled: GREY, duplicate: GREY,
  generation_failed: BAD, insufficient_evidence: WARN,
};
const ACTIVE = new Set(['queued', 'running', 'promoting', 'generating', 'evaluating']);
const label = (s) => String(s ?? '').replace(/_/g, ' ');
const Badge = ({ value }) => (value == null ? null :
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
const Pre = ({ children }) => <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-black/50 p-3 font-mono text-[11px] text-slate-300">{children}</pre>;
const fmt = (v, unit = '') => (v == null ? '—' : `${v}${unit}`);

// --- opportunity explorer and planner ----------------------------------------------------------------------------

function Opportunities({ projectId, items, busy, act, onPlanned }) {
  const [open, setOpen] = useState('');
  const [searched, setSearched] = useState(false);
  const [cfg, setCfg] = useState({ max_candidates: 2, weights: { performance: 0.5, security: 0.15, reliability: 0.15, maintainability: 0.1, resource_efficiency: 0.1 } });
  return (
    <Card title={`Opportunity explorer (${items.length})`} actions={<Btn disabled={busy} onClick={() => act(async () => { await discoverOpportunities(projectId); setSearched(true); })}><FaSearch className="h-2.5 w-2.5" /> Discover from evidence</Btn>}>
      <p className="mb-2 text-[11px] text-text-muted">Opportunities come from existing evidence (Performance Engineer, Security Guardian, past experiments). Expected benefits are predictions until an experiment measures them.</p>
      {items.length === 0 ? <p className="text-xs text-text-muted">{searched ? 'The current evidence shows no opportunity this version can experiment on (N+1 queries on measurable endpoints, verified security findings). That does not mean the code cannot be improved.' : 'No opportunities discovered yet.'}</p> : (
        <ul className="space-y-1.5">{items.map((o) => (
          <li key={o.id} className="rounded-xl border border-border-subtle bg-bg-base/40">
            <button className="flex w-full flex-wrap items-center gap-2 px-3 py-2 text-left" onClick={() => setOpen(open === o.id ? '' : o.id)}>
              {open === o.id ? <FaChevronDown className="h-2.5 w-2.5 text-text-muted" /> : <FaChevronRight className="h-2.5 w-2.5 text-text-muted" />}
              <span className="rounded bg-bg-base px-1.5 text-[10px] font-mono text-text-secondary">{o.priority}</span>
              <span className="text-xs text-text-primary">{o.title}</span>
              <Badge value={label(o.category)} /><span className="text-[10px] text-text-muted">confidence {o.confidence}</span>
              {!o.experimentable && <span className="text-[10px] text-amber-200">not experimentable</span>}
            </button>
            {open === o.id && (
              <div className="space-y-1.5 border-t border-border-subtle px-3 py-2 text-xs text-text-secondary">
                {o.evidence.map((e, i) => <p key={i}><Badge value={e.kind === 'measured' ? 'passed' : 'planned'} /> <span className="text-text-muted">{e.source}:</span> <span className="font-mono">{e.detail}</span></p>)}
                <p><span className="text-text-muted">Hypothesis: </span>{o.hypothesis}</p>
                <p><span className="text-text-muted">Expected benefit: </span>{o.expected_benefit}</p>
                <p><span className="text-text-muted">Possible regressions: </span>{o.possible_regressions.join('; ') || '—'}</p>
                <p><span className="text-text-muted">Validation: </span>{o.validation}</p>
                <p><span className="text-text-muted">Affected components (Digital Twin): </span><span className="font-mono">{o.components.join(', ') || '—'}</span></p>
                <p className="text-[11px] text-text-muted">Priority factors: {Object.entries(o.priority_factors).map(([k, v]) => `${label(k)} ${v}`).join(' · ')}</p>
                {o.history.length > 0 && <p className="text-[11px]">Past experiments: {o.history.map((h) => `${h.strategy} ${h.result} (${h.applicability}, ${h.evidence_quality})`).join('; ')}</p>}
                {o.experimentable ? (
                  <div className="flex flex-wrap items-end gap-2 rounded-lg border border-border-subtle p-2">
                    <label className="flex flex-col text-[10px] uppercase text-text-muted">Candidates
                      <select className={inputCls} value={cfg.max_candidates} onChange={(e) => setCfg({ ...cfg, max_candidates: Number(e.target.value) })}>{[1, 2, 3].map((n) => <option key={n}>{n}</option>)}</select></label>
                    {Object.keys(cfg.weights).map((k) => (
                      <label key={k} className="flex flex-col text-[10px] uppercase text-text-muted">{label(k)}
                        <input type="number" min="0" max="1" step="0.05" className={`${inputCls} w-20`} value={cfg.weights[k]} onChange={(e) => setCfg({ ...cfg, weights: { ...cfg.weights, [k]: Number(e.target.value) } })} /></label>
                    ))}
                    <Btn tone="primary" disabled={busy} onClick={() => act(async () => onPlanned((await planExperiment(projectId, { opportunity_id: o.id, ...cfg })).experiment))}><FaFlask className="h-2.5 w-2.5" /> Plan experiment</Btn>
                  </div>
                ) : <p className="text-amber-200">{o.not_experimentable_reason}</p>}
              </div>
            )}
          </li>
        ))}</ul>
      )}
    </Card>
  );
}

// --- experiment: plan, live monitor, comparison, promotion -------------------------------------------------------------

function Plan({ e }) {
  const p = e.plan;
  return (
    <div className="space-y-1 text-xs text-text-secondary">
      <p><span className="text-text-muted">Hypothesis: </span>{p.hypothesis}</p>
      <p><span className="text-text-muted">Baseline: </span>{p.baseline}</p>
      <ul className="list-disc pl-4">{p.strategies.map((s) => <li key={s.id}><span className="text-text-primary">{s.title}</span> <span className="font-mono text-[10px] text-text-muted">{s.id}</span>{s.memory_note && <span className="text-[11px] text-violet-200"> — memory: {s.memory_note}</span>}</li>)}</ul>
      {p.suppressed_strategies.length > 0 && <p className="text-amber-200">Not tried again: {p.suppressed_strategies.map((s) => `${s.strategy} (${s.note})`).join('; ')}</p>}
      <p><span className="text-text-muted">Acceptance: </span>target median at least {p.thresholds.min_improvement_pct}% faster and beyond {p.thresholds.noise_factor}× the run-to-run spread; no endpoint more than {p.thresholds.max_regression_pct}% slower; tests, security and quality must not regress</p>
      <p><span className="text-text-muted">Workload: </span>{p.workload.endpoints.map((x) => `${x.method} ${x.path}`).join(', ')} · {p.workload.requests_per_endpoint} requests × {p.workload.repetitions} repetitions, concurrency {p.workload.concurrency}</p>
      <p><span className="text-text-muted">Environment: </span>{p.environment}</p>
      <details><summary className="cursor-pointer text-[11px] text-text-muted">Safety, limits and cleanup</summary>
        <ul className="list-disc pl-4 text-[11px]">{[...p.safety, ...Object.entries(p.resource_limits).map(([k, v]) => `${k}: ${v}`), ...p.cleanup, `time limit ${p.max_seconds}s`].map((x, i) => <li key={i}>{x}</li>)}</ul></details>
      {p.rejected_reasons.length > 0 && <p className="text-rose-200">Plan rejected: {p.rejected_reasons.join('; ')}</p>}
    </div>
  );
}

const ROWS = [
  ['Status', (c) => <Badge value={c.status} />],
  ['Eligible', (c) => <Badge value={c.eligible ? 'eligible' : (c.failure_kind || 'rejected')} />],
  ['Score', (c) => fmt(c.score)],
  ['Tests', (c) => { const t = c.correctness?.tests; return t ? `${t.status} ${Object.entries(t.counts || {}).map(([k, v]) => `${v} ${k}`).join(', ')}${c.correctness.flaky ? ' (flaky)' : ''}` : '—'; }],
  ['Correctness', (c) => (c.correctness?.accepted ? 'no regression' : [...(c.correctness?.regressions || []), ...(c.correctness?.unverified || [])].join('; ') || '—')],
  ['Security', (c) => (c.security?.status === 'evaluated' ? (c.security.new_serious.length ? `new: ${c.security.new_serious.join('; ')}` : c.security.detail) : c.security?.detail || '—')],
  ['Performance', (c) => <span><Badge value={c.performance?.decision} /> {(c.performance?.target_rows || []).map((r) => r.reason).join('; ')}</span>],
  ['Resources', (c) => (c.resources?.mem_max_mb != null ? `peak ${c.resources.mem_max_mb} MB, CPU avg ${fmt(c.resources.cpu_avg_pct, '%')}` : 'not measured')],
  ['Resilience', (c) => `${label(c.resilience?.status)}: ${c.resilience?.reason || ''}`],
  ['Maintainability', (c) => (c.maintainability?.changed_lines != null ? `${c.maintainability.changed_lines} changed lines, branches ${c.maintainability.branches_delta >= 0 ? '+' : ''}${c.maintainability.branches_delta}` : '—')],
  ['Evidence', (c) => label(c.performance?.evidence || 'insufficient')],
];

function Comparison({ e }) {
  const [diff, setDiff] = useState('');
  const base = e.measurement?.baseline;
  return (
    <div className="space-y-2 text-xs text-text-secondary">
      {base && <p className="text-[11px]"><span className="text-text-muted">Baseline (same run): </span>{(base.endpoints || []).map((x) => `${x.method} ${x.path}: median ${x.median_ms} ms, p95 ${x.p95_ms} ms, ${x.throughput_rps} rps`).join(' · ') || base.error}</p>}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-[11px]">
          <thead className="text-[10px] uppercase tracking-wide text-text-muted"><tr><th className="py-1 pr-2" />{e.candidates.map((c) => <th key={c.id} className="pr-2">{c.id} · {label(c.strategy)}{c.id === e.selected && <span className="ml-1 text-emerald-300">★ selected</span>}</th>)}</tr></thead>
          <tbody>{ROWS.map(([name, f]) => (
            <tr key={name} className="border-t border-border-subtle align-top"><td className="py-1 pr-2 text-text-muted">{name}</td>{e.candidates.map((c) => <td key={c.id} className="pr-2 break-words">{f(c)}</td>)}</tr>
          ))}</tbody>
        </table>
      </div>
      {e.candidates.map((c) => (
        <details key={c.id} className="rounded-lg border border-border-subtle p-2">
          <summary className="cursor-pointer">{c.id}: mandatory constraints{c.eligible ? ' and score' : ''}</summary>
          <ul className="mt-1 space-y-0.5">{c.constraints.map((x) => <li key={x.name}>{x.passed ? <span className="text-emerald-300">✓</span> : <span className="text-rose-300">✗</span>} {x.name} — <span className="text-text-muted">{x.detail}</span></li>)}</ul>
          {c.eligible && <table className="mt-1 text-[11px]"><tbody>{Object.entries(c.score_breakdown).map(([k, v]) => <tr key={k}><td className="pr-2 text-text-muted">{label(k)}</td><td className="pr-2">{v.input}</td><td className="pr-2">score {v.score}</td><td className="pr-2">× {v.weight}</td><td>= {v.contribution}</td></tr>)}</tbody></table>}
          {c.generation_error && <p className="text-amber-200">{c.generation_error}</p>}
          <p className="text-[10px] text-text-muted">Model configuration: {Object.entries(c.model || {}).map(([k, v]) => `${k}: ${v}`).join(' · ')}</p>
          {c.diff && <Btn className="mt-1" onClick={() => setDiff(diff === c.id ? '' : c.id)}>{diff === c.id ? 'Hide diff' : 'Show diff'}</Btn>}
          {diff === c.id && <Pre>{c.diff}</Pre>}
          {c.correctness?.tests?.output_tail && !c.correctness.accepted && <details><summary className="cursor-pointer text-[11px] text-text-muted">Test output</summary><Pre>{c.correctness.tests.output_tail}</Pre></details>}
        </details>
      ))}
      <p className="text-[11px]"><span className="text-text-muted">Selection: </span>{e.selection?.method} · outcome <Badge value={e.outcome} /> {e.outcome_reasons.join(' ')}</p>
    </div>
  );
}

function Promotion({ e, busy, onApprove, onPromote }) {
  const sel = e.candidates.find((c) => c.id === e.selected);
  const p = e.promotion;
  return (
    <div className="space-y-2 text-xs text-text-secondary">
      {!sel && <p>No candidate was selected: {e.outcome_reasons.join(' ')}</p>}
      {sel && <p>Selected: <span className="text-text-primary">{sel.id} ({label(sel.strategy)})</span> · changes {Object.keys(sel.changes).join(', ')} · patch {sel.patch_hash?.slice(0, 12)}</p>}
      {e.approval && <p>Approved by {e.approval.approved_by} for source revision <span className="font-mono">{e.approval.source_revision.slice(0, 12)}</span> and patch <span className="font-mono">{e.approval.patch_hash.slice(0, 12)}</span>{!e.approval.valid && <span className="text-amber-200"> — invalidated: {e.approval.invalidated_reason}</span>}</p>}
      <div className="flex flex-wrap gap-2">
        {e.status === 'evaluated' && e.outcome === 'awaiting_approval' && <Btn tone="good" disabled={busy} onClick={onApprove}><FaCheck className="h-2.5 w-2.5" /> Approve {sel?.id}</Btn>}
        {e.status === 'approved' && <Btn tone="primary" disabled={busy} onClick={onPromote}><FaRocket className="h-2.5 w-2.5" /> Promote (Autopilot: checks, re-measure, apply, final tests)</Btn>}
      </div>
      {p && (
        <div className="space-y-0.5 rounded-lg border border-border-subtle p-2">
          <p>Promotion <Badge value={p.status} /> {p.execution_id && <span className="font-mono text-[10px] text-text-muted">Autopilot {p.execution_id}</span>}</p>
          {p.gate?.decision && <p><span className="text-text-muted">Re-measurement: </span><Badge value={p.gate.decision} /> {(p.gate.reasons || []).slice(0, 2).join('; ')}</p>}
          {p.final_tests && <p><span className="text-text-muted">Final tests on the promoted project: </span><Badge value={p.final_tests.status} /> {Object.entries(p.final_tests.counts || {}).map(([k, v]) => `${v} ${k}`).join(', ')}</p>}
          <p><span className="text-text-muted">Rollback: </span>{p.rolled_back ? p.rollback_detail : ACTIVE.has(e.status) ? 'in progress' : 'not needed'}</p>
          {p.error && <p className="text-amber-200">{p.error}</p>}
        </div>
      )}
    </div>
  );
}

// --- page ------------------------------------------------------------------------------------------------------------------

/**
 * AIForge Evolution Engine: discover improvement opportunities from evidence, generate several candidate
 * implementations in isolated copies, evaluate them with the same tests, security re-check and measurements,
 * select one by deterministic rules, and promote it only after approval. Values shown come from the backend.
 */
export default function EvolutionEnginePage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [ops, setOps] = useState([]);
  const [exps, setExps] = useState([]);
  const [activeJob, setActiveJob] = useState(null);
  const [selected, setSelected] = useState('');
  const [exp, setExp] = useState(null);
  const [related, setRelated] = useState([]);
  const [mem, setMem] = useState([]);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

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
      const [o, x, m] = await Promise.all([listOpportunities(projectId), listExperiments(projectId), getEngineeringMemory(projectId)]);
      setOps(o.opportunities || []); setExps(x.experiments || []); setActiveJob(x.active_job || null); setMem(m.memory || []);
      setSelected((cur) => cur || x.experiments?.[0]?.id || '');
    } catch (e) { setError(e?.error || 'Could not load the Evolution Engine.'); }
  }, [projectId]);
  useEffect(() => { setSelected(''); setExp(null); setError(''); refresh(); }, [projectId, refresh]);
  const loadExp = useCallback(async () => {
    if (!selected) { setExp(null); return; }
    try { const r = await getExperiment(projectId, selected); setExp(r.experiment); setRelated(r.memory || []); setActiveJob(r.active_job || null); }
    catch (e) { setError(e?.error || 'Could not load the experiment.'); }
  }, [projectId, selected]);
  useEffect(() => { setConsent(false); loadExp(); }, [loadExp]);
  useEffect(() => {
    if (!exp || !(ACTIVE.has(exp.status) || activeJob)) return undefined;
    const t = setInterval(() => { loadExp(); refresh(); }, 3000);
    return () => clearInterval(t);
  }, [exp, activeJob, loadExp, refresh]);

  const act = async (fn) => { setBusy(true); setError(''); try { await fn(); await refresh(); await loadExp(); } catch (e) { setError(e?.error || 'Request failed.'); } finally { setBusy(false); } };
  const live = exp && ACTIVE.has(exp.status);

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaDna className="h-4 w-4" /> Evolution Engine</h1>
          <p className="text-xs text-text-muted">Every experiment makes AIForge a better engineer: alternatives are generated, measured and compared — and only evidence decides.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {projectId && (<>
        <Opportunities projectId={projectId} items={ops} busy={busy} act={act} onPlanned={(x) => setSelected(x.id)} />

        {exps.length > 0 && (
          <Card title="Experiments">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-[11px] text-text-secondary">
                <thead className="text-[10px] uppercase tracking-wide text-text-muted"><tr><th className="py-1 pr-2">Created</th><th className="pr-2">Opportunity</th><th className="pr-2">Status</th><th className="pr-2">Outcome</th><th className="pr-2">Candidates</th><th /></tr></thead>
                <tbody>{exps.map((x) => (
                  <tr key={x.id} className={`border-t border-border-subtle ${x.id === selected ? 'bg-accent-blue/5' : ''}`}>
                    <td className="py-1 pr-2">{new Date(x.created_at).toLocaleString()}</td><td className="pr-2">{x.title}</td>
                    <td className="pr-2"><Badge value={x.status} /></td><td className="pr-2"><Badge value={x.outcome} /></td>
                    <td className="pr-2">{x.candidates.map((c) => `${c.id}:${c.strategy}${c.eligible ? '✓' : ''}`).join(' ') || '—'}</td>
                    <td><Btn onClick={() => setSelected(x.id)}>Open</Btn></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </Card>
        )}

        {exp && (<>
          <Card title="Experiment plan" actions={<div className="flex items-center gap-2"><Badge value={exp.status} /><Badge value={exp.outcome} /></div>}>
            <Plan e={exp} />
            {exp.status === 'planned' && (
              <div className="mt-2 flex flex-wrap items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-xs">
                <label className="flex items-center gap-1.5 text-amber-100"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                  I approve generating {exp.plan.strategies.length} candidate(s) with the local model and running them in isolated copies (the project is not changed)</label>
                <Btn tone="good" disabled={busy || !consent || !!activeJob} onClick={() => act(() => runExperiment(projectId, exp.id))}><FaPlay className="h-2.5 w-2.5" /> Run experiment</Btn>
              </div>
            )}
          </Card>

          {(live || exp.audit.length > 2) && (
            <Card title="Live experiment monitor" actions={live && exp.status !== 'promoting' && <Btn tone="bad" disabled={busy || exp.cancel_requested} onClick={() => act(() => abortExperiment(projectId, exp.id))}><FaStop className="h-2.5 w-2.5" /> {exp.cancel_requested ? 'Aborting…' : 'Abort'}</Btn>}>
              <div className="space-y-2 text-xs text-text-secondary">
                <p>Now: <span className="text-text-primary">{exp.current || '—'}</span>{exp.source_revision && <span className="text-text-muted"> · source revision <span className="font-mono">{exp.source_revision.slice(0, 12)}</span></span>}{exp.duration_seconds != null && <span className="text-text-muted"> · {exp.duration_seconds}s</span>}</p>
                <div className="flex flex-wrap gap-2">{exp.candidates.map((c) => <span key={c.id} className="rounded-lg border border-border-subtle px-2 py-1">{c.id} {label(c.strategy)} <Badge value={c.status} /> {Object.entries(c.durations || {}).map(([k, v]) => `${k} ${v}`).join(' · ')}</span>)}</div>
                {exp.error && <p className="text-amber-200">{exp.error}</p>}
                <Pre>{exp.audit.slice(-14).map((a) => `${String(a.at).slice(11, 19)} ${a.action}`).join('\n')}</Pre>
              </div>
            </Card>
          )}

          {exp.candidates.length > 0 && !live && <Card title="Candidate comparison"><Comparison e={exp} /></Card>}
          {['evaluated', 'approved', 'promoting', 'completed'].includes(exp.status) && (
            <Card title="Promotion workflow"><Promotion e={exp} busy={busy}
              onApprove={() => act(() => approveCandidate(projectId, exp.id, exp.selected))}
              onPromote={() => act(() => promoteExperiment(projectId, exp.id))} /></Card>
          )}
          {related.length > 0 && <Card title="Related experiments (Engineering Memory)">
            <ul className="space-y-0.5 text-[11px] text-text-secondary">{related.map((h) => <li key={h.id}><Badge value={h.applicability} /> {h.strategy} <Badge value={h.result} /> evidence <Badge value={h.evidence_quality} /> {h.measured?.median_change_pct != null && `median ${h.measured.median_change_pct}%`} <span className="text-text-muted">{h.scope}</span></li>)}</ul>
          </Card>}
        </>)}

        <Card title={`Engineering memory (${mem.length})`}>
          {mem.length === 0 ? <p className="text-xs text-text-muted">Nothing learned yet: records appear only after experiments are evaluated.</p> : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-[11px] text-text-secondary">
                <thead className="text-[10px] uppercase tracking-wide text-text-muted"><tr><th className="py-1 pr-2">Recorded</th><th className="pr-2">Problem</th><th className="pr-2">Strategy</th><th className="pr-2">Result</th><th className="pr-2">Measured</th><th className="pr-2">Evidence</th><th className="pr-2">Final</th><th>Context and scope</th></tr></thead>
                <tbody>{mem.map((m) => (
                  <tr key={m.id} className="border-t border-border-subtle align-top">
                    <td className="py-1 pr-2">{new Date(m.recorded_at).toLocaleString()}</td><td className="pr-2">{label(m.category)}</td><td className="pr-2">{label(m.strategy)}</td>
                    <td className="pr-2"><Badge value={m.result} />{m.failure_kind && <div><Badge value={m.failure_kind} /></div>}</td>
                    <td className="pr-2">{m.measured?.median_change_pct != null ? `${m.measured.median_change_pct}% (${m.measured.repetitions} reps)` : '—'}</td>
                    <td className="pr-2"><Badge value={m.evidence_quality} /></td><td className="pr-2"><Badge value={m.final_outcome} /></td>
                    <td className="text-text-muted">{Object.entries(m.context || {}).map(([k, v]) => `${k}: ${v}`).join(' · ')}<div>{m.scope}</div>{m.reasons.length > 0 && <div className="text-amber-200">{m.reasons.slice(0, 2).join('; ')}</div>}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </Card>
      </>)}
    </div>
  );
}
