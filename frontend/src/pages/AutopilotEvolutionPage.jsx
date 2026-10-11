import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { FaCheck, FaSearch, FaStop, FaSync, FaTimes, FaPlay, FaShieldAlt, FaChevronDown, FaChevronRight } from 'react-icons/fa';
import {
  cancelExecution, createPlan, decidePlan, executePlan, getExecution, getExecutionReport, getLatestAnalysis,
  listAutopilotProjects, listExecutions, listFindings, listPlans, setFindingDismissed, startAnalysis,
} from '../services/evolutionAutopilot';

const TONE = {
  critical: 'bg-rose-500/20 text-rose-200 border-rose-500/40',
  high: 'bg-orange-500/15 text-orange-200 border-orange-500/30',
  medium: 'bg-amber-500/15 text-amber-200 border-amber-500/30',
  low: 'bg-sky-500/10 text-sky-200 border-sky-500/25',
  info: 'bg-slate-800 text-slate-300 border-slate-700',
  passed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  done: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  ran: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  approved: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  applied: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  fixed_verified: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  failed: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  rejected: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  fix_failed: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  error: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  blocked: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  unavailable: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  partial: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  needs_approval: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  awaiting_approval: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  out_of_scope: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  running: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  queued: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  planned: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
};
const ACTIVE = new Set(['queued', 'running']);
const label = (s) => String(s ?? '').replace(/_/g, ' ');

function Badge({ value, title }) {
  return (
    <span title={title} className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${TONE[value] || 'bg-slate-800 text-slate-400 border-slate-700'}`}>
      {ACTIVE.has(value) && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
      {label(value)}
    </span>
  );
}

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

const Stat = ({ label: l, value }) => (
  <div className="rounded-xl bg-bg-base/60 px-3 py-2">
    <p className="text-[10px] uppercase tracking-wide text-text-muted">{l}</p>
    <p className="mt-0.5 text-sm font-semibold text-text-primary">{value}</p>
  </div>
);

const Pre = ({ children, max = 'max-h-64' }) => (
  <pre className={`${max} overflow-auto whitespace-pre-wrap break-words rounded-lg bg-black/50 p-3 font-mono text-[11px] leading-relaxed text-slate-300`}>{children}</pre>
);

// ------------------------------------------------------------------------------------------------

function AnalysisPanel({ analysis, activeJob, onAnalyze, busy }) {
  const [runTests, setRunTests] = useState(false);
  const m = analysis?.project_map || {};
  const s = analysis?.summary || {};
  return (
    <Card title="Analysis" actions={
      <div className="flex items-center gap-3">
        <label className="flex items-center gap-1.5 text-[11px] text-text-secondary" title="Tests run only in the Docker sandbox; without Docker they are reported as blocked.">
          <input type="checkbox" checked={runTests} onChange={(e) => setRunTests(e.target.checked)} /> run tests (sandbox)
        </label>
        <Btn tone="primary" disabled={busy || !!activeJob} onClick={() => onAnalyze(runTests)}>
          <FaSync className={`h-2.5 w-2.5 ${ACTIVE.has(analysis?.status) ? 'animate-spin' : ''}`} /> Analyze
        </Btn>
      </div>
    }>
      {!analysis && <p className="text-xs text-text-muted">No analysis yet. Analysis reads the code and runs static tools (parser, ruff, Bandit, secret scanner); it never runs the project on this machine.</p>}
      {analysis && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-text-muted">
            <Badge value={analysis.status} />
            <span>started {analysis.started_at ? new Date(analysis.started_at).toLocaleString() : '-'}</span>
            {analysis.finished_at && <span>finished {new Date(analysis.finished_at).toLocaleTimeString()}</span>}
          </div>
          {analysis.error && <p className="text-xs text-rose-300">{analysis.error}</p>}
          {analysis.status === 'completed' && (
            <>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
                <Stat label="Findings" value={s.total ?? 0} />
                <Stat label="Open" value={s.open ?? 0} />
                <Stat label="P1 / P2" value={`${s.by_priority?.P1 ?? 0} / ${s.by_priority?.P2 ?? 0}`} />
                <Stat label="Critical / High" value={`${s.by_severity?.critical ?? 0} / ${s.by_severity?.high ?? 0}`} />
                <Stat label="Resolved since last" value={s.resolved_since_last ?? 0} />
                <Stat label="Files scanned" value={`${m.file_count ?? 0}${m.truncated ? '+' : ''}`} />
              </div>
              <div className="grid gap-3 lg:grid-cols-2">
                <div>
                  <p className="mb-1 text-[10px] uppercase tracking-wide text-text-muted">Project map</p>
                  <ul className="space-y-0.5 text-xs text-text-secondary">
                    <li>Stack: <span className="text-text-primary">{(m.stack || []).join(', ') || 'unknown'}</span></li>
                    <li>Entry points: <span className="font-mono text-text-primary">{(m.entry_points || []).join(', ') || 'none found'}</span></li>
                    <li>Routes: {m.routes?.length ?? 0} · Models: {m.models?.length ?? 0} · Components: {m.components?.length ?? 0} · Frontend API calls: {m.api_calls?.length ?? 0}</li>
                    <li>Test files: {m.tests?.length ?? 0} · Manifests: {Object.keys(m.manifests || {}).join(', ') || 'none'}</li>
                    {m.unparseable?.length > 0 && <li className="text-rose-300">Unparseable: {m.unparseable.join(', ')}</li>}
                  </ul>
                </div>
                <div>
                  <p className="mb-1 text-[10px] uppercase tracking-wide text-text-muted">Tools that ran</p>
                  <ul className="space-y-1">
                    {(analysis.tools || []).map((t, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs">
                        <Badge value={t.status} />
                        <span className="text-text-secondary"><span className="text-text-primary">{t.tool}</span> — {t.detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </Card>
  );
}

// ------------------------------------------------------------------------------------------------

const FILTERS = {
  priority: ['P1', 'P2', 'P3', 'P4'],
  severity: ['critical', 'high', 'medium', 'low', 'info'],
  category: ['syntax', 'quality', 'tests', 'dependencies', 'security', 'maintainability', 'performance'],
  status: ['open', 'planned', 'fix_failed', 'fixed_verified', 'resolved', 'dismissed'],
};
const PAGE = 25;

function FindingRow({ f, selected, onToggle, onDismiss }) {
  const [open, setOpen] = useState(false);
  const selectable = ['open', 'fix_failed'].includes(f.status);
  return (
    <li className="rounded-xl border border-border-subtle bg-bg-base/40">
      <div className="flex items-start gap-2 px-3 py-2">
        <input type="checkbox" className="mt-1" disabled={!selectable} checked={selected} onChange={() => onToggle(f.id)}
               title={selectable ? 'Select for a plan' : 'Only open findings can be planned'} />
        <button onClick={() => setOpen((v) => !v)} className="mt-1 text-text-muted hover:text-text-primary">
          {open ? <FaChevronDown className="h-2.5 w-2.5" /> : <FaChevronRight className="h-2.5 w-2.5" />}
        </button>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="rounded bg-surface-elevated px-1.5 py-0.5 font-mono text-[10px] text-text-primary" title={(f.priority_reasons || []).join('\n')}>{f.priority}</span>
            <Badge value={f.severity} />
            <span className="text-[10px] uppercase tracking-wide text-text-muted">{f.category} · {f.confidence}</span>
            {f.status !== 'open' && <Badge value={f.status} />}
          </div>
          <p className="mt-1 break-words text-xs text-text-primary">{f.title}</p>
          {f.file && <p className="font-mono text-[10px] text-text-muted">{f.file}{f.line_start ? `:${f.line_start}` : ''}</p>}
        </div>
        {f.status === 'dismissed'
          ? <Btn onClick={() => onDismiss(f.id, false)}>Reopen</Btn>
          : ['open', 'fix_failed'].includes(f.status) && <Btn onClick={() => onDismiss(f.id, true)}>Dismiss</Btn>}
      </div>
      {open && (
        <div className="space-y-2 border-t border-border-subtle px-3 py-2 text-xs text-text-secondary">
          <p>{f.description}</p>
          {f.evidence && <Pre max="max-h-40">{f.evidence}</Pre>}
          <p><span className="text-text-muted">Fix: </span>{f.remediation || '-'} <span className="text-text-muted">({f.fix_strategy === 'manual' ? 'needs a person' : `automatic: ${label(f.fix_strategy)}`})</span></p>
          <p><span className="text-text-muted">Verified by: </span>{f.validation || '-'}</p>
          <p className="text-[10px] text-text-muted">Rule {f.rule_id} · {f.analyzer} · first seen {new Date(f.first_seen).toLocaleString()} · priority: {(f.priority_reasons || []).join(', ')}</p>
        </div>
      )}
    </li>
  );
}

function FindingsExplorer({ projectId, version, onPlanned, onError }) {
  const [filters, setFilters] = useState({ status: 'open,fix_failed' });
  const [q, setQ] = useState('');
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState({ items: [], total: 0 });
  const [selected, setSelected] = useState(new Set());
  const [objective, setObjective] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const params = { ...filters, offset, limit: PAGE };
      if (q.trim()) params.q = q.trim();
      setPage(await listFindings(projectId, params));
    } catch (e) { onError(e?.error || 'Could not load findings.'); }
  }, [projectId, filters, q, offset, onError]);
  useEffect(() => { load(); }, [load, version]);
  useEffect(() => { setSelected(new Set()); setOffset(0); }, [projectId]);

  const toggle = (id) => setSelected((s) => {
    const n = new Set(s);
    if (n.has(id)) n.delete(id); else n.add(id);
    return n;
  });
  const dismiss = async (id, dismissed) => {
    try { await setFindingDismissed(projectId, id, dismissed); setSelected((s) => { const n = new Set(s); n.delete(id); return n; }); load(); }
    catch (e) { onError(e?.error || 'Could not update the finding.'); }
  };
  const plan = async () => {
    setBusy(true);
    try {
      const res = await createPlan(projectId, [...selected], objective);
      setSelected(new Set()); setObjective('');
      onPlanned(res.plan); load();
    } catch (e) { onError(e?.error || 'Could not create the plan.'); }
    finally { setBusy(false); }
  };
  const setFilter = (key, value) => { setOffset(0); setFilters((f) => ({ ...f, [key]: value || undefined })); };

  return (
    <Card title={`Findings (${page.total})`} actions={
      <div className="flex flex-wrap items-center gap-2">
        {Object.entries(FILTERS).map(([key, values]) => (
          <select key={key} value={filters[key] || ''} onChange={(e) => setFilter(key, e.target.value)}
                  className="rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-[11px] text-text-secondary">
            <option value="">{key}: any</option>
            {key === 'status' && <option value="open,fix_failed">status: needs work</option>}
            {values.map((v) => <option key={v} value={v}>{label(v)}</option>)}
          </select>
        ))}
        <div className="flex items-center gap-1 rounded-lg border border-border-dark bg-bg-base px-2">
          <FaSearch className="h-2.5 w-2.5 text-text-muted" />
          <input value={q} onChange={(e) => { setOffset(0); setQ(e.target.value); }} placeholder="search"
                 className="w-28 bg-transparent py-1 text-[11px] text-text-primary outline-none" />
        </div>
      </div>
    }>
      {page.items.length === 0 && <p className="text-xs text-text-muted">No findings match.</p>}
      <ul className="space-y-1.5">
        {page.items.map((f) => <FindingRow key={f.id} f={f} selected={selected.has(f.id)} onToggle={toggle} onDismiss={dismiss} />)}
      </ul>
      {page.total > PAGE && (
        <div className="mt-2 flex items-center justify-end gap-2 text-[11px] text-text-muted">
          <Btn disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Prev</Btn>
          <span>{offset + 1}–{Math.min(offset + PAGE, page.total)} of {page.total}</span>
          <Btn disabled={offset + PAGE >= page.total} onClick={() => setOffset(offset + PAGE)}>Next</Btn>
        </div>
      )}
      {selected.size > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-accent-blue/40 bg-accent-blue/10 p-2">
          <span className="text-xs text-text-primary">{selected.size} selected</span>
          <input value={objective} onChange={(e) => setObjective(e.target.value)} placeholder="Objective (optional)"
                 className="min-w-0 flex-1 rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-xs text-text-primary outline-none" />
          <Btn tone="primary" disabled={busy || selected.size > 40} onClick={plan}>Propose plan</Btn>
        </div>
      )}
    </Card>
  );
}

// ------------------------------------------------------------------------------------------------

function PlanPanel({ projectId, plan, lastExecution, onChanged, onExecuted, onError }) {
  const [runTests, setRunTests] = useState(true);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  if (!plan) return null;
  const extra = lastExecution?.plan_id === plan.id && lastExecution.status === 'needs_approval'
    ? [...new Set((lastExecution.task_results || []).filter((r) => r.status === 'out_of_scope').flatMap((r) => (r.outside?.length ? r.outside : r.files)))] : [];

  const act = async (fn) => {
    setBusy(true);
    try { await fn(); } catch (e) { onError(e?.error || 'Request failed.'); } finally { setBusy(false); }
  };
  const decide = (decision, body = {}) => act(async () => onChanged((await decidePlan(projectId, plan.id, decision, { note, ...body })).plan));
  const execute = () => act(async () => onExecuted((await executePlan(projectId, plan.id, runTests)).execution));
  const status = plan.status;

  return (
    <Card title="Improvement plan" actions={<Badge value={status} />}>
      <div className="space-y-3 text-xs text-text-secondary">
        <p className="text-sm text-text-primary">{plan.objective}</p>
        <ol className="space-y-1.5">
          {plan.tasks.map((t) => (
            <li key={t.id} className="rounded-lg bg-bg-base/60 px-3 py-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-[10px] text-text-muted">{t.id}</span>
                <span className="text-text-primary">{t.title}</span>
                {t.depends_on?.length > 0 && <span className="text-[10px] text-text-muted">after {t.depends_on.join(', ')}</span>}
              </div>
              <p className="mt-0.5 whitespace-pre-wrap">{t.modification}</p>
              <p className="mt-0.5 text-[10px] text-text-muted">{t.agent} · files: <span className="font-mono">{t.files.join(', ') || '-'}</span></p>
            </li>
          ))}
        </ol>
        <div className="grid gap-3 md:grid-cols-2">
          <div><p className="text-[10px] uppercase tracking-wide text-text-muted">Files that may change</p><p className="font-mono">{plan.expected_files.join(', ') || 'none'}</p></div>
          <div><p className="text-[10px] uppercase tracking-wide text-text-muted">Checks</p><p>{plan.checks.join(', ')}</p></div>
          <div><p className="text-[10px] uppercase tracking-wide text-text-muted">Risks</p>{plan.risks.length ? <ul className="list-disc pl-4">{plan.risks.map((r, i) => <li key={i}>{r}</li>)}</ul> : <p>None beyond the checks below (deterministic fixes only).</p>}</div>
          <div><p className="text-[10px] uppercase tracking-wide text-text-muted">Assumptions</p><ul className="list-disc pl-4">{plan.assumptions.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
          <div><p className="text-[10px] uppercase tracking-wide text-text-muted">Your approval covers</p><ul className="list-disc pl-4">{plan.approval_required.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
          <div><p className="text-[10px] uppercase tracking-wide text-text-muted">Done when</p><ul className="list-disc pl-4">{plan.completion_criteria.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
        </div>
        {extra.length > 0 && (
          <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-amber-200">
            The last run needed files outside this plan: <span className="font-mono">{extra.join(', ')}</span>. Approving again with them allows those files.
          </p>
        )}
        {plan.decisions?.length > 0 && (
          <p className="text-[10px] text-text-muted">{plan.decisions.map((d) => `${label(d.decision)} by ${d.user_id} ${new Date(d.at).toLocaleString()}${d.note ? ` — ${d.note}` : ''}`).join(' · ')}</p>
        )}
        <div className="flex flex-wrap items-center gap-2 border-t border-border-subtle pt-3">
          {['awaiting_approval', 'draft'].includes(status) && (
            <>
              <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note (optional)"
                     className="min-w-0 flex-1 rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-xs text-text-primary outline-none" />
              <Btn tone="good" disabled={busy} onClick={() => decide('approve', extra.length ? { extra_files: extra } : {})}>
                <FaCheck className="h-2.5 w-2.5" /> {extra.length ? 'Approve with extra files' : 'Approve'}
              </Btn>
              <Btn tone="bad" disabled={busy} onClick={() => decide('reject')}><FaTimes className="h-2.5 w-2.5" /> Reject</Btn>
            </>
          )}
          {status === 'approved' && (
            <>
              <label className="flex items-center gap-1.5 text-[11px]" title="Tests run only in the Docker sandbox. Without Docker the test check is blocked and acceptance rests on static checks.">
                <input type="checkbox" checked={runTests} onChange={(e) => setRunTests(e.target.checked)} /> run tests (sandbox)
              </label>
              <Btn tone="primary" disabled={busy} onClick={execute}><FaPlay className="h-2.5 w-2.5" /> Execute</Btn>
              <Btn disabled={busy} onClick={() => decide('cancel')}>Cancel plan</Btn>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}

// ------------------------------------------------------------------------------------------------

function CheckTable({ baseline, after }) {
  const ids = [...new Set([...(baseline || []), ...(after || [])].map((c) => c.check_id))];
  const find = (list, id) => (list || []).find((c) => c.check_id === id);
  const counts = (c) => (c && Object.keys(c.counts || {}).length ? Object.entries(c.counts).map(([k, v]) => `${k} ${v}`).join(', ') : '');
  return (
    <table className="w-full text-left text-xs">
      <thead className="text-[10px] uppercase tracking-wide text-text-muted">
        <tr><th className="py-1 pr-2">Check</th><th className="pr-2">Before</th><th className="pr-2">After</th><th>Where</th></tr>
      </thead>
      <tbody>
        {ids.map((id) => {
          const b = find(baseline, id); const a = find(after, id);
          return (
            <tr key={id} className="border-t border-border-subtle align-top">
              <td className="py-1.5 pr-2 text-text-primary">{(a || b)?.label}</td>
              <td className="pr-2">{b ? <><Badge value={b.status} /> <span className="text-[10px] text-text-muted">{counts(b)}</span></> : '-'}</td>
              <td className="pr-2">{a ? <><Badge value={a.status} /> <span className="text-[10px] text-text-muted">{counts(a)}</span></> : '-'}</td>
              <td className="text-[10px] text-text-muted">{(a || b)?.environment}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function ExecutionPanel({ projectId, execution, onUpdate, onError }) {
  const [report, setReport] = useState(null);
  const [showDiff, setShowDiff] = useState(false);
  const active = execution && ACTIVE.has(execution.status);

  useEffect(() => {
    if (!execution) return undefined;
    let stop = false;
    const tick = async () => {
      try {
        const e = (await getExecution(projectId, execution.id)).execution;
        if (stop) return;
        onUpdate(e);
        if (!ACTIVE.has(e.status)) setReport((await getExecutionReport(projectId, e.id)).report);
      } catch (err) { onError(err?.error || 'Could not load the execution.'); }
    };
    tick();
    if (!active) return () => { stop = true; };
    const t = setInterval(tick, 2500);
    return () => { stop = true; clearInterval(t); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, execution?.id, active]);

  if (!execution) return null;
  const verdict = execution.verdict || {};
  return (
    <Card title="Execution" actions={
      <div className="flex items-center gap-2">
        <Badge value={execution.status} />
        {active && <Btn tone="bad" disabled={execution.cancel_requested} onClick={() => cancelExecution(projectId, execution.id).catch((e) => onError(e?.error))}>
          <FaStop className="h-2.5 w-2.5" /> {execution.cancel_requested ? 'Cancelling…' : 'Cancel'}
        </Btn>}
      </div>
    }>
      <div className="space-y-3 text-xs text-text-secondary">
        <ol className="grid gap-1.5 sm:grid-cols-2 lg:grid-cols-4">
          {(execution.stages || []).map((s) => (
            <li key={s.name} className="rounded-lg bg-bg-base/60 px-3 py-2">
              <div className="flex items-center justify-between gap-2"><span className="text-text-primary">{s.name}</span><Badge value={s.status} /></div>
              {s.detail && <p className="mt-1 break-words text-[10px] text-text-muted">{s.detail}</p>}
            </li>
          ))}
        </ol>
        {execution.task_results?.length > 0 && (
          <ul className="space-y-1">
            {execution.task_results.map((r) => (
              <li key={r.task_id} className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-[10px] text-text-muted">{r.task_id}</span><Badge value={r.status} />
                <span className="font-mono text-[10px]">{(r.files || []).join(', ')}</span>
                {r.detail && <span className="text-[10px] text-text-muted">{r.detail}</span>}
              </li>
            ))}
          </ul>
        )}
        {(execution.baseline?.length > 0 || execution.after?.length > 0) && <CheckTable baseline={execution.baseline} after={execution.after} />}
        {verdict.evidence && (
          <div className={`rounded-lg border p-2 ${verdict.accepted ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-rose-500/30 bg-rose-500/10'}`}>
            <p className="flex items-center gap-1.5 text-text-primary"><FaShieldAlt className="h-3 w-3" /> {verdict.accepted ? 'Accepted' : 'Rejected'} — evidence: {verdict.evidence}</p>
            {[...(verdict.regressions || []), ...(verdict.unverified || [])].map((r, i) => <p key={i} className="text-rose-200">• {r}</p>)}
            {(verdict.notes || []).map((r, i) => <p key={i} className="text-text-muted">• {r}</p>)}
          </div>
        )}
        {execution.error && <p className="text-rose-300">{execution.error}</p>}
        {report && (
          <div className="space-y-1">
            <p className="text-text-primary">{report.statement}</p>
            {report.verified_findings?.length > 0 && <p><span className="text-emerald-300">Verified fixed:</span> {report.verified_findings.map((f) => f.title || f.id).join('; ')}</p>}
            {report.unresolved_findings?.length > 0 && <p><span className="text-amber-300">Still detected:</span> {report.unresolved_findings.map((f) => f.title || f.id).join('; ')}</p>}
            {report.checks?.not_executed?.length > 0 && <p className="text-amber-200">Not executed: {report.checks.not_executed.map((c) => `${c.check} (${label(c.status)})`).join(', ')}</p>}
          </div>
        )}
        {execution.diff && (
          <div>
            <Btn onClick={() => setShowDiff((v) => !v)}>{showDiff ? 'Hide' : 'Show'} diff ({execution.changed_files.length} file{execution.changed_files.length === 1 ? '' : 's'})</Btn>
            {showDiff && <div className="mt-2"><Pre max="max-h-96">{execution.diff}</Pre></div>}
          </div>
        )}
      </div>
    </Card>
  );
}

// ------------------------------------------------------------------------------------------------

/**
 * AIForge Autopilot: analyze a generated project, review evidence-backed findings, approve a plan,
 * and watch it run in an isolated copy. Everything shown comes from the Autopilot API; checks that
 * could not run are shown as blocked, never as passed.
 */
export default function AutopilotEvolutionPage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [activeJob, setActiveJob] = useState(null);
  const [plans, setPlans] = useState([]);
  const [planId, setPlanId] = useState('');
  const [execution, setExecution] = useState(null);
  const [version, setVersion] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

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
      const [a, p, ex] = await Promise.all([getLatestAnalysis(projectId), listPlans(projectId), listExecutions(projectId)]);
      setAnalysis(a.analysis); setActiveJob(a.active_job);
      setPlans(p.plans || []);
      setPlanId((cur) => cur || p.plans?.[0]?.id || '');
      const latest = ex.executions?.[0];
      setExecution((cur) => (cur && cur.project_id === projectId ? cur : latest || null));
    } catch (e) { setError(e?.error || 'Could not load Autopilot data.'); }
  }, [projectId]);

  useEffect(() => { setAnalysis(null); setPlans([]); setPlanId(''); setExecution(null); setError(''); refresh(); }, [projectId, refresh]);
  useEffect(() => {
    if (!ACTIVE.has(analysis?.status)) return undefined;
    const t = setInterval(async () => { await refresh(); setVersion((v) => v + 1); }, 2500);
    return () => clearInterval(t);
  }, [analysis?.status, refresh]);

  const analyze = async (runTests) => {
    setBusy(true); setError('');
    try { setAnalysis((await startAnalysis(projectId, runTests)).analysis); }
    catch (e) { setError(e?.error || 'Could not start the analysis.'); }
    finally { setBusy(false); }
  };
  const plan = useMemo(() => plans.find((p) => p.id === planId) || null, [plans, planId]);
  const upsertPlan = (p) => { setPlans((ps) => [p, ...ps.filter((x) => x.id !== p.id)]); setPlanId(p.id); };
  const onExecutionUpdate = useCallback((e) => {
    setExecution(e);
    if (!ACTIVE.has(e.status)) {
      refresh();
      setVersion((v) => v + 1);
    }
  }, [refresh]);

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-text-primary">AIForge Autopilot</h1>
          <p className="text-xs text-text-muted">Evidence-based findings, plans you approve, and changes that are kept only when the checks hold.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)}
                className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {!projectId && projects.length === 0 && (
        <Card><p className="text-xs text-text-muted">Generate a project first; Autopilot works on projects you own.</p></Card>
      )}
      {projectId && (
        <>
          <AnalysisPanel analysis={analysis} activeJob={activeJob} onAnalyze={analyze} busy={busy} />
          {analysis?.status === 'completed' && (
            <FindingsExplorer projectId={projectId} version={version} onPlanned={upsertPlan} onError={setError} />
          )}
          {plans.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 text-xs text-text-secondary">
              <span className="text-[10px] uppercase tracking-wide text-text-muted">Plans</span>
              {plans.slice(0, 8).map((p) => (
                <button key={p.id} onClick={() => setPlanId(p.id)}
                        className={`flex items-center gap-1.5 rounded-lg border px-2 py-1 ${p.id === planId ? 'border-accent-blue bg-accent-blue/10' : 'border-border-dark hover:bg-surface-hover'}`}>
                  <span className="max-w-[14rem] truncate">{p.objective}</span><Badge value={p.status} />
                </button>
              ))}
            </div>
          )}
          <PlanPanel projectId={projectId} plan={plan} lastExecution={execution} onChanged={upsertPlan}
                     onExecuted={(e) => { setExecution(e); setPlans((ps) => ps.map((p) => (p.id === e.plan_id ? { ...p, status: 'running' } : p))); }}
                     onError={setError} />
          <ExecutionPanel projectId={projectId} execution={execution} onUpdate={onExecutionUpdate} onError={setError} />
        </>
      )}
    </div>
  );
}
