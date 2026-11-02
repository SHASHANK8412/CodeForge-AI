import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { FaCheck, FaChevronDown, FaChevronRight, FaDownload, FaPlay, FaShieldAlt, FaStop, FaTimes, FaUserShield } from 'react-icons/fa';
import {
  abortGuardianJob, acceptGuardianRisk, compareGuardianAssessments, createGuardianPlan, getGuardianAssessment, getGuardianGate,
  getGuardianReport, listGuardianAssessments, listGuardianFindings, startGuardianAssessment, verifyGuardianFindings,
} from '../services/guardian';
import { decidePlan, executePlan, listAutopilotProjects, listExecutions, listPlans } from '../services/evolutionAutopilot';

const GOOD = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
const BAD = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
const WARN = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
const GREY = 'bg-slate-700/50 text-slate-300 border-slate-600';
const TONE = {
  completed: GOOD, ran: GOOD, improved: GOOD, fix_verified: GOOD, approved: GOOD, done: GOOD, not_reproduced: GREY,
  fixed: 'bg-teal-500/15 text-teal-300 border-teal-500/30',
  failed: BAD, error: BAD, regressed: BAD, rejected: BAD, verified: BAD,
  critical: 'bg-rose-500/20 text-rose-200 border-rose-500/40', high: 'bg-orange-500/15 text-orange-200 border-orange-500/30',
  medium: WARN, low: 'bg-sky-500/10 text-sky-200 border-sky-500/25', info: GREY,
  P1: 'bg-rose-500/20 text-rose-200 border-rose-500/40', P2: 'bg-orange-500/15 text-orange-200 border-orange-500/30', P3: WARN, P4: GREY,
  detected: WARN, requires_review: WARN, inconclusive: WARN, partial: WARN, unavailable: GREY, verification_unavailable: GREY,
  not_measured: GREY, aborted: GREY, skipped: GREY, accepted_risk: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
  awaiting_approval: 'bg-violet-500/15 text-violet-300 border-violet-500/30', public: BAD, authenticated: GREY,
};
const ACTIVE = new Set(['queued', 'analyzing', 'verifying', 'running', 'verification_in_progress']);
const SEVERITIES = ['critical', 'high', 'medium', 'low', 'info'];
const CATEGORIES = ['injection', 'auth', 'secrets', 'web', 'dependencies', 'crypto', 'configuration'];
const STATES = ['detected', 'requires_review', 'verified', 'not_reproduced', 'verification_unavailable', 'fixed', 'fix_verified', 'accepted_risk'];
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
const Pre = ({ children }) => <pre className="max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-black/50 p-3 font-mono text-[11px] text-slate-300">{children}</pre>;
const Stat = ({ name, value }) => (
  <div className="rounded-xl bg-bg-base/60 px-3 py-2"><p className="text-[10px] uppercase tracking-wide text-text-muted">{name}</p><p className="mt-0.5 text-sm font-semibold text-text-primary">{value}</p></div>
);
const download = (name, content, type) => {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

// --- overview ------------------------------------------------------------------------------------------------

function Overview({ a, activeJob, busy, onStart, onAbort, onExport }) {
  const s = a?.summary || {};
  return (
    <Card title="Security overview" actions={<div className="flex flex-wrap items-center gap-2">
      {a && <Badge value={a.status} />}
      {activeJob ? <Btn tone="bad" disabled={busy} onClick={onAbort}><FaStop className="h-2.5 w-2.5" /> Abort running job</Btn>
        : <Btn tone="primary" disabled={busy} onClick={onStart}><FaPlay className="h-2.5 w-2.5" /> Run assessment</Btn>}
      {a?.status === 'completed' && <>
        <Btn disabled={busy} onClick={() => onExport('markdown')}><FaDownload className="h-2.5 w-2.5" /> Report (Markdown)</Btn>
        <Btn disabled={busy} onClick={() => onExport('json')}><FaDownload className="h-2.5 w-2.5" /> Report (JSON)</Btn>
      </>}
    </div>}>
      <div className="space-y-3 text-xs text-text-secondary">
        <p className="text-[11px] text-text-muted">An assessment reads the project (no code is run). Verification is a separate, approved step that sends benign requests to a disposable copy in an isolated sandbox.</p>
        {!a && <p>No assessment yet for this project. Nothing below is assumed: run one to see findings.</p>}
        {a && <>
          {a.error && <p className="text-amber-200">{a.error}</p>}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-6">
            <Stat name="Open findings" value={s.open ?? '—'} />
            <Stat name="Critical / high open" value={s.critical_high_open ?? '—'} />
            <Stat name="Verified (open)" value={s.verified_open ?? '—'} />
            <Stat name="Fixed, awaiting re-check" value={s.awaiting_verification ?? '—'} />
            <Stat name="Accepted risks" value={s.accepted_risks ?? '—'} />
            <Stat name="Total" value={s.total ?? '—'} />
          </div>
          <div className="flex flex-wrap gap-1.5">{Object.entries(s.by_category || {}).map(([c, n]) => <span key={c} className="rounded-lg border border-border-subtle px-2 py-0.5 text-[11px]">{label(c)}: <span className="text-text-primary">{n}</span></span>)}</div>
          <div>
            <p className="mb-1 text-[10px] uppercase tracking-wide text-text-muted">Tools</p>
            <ul className="space-y-0.5">{a.tools.map((t) => (
              <li key={t.tool}><Badge value={t.status} /> <span className="text-text-primary">{t.tool}</span>{t.version && <span className="text-text-muted"> {t.version}</span>} — {t.detail}{t.retrieved_at && <span className="text-text-muted"> (advisories retrieved {new Date(t.retrieved_at).toLocaleString()})</span>}</li>
            ))}</ul>
          </div>
          {a.coverage?.not_covered?.length > 0 && <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-amber-100">
            <p className="mb-0.5 font-semibold">Not covered — an empty result here does not mean the project is secure</p>
            <ul className="list-disc pl-4">{a.coverage.not_covered.map((x, i) => <li key={i}>{x}</li>)}</ul>
          </div>}
          {a.coverage?.files_read != null && <p className="text-[11px] text-text-muted">Read {a.coverage.files_read} file(s){a.coverage.languages?.length ? ` (${a.coverage.languages.join(', ')})` : ''}; routes behind authentication: {a.coverage.auth?.protected_routes?.length ?? 0}.</p>}
        </>}
      </div>
    </Card>
  );
}

// --- findings explorer -----------------------------------------------------------------------------------------

function FindingRow({ f, picked, onPick, onAccept, onPlan, busy }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState('');
  const closed = ['fix_verified', 'accepted_risk'].includes(f.state);
  return (
    <li className="rounded-xl border border-border-subtle bg-bg-base/40">
      <div className="flex items-start gap-2 px-3 py-2">
        <input type="checkbox" className="mt-1" aria-label={`select ${f.title} for verification`} disabled={!f.verifiable || closed} checked={picked} onChange={(e) => onPick(f.id, e.target.checked)} />
        <button className="flex min-w-0 flex-1 flex-wrap items-center gap-1.5 text-left" onClick={() => setOpen((v) => !v)}>
          {open ? <FaChevronDown className="h-2.5 w-2.5 text-text-muted" /> : <FaChevronRight className="h-2.5 w-2.5 text-text-muted" />}
          <Badge value={f.priority} /><Badge value={f.severity} /><Badge value={f.state} />
          <span className="text-xs text-text-primary">{f.title}</span>
          <span className="font-mono text-[10px] text-text-muted">{f.file}{f.line ? `:${f.line}` : ''}{f.route ? ` · ${f.route}` : ''}</span>
          {f.context?.exposure && <Badge value={f.context.exposure} />}
        </button>
      </div>
      {open && (
        <div className="space-y-2 border-t border-border-subtle px-3 py-2 text-xs text-text-secondary">
          <p>{f.description}</p>
          <p><span className="text-text-muted">Rule </span><span className="font-mono">{f.rule_id}</span> · {label(f.category)} · confidence {f.confidence} · detected by {f.detection.join(', ')}{f.references.length ? ` · ${f.references.join(', ')}` : ''}</p>
          <p><span className="text-text-muted">Impact: </span>{f.impact}</p>
          <p><span className="text-text-muted">Priority reasons: </span>{f.priority_reasons.join('; ')}</p>
          <div><p className="text-[10px] uppercase tracking-wide text-text-muted">Evidence (secrets redacted)</p>
            <ul className="space-y-0.5">{f.evidence.map((e, i) => <li key={i}><span className="font-mono text-text-muted">{e.source}{e.line ? ` @${e.line}` : ''}</span> — <span className="font-mono">{e.detail}</span></li>)}</ul></div>
          {f.context?.dependents?.length > 0 && <p><span className="text-text-muted">Depends on this file (Digital Twin): </span><span className="font-mono">{f.context.dependents.join(', ')}</span></p>}
          {f.dependencies?.length > 0 && <p><span className="text-text-muted">Packages: </span>{f.dependencies.join(', ')}</p>}
          <p><span className="text-text-muted">Remediation: </span>{f.remediation}</p>
          {f.verification && f.verification.method !== '-' && (
            <div className="rounded-lg border border-border-subtle p-2">
              <p className="flex flex-wrap items-center gap-2"><span className="text-text-muted">Safe verification</span><Badge value={f.verification.status} />{f.last_verified && <span className="text-[10px] text-text-muted">{new Date(f.last_verified).toLocaleString()}</span>}</p>
              <p className="mt-0.5"><span className="text-text-muted">Method: </span>{f.verification.method}</p>
              <p><span className="text-text-muted">Conclusion: </span><span className="text-text-primary">{f.verification.conclusion}</span></p>
              {f.verification.requests.length > 0 && <Pre>{f.verification.requests.map((r) => `${r.purpose}: ${r.request.method} ${r.request.path}${r.request.params ? ' ' + JSON.stringify(r.request.params) : ''} -> ${r.status}\n  ${String(r.body || '').slice(0, 200)}`).join('\n')}</Pre>}
              {f.verification.limitations.length > 0 && <p className="text-[11px] text-text-muted">Limitations: {f.verification.limitations.join('; ')}</p>}
            </div>
          )}
          {!f.verifiable && <p className="text-[11px] text-text-muted">No safe dynamic test exists for this rule; it stays a static finding until a person reviews it.</p>}
          {f.state === 'accepted_risk' && <p className="text-violet-200">Accepted by {f.accepted_by}: {f.accepted_note}</p>}
          {!closed && (
            <div className="flex flex-wrap items-center gap-2">
              <Btn tone="primary" disabled={busy} onClick={() => onPlan(f.id)}>Propose fix (Autopilot plan)</Btn>
              <input className={`${inputCls} w-64`} placeholder="Why is this risk acceptable? (required)" value={note} onChange={(e) => setNote(e.target.value)} />
              <Btn disabled={busy || note.trim().length < 3} onClick={() => onAccept(f.id, note.trim())}><FaUserShield className="h-2.5 w-2.5" /> Accept risk</Btn>
            </div>
          )}
        </div>
      )}
    </li>
  );
}

function Findings({ findings, filters, setFilters, picked, setPicked, busy, onAccept, onPlan }) {
  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });
  return (
    <Card title={`Findings explorer (${findings.length})`}>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <select className={inputCls} value={filters.severity} onChange={set('severity')}><option value="">all severities</option>{SEVERITIES.map((s) => <option key={s}>{s}</option>)}</select>
        <select className={inputCls} value={filters.category} onChange={set('category')}><option value="">all categories</option>{CATEGORIES.map((s) => <option key={s}>{s}</option>)}</select>
        <select className={inputCls} value={filters.state} onChange={set('state')}><option value="">all states</option>{STATES.map((s) => <option key={s} value={s}>{label(s)}</option>)}</select>
        <select className={inputCls} value={filters.priority} onChange={set('priority')}><option value="">all priorities</option>{['P1', 'P2', 'P3', 'P4'].map((s) => <option key={s}>{s}</option>)}</select>
        <input className={`${inputCls} w-40`} placeholder="file prefix" value={filters.file} onChange={set('file')} />
        <input className={`${inputCls} w-44`} placeholder="search" value={filters.q} onChange={set('q')} />
        <label className="flex items-center gap-1 text-[11px] text-text-muted"><input type="checkbox" checked={filters.include_resolved} onChange={(e) => setFilters({ ...filters, include_resolved: e.target.checked })} /> include no longer detected</label>
      </div>
      {findings.length === 0 ? <p className="text-xs text-text-muted">No findings match. This does not mean the code is free of vulnerabilities — see coverage above.</p> : (
        <ul className="space-y-1.5">{findings.map((f) => (
          <FindingRow key={f.id} f={f} busy={busy} picked={picked.includes(f.id)} onAccept={onAccept} onPlan={onPlan}
                      onPick={(id, on) => setPicked(on ? [...picked, id] : picked.filter((x) => x !== id))} />
        ))}</ul>
      )}
    </Card>
  );
}

// --- verification center ---------------------------------------------------------------------------------------

function Verification({ picked, findings, job, busy, onVerify, onAbort, onClear }) {
  const [consent, setConsent] = useState(false);
  const chosen = findings.filter((f) => picked.includes(f.id));
  useEffect(() => { setConsent(false); }, [picked]);
  return (
    <Card title="Verification center">
      <div className="space-y-2 text-xs text-text-secondary">
        <p className="text-[11px] text-text-muted">Selected findings are tested with benign requests (no destructive payloads) against a disposable copy of the app on an internal Docker network with no external route. A rule match alone is never reported as verified.</p>
        {chosen.length === 0 ? <p>Select verifiable findings in the explorer (the checkbox is enabled for rules with a safe test).</p> : (
          <>
            <ul className="list-disc pl-4">{chosen.map((f) => <li key={f.id}>{f.title} <span className="font-mono text-text-muted">{f.route || f.file}</span></li>)}</ul>
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2">
              <label className="flex items-center gap-1.5 text-amber-100"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                I approve running these safe tests against a disposable copy in the isolated sandbox</label>
              <Btn tone="good" disabled={busy || !consent || !!job} onClick={() => onVerify(chosen.map((f) => f.id))}><FaPlay className="h-2.5 w-2.5" /> Verify {chosen.length}</Btn>
              <Btn disabled={busy} onClick={onClear}>Clear selection</Btn>
            </div>
          </>
        )}
        {job && (
          <div className="space-y-1 rounded-lg border border-border-subtle p-2">
            <p className="flex flex-wrap items-center gap-2"><span>{job.verification_requested ? 'Verification' : 'Assessment'} {job.id}</span><Badge value={job.status} />
              {ACTIVE.has(job.status) && <Btn tone="bad" disabled={busy || job.abort_requested} onClick={onAbort}><FaStop className="h-2.5 w-2.5" /> {job.abort_requested ? 'Aborting…' : 'Abort'}</Btn>}</p>
            <Pre>{(job.audit || []).slice(-12).map((x) => `${String(x.at).slice(11, 19)} ${x.action}${x.detail ? ' ' + x.detail : ''}`).join('\n') || 'starting…'}</Pre>
          </div>
        )}
      </div>
    </Card>
  );
}

// --- remediation workspace -------------------------------------------------------------------------------------

function Remediation({ projectId, findings, refreshKey, onChanged, onError }) {
  const [plans, setPlans] = useState([]);
  const [execs, setExecs] = useState([]);
  const [gates, setGates] = useState({});
  const [reviewed, setReviewed] = useState({});
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try {
      const [p, e] = await Promise.all([listPlans(projectId), listExecutions(projectId)]);
      const secPlans = (p.plans || []).filter((x) => x.origin === 'security');
      setPlans(secPlans);
      const ex = (e.executions || []).filter((x) => secPlans.some((pl) => pl.id === x.plan_id));
      setExecs(ex);
      const g = {};
      for (const x of ex.filter((y) => !ACTIVE.has(y.status))) {
        try { g[x.id] = (await getGuardianGate(projectId, x.id)).gate; } catch { /* no gate ran (e.g. correctness checks rejected the change first) */ }
      }
      setGates(g);
    } catch (err) { onError(err?.error || 'Could not load remediations.'); }
  }, [projectId, onError]);
  useEffect(() => { load(); }, [load, refreshKey]);
  useEffect(() => {
    if (!execs.some((x) => ACTIVE.has(x.status))) return undefined;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [execs, load]);
  const act = async (fn) => { setBusy(true); try { await fn(); await load(); onChanged(); } catch (e) { onError(e?.error || 'Request failed.'); } finally { setBusy(false); } };
  const byId = Object.fromEntries(findings.map((f) => [f.id, f]));
  if (plans.length === 0) return (
    <Card title="Remediation workspace"><p className="text-xs text-text-muted">No security fixes proposed yet. Use “Propose fix” on a finding: Autopilot changes an isolated copy, adds a security regression test, runs the project's tests in the sandbox and re-runs the same safe verification before anything is applied.</p></Card>
  );
  return (
    <Card title="Remediation workspace">
      <div className="space-y-2 text-xs text-text-secondary">
        {plans.map((p) => {
          const ex = execs.filter((x) => x.plan_id === p.id).sort((a, b) => (b.started_at || '').localeCompare(a.started_at || ''))[0];
          const g = ex && gates[ex.id];
          const f = byId[p.origin_ref];
          return (
            <div key={p.id} className="rounded-xl border border-border-dark p-3">
              <div className="flex flex-wrap items-center gap-2"><span className="text-text-primary">{p.objective}</span><Badge value={p.status} />{ex && <><span>execution</span><Badge value={ex.status} /></>}{f && <><span>finding</span><Badge value={f.state} /></>}</div>
              <ul className="mt-1 list-disc pl-4">{p.tasks.map((t) => <li key={t.id}>{t.modification || t.title} <span className="font-mono text-text-muted">{t.files.join(', ')}</span></li>)}</ul>
              <p className="text-[11px] text-text-muted">Completion: {p.completion_criteria.join('; ')}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {p.status === 'awaiting_approval' && <>
                  {p.security_review_required && <label className="flex items-center gap-1.5 text-amber-100"><input type="checkbox" checked={!!reviewed[p.id]} onChange={(e) => setReviewed({ ...reviewed, [p.id]: e.target.checked })} /> I reviewed that this changes authentication</label>}
                  <Btn tone="good" disabled={busy || (p.security_review_required && !reviewed[p.id])} onClick={() => act(() => decidePlan(projectId, p.id, 'approve', { security_reviewed: !!reviewed[p.id] }))}><FaCheck className="h-2.5 w-2.5" /> Approve</Btn>
                  <Btn tone="bad" disabled={busy} onClick={() => act(() => decidePlan(projectId, p.id, 'reject'))}><FaTimes className="h-2.5 w-2.5" /> Reject</Btn></>}
                {p.status === 'approved' && <Btn tone="primary" disabled={busy} onClick={() => act(() => executePlan(projectId, p.id, true))}><FaPlay className="h-2.5 w-2.5" /> Fix in an isolated copy, test and re-verify</Btn>}
              </div>
              {ex && <div className="mt-2 space-y-0.5 text-[11px]">
                {ex.stages.map((s) => <p key={s.name}><Badge value={s.status} /> {s.name} <span className="text-text-muted">{(s.detail || '').slice(0, 240)}</span></p>)}
                {ex.error && <p className="text-amber-200">{ex.error}</p>}
                <p><span className="text-text-muted">Applied: </span>{ex.applied_to_project ? 'yes — after the tests and the security re-check passed' : ACTIVE.has(ex.status) ? 'in progress' : 'no; the isolated copy was discarded and the project is unchanged'}</p>
                {ex.diff && <details><summary className="cursor-pointer text-text-muted">Diff</summary><Pre>{ex.diff}</Pre></details>}
              </div>}
              {g && <div className="mt-2 text-[11px]">
                <p className="flex items-center gap-2"><span className="text-text-muted">Security re-check (original vs changed copy):</span><Badge value={g.decision} /></p>
                {g.reasons.map((r, i) => <p key={i}>• {r}</p>)}
              </div>}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// --- page --------------------------------------------------------------------------------------------------------

/**
 * AIForge Security Guardian: static analysis and scanners with deduplicated, evidence-backed findings,
 * explicit verification states, approved safe verification in an isolated sandbox, and remediation through
 * Autopilot gated by the same verification. Nothing is shown as verified or fixed without recorded evidence.
 */
export default function SecurityGuardianPage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [history, setHistory] = useState([]);
  const [activeJob, setActiveJob] = useState(null);
  const [job, setJob] = useState(null);
  const [findings, setFindings] = useState([]);
  const [filters, setFilters] = useState({ severity: '', category: '', state: '', priority: '', file: '', q: '', include_resolved: false });
  const [picked, setPicked] = useState([]);
  const [compare, setCompare] = useState({ first: '', second: '' });
  const [comparison, setComparison] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
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

  const params = useMemo(() => Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '' && v !== false)), [filters]);
  const loadFindings = useCallback(async () => {
    if (!projectId) return;
    try { setFindings((await listGuardianFindings(projectId, params)).items || []); } catch (e) { setError(e?.error || 'Could not load findings.'); }
  }, [projectId, params]);
  const refresh = useCallback(async () => {
    if (!projectId) return;
    try {
      const h = await listGuardianAssessments(projectId);
      setHistory(h.assessments || []); setActiveJob(h.active_job || null);
      const jid = h.active_job || h.assessments?.[0]?.id;
      setJob(jid ? (await getGuardianAssessment(projectId, jid)).assessment : null);
    } catch (e) { setError(e?.error || 'Could not load the Security Guardian.'); }
    loadFindings();
  }, [projectId, loadFindings]);
  useEffect(() => { setPicked([]); setComparison(null); setError(''); }, [projectId]);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (!activeJob) return undefined;
    const t = setInterval(refresh, 2500);
    return () => clearInterval(t);
  }, [activeJob, refresh]);

  const latest = history.find((a) => !a.verification_requested) || null;
  const [latestFull, setLatestFull] = useState(null);
  useEffect(() => {
    if (!latest) { setLatestFull(null); return; }
    getGuardianAssessment(projectId, latest.id).then((r) => setLatestFull(r.assessment)).catch(() => setLatestFull(null));
  }, [projectId, latest?.id, latest?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (fn) => { setBusy(true); setError(''); try { await fn(); } catch (e) { setError(e?.error || 'Request failed.'); } finally { setBusy(false); } };
  const exportReport = (format) => act(async () => {
    const r = await getGuardianReport(projectId, format);
    if (format === 'markdown') download(`security-report-${projectId}.md`, r, 'text/markdown');
    else download(`security-report-${projectId}.json`, JSON.stringify(r, null, 2), 'application/json');
  });
  const assessments = history.filter((a) => !a.verification_requested && a.status === 'completed');

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaShieldAlt className="h-4 w-4" /> Security Guardian</h1>
          <p className="text-xs text-text-muted">Evidence-backed findings, safe verification in an isolated sandbox, and fixes that are applied only after they are re-verified.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {projectId && (<>
        <Overview a={latestFull} activeJob={activeJob} busy={busy} onExport={exportReport}
                  onStart={() => act(async () => { await startGuardianAssessment(projectId); await refresh(); })}
                  onAbort={() => act(async () => { await abortGuardianJob(projectId, activeJob); await refresh(); })} />
        <Verification picked={picked} findings={findings} job={job && (ACTIVE.has(job.status) || job.verification_requested) ? job : null} busy={busy}
                      onClear={() => setPicked([])}
                      onVerify={(ids) => act(async () => { await verifyGuardianFindings(projectId, ids); setPicked([]); await refresh(); })}
                      onAbort={() => act(async () => { await abortGuardianJob(projectId, job.id); await refresh(); })} />
        <Findings findings={findings} filters={filters} setFilters={setFilters} picked={picked} setPicked={setPicked} busy={busy}
                  onAccept={(id, note) => act(async () => { await acceptGuardianRisk(projectId, id, note); await refresh(); })}
                  onPlan={(id) => act(async () => { await createGuardianPlan(projectId, id); setRefreshKey((k) => k + 1); })} />
        <Remediation projectId={projectId} findings={findings} refreshKey={refreshKey} onChanged={refresh} onError={onError} />

        {history.length > 0 && (
          <Card title="History">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-[11px] text-text-secondary">
                <thead className="text-[10px] uppercase tracking-wide text-text-muted"><tr><th className="py-1 pr-2">When</th><th className="pr-2">Kind</th><th className="pr-2">Status</th><th className="pr-2">Result</th></tr></thead>
                <tbody>{history.map((h) => (
                  <tr key={h.id} className="border-t border-border-subtle align-top">
                    <td className="py-1 pr-2">{new Date(h.created_at).toLocaleString()}</td>
                    <td className="pr-2">{h.verification_requested ? 'verification' : 'assessment'}</td>
                    <td className="pr-2"><Badge value={h.status} /></td>
                    <td className="pr-2">{h.verification_requested
                      ? Object.values(h.summary || {}).map(label).join(', ') || '—'
                      : `${h.summary?.open ?? '—'} open · ${h.summary?.critical_high_open ?? '—'} critical/high · ${h.summary?.verified_open ?? '—'} verified`}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            {assessments.length > 1 && (
              <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-text-secondary">
                <span>Compare</span>
                {['first', 'second'].map((k) => (
                  <select key={k} className={inputCls} value={compare[k]} onChange={(e) => setCompare({ ...compare, [k]: e.target.value })}>
                    <option value="">{k === 'first' ? 'earlier' : 'later'} assessment</option>
                    {assessments.map((a) => <option key={a.id} value={a.id}>{new Date(a.created_at).toLocaleString()}</option>)}
                  </select>
                ))}
                <Btn disabled={busy || !compare.first || !compare.second || compare.first === compare.second}
                     onClick={() => act(async () => setComparison(await compareGuardianAssessments(projectId, compare.first, compare.second)))}>Compare</Btn>
              </div>
            )}
            {comparison && (
              <div className="mt-2 grid gap-2 text-[11px] text-text-secondary md:grid-cols-3">
                {[['New', comparison.new], ['Resolved', comparison.resolved], ['Recurring', comparison.recurring]].map(([n, xs]) => (
                  <div key={n}><p className="text-text-muted">{n} ({xs.length})</p>{xs.map((x) => <p key={x.id}>{x.severity && <Badge value={x.severity} />} {x.title}</p>)}</div>
                ))}
              </div>
            )}
          </Card>
        )}
      </>)}
    </div>
  );
}
