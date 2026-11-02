import React, { useCallback, useEffect, useRef, useState } from 'react';
import { FaPlay, FaSearch, FaStop } from 'react-icons/fa';
import {
  analyzeIntegration, cancelIntegrationRun, errorsOf, getIntegrationReport, getIntegrationRun, listIntegrationRuns, verifyIntegration,
} from '../../services/integrationEngine';
import VerificationStatus from '../verification/VerificationStatus';
import ContractPanel from './ContractPanel';

const Card = ({ title, actions, children }) => (
  <section className="rounded-2xl border border-border-dark bg-surface-card p-4">
    {(title || actions) && <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
      {title && <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">{title}</h2>}{actions}</div>}
    {children}
  </section>
);
const inputCls = 'rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-xs text-text-primary outline-none';
const OPEN = ['open', 'unresolved', 'needs_contract_decision', 'blocked'];
const SEV = { critical: 'text-rose-300', high: 'text-rose-200', medium: 'text-amber-200', low: 'text-text-muted' };
const COVERAGE = {
  backend: ['API operations vs backend routes', 'backend routes'],
  frontend: ['frontend calls vs contract', 'frontend calls', 'frontend calls vs backend routes'],
  database: ['database entities vs schema / models', 'database entities'],
};
const GROUPS = [
  ['Missing endpoints', (f) => ['missing_endpoint', 'frontend_call_not_in_contract'].includes(f.rule)],
  ['Paths, methods and auth', (f) => ['incorrect_url_path', 'incorrect_http_method', 'auth_mismatch', 'incorrect_status_code',
    'frontend_backend_mismatch'].includes(f.rule)],
  ['Schema mismatches', (f) => /field|type|pagination|datetime|error_response/.test(f.rule) && !f.rule.startsWith('db_')],
  ['Database', (f) => f.rule.startsWith('db_')],
  ['Contract drift', (f) => f.rule === 'contract_drift'],
  ['Other', () => true],
];

/** A component's status from the run: open findings on it, or whether its checks ran at all (never assumed). */
function componentStatus(run, name) {
  if (!run) return { status: null, detail: '' };
  const open = (run.findings || []).filter((f) => OPEN.includes(f.status) && (f.components || []).includes(name));
  const cov = (run.coverage || []).filter((c) => COVERAGE[name].includes(c.check));
  if (open.some((f) => ['critical', 'high'].includes(f.severity))) return { status: 'INCOMPATIBLE', detail: `${open.length} open finding(s)` };
  if (!cov.length || cov.every((c) => c.status !== 'checked')) return { status: 'NOT_CHECKED', detail: cov[0]?.detail || 'not analysed' };
  if (open.length) return { status: 'COMPATIBLE_WITH_WARNINGS', detail: `${open.length} open finding(s)` };
  return { status: 'COMPATIBLE', detail: cov.map((c) => c.detail).join('; ') };
}

function Finding({ f }) {
  return (
    <li className="rounded-lg border border-border-subtle p-2">
      <p className="flex flex-wrap items-center gap-2"><span className={`font-semibold uppercase ${SEV[f.severity]}`}>{f.severity}</span>
        <span className="font-mono text-text-primary">{f.rule}</span><span>{f.target}</span>
        <span className="text-text-muted">{f.basis}{f.responsible_agent ? ` · ${f.responsible_agent} agent` : ' · responsible: undecided'}</span>
        {f.status !== 'open' && <span className="text-amber-200">{f.status.replace(/_/g, ' ')}</span>}
        {f.breaking != null && <span className={f.breaking ? 'text-rose-300' : 'text-emerald-300'}>{f.breaking ? 'breaking' : 'backward compatible'}</span>}</p>
      <p><span className="text-text-muted">expected: </span>{f.expected}</p>
      <p><span className="text-text-muted">actual: </span>{f.actual}</p>
      <p className="text-text-muted">fix: {f.recommended_fix}</p>
    </li>
  );
}

/**
 * The Integration & Compatibility dashboard for one project: its shared contract, analysis and verification runs, the
 * frontend / backend / database status, findings (missing endpoints, schema mismatches, drift), generated contract
 * tests with their real outcomes, repair attempts and the final report. Everything comes from the API.
 */
export default function IntegrationDashboard({ projectId, projectName }) {
  const [runs, setRuns] = useState([]);
  const [selected, setSelected] = useState('');
  const [run, setRun] = useState(null);
  const [maxRepairs, setMaxRepairs] = useState(3);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);

  const refresh = useCallback(async () => {
    if (!projectId) return;
    try {
      const r = await listIntegrationRuns(projectId);
      if (!alive.current) return;
      setRuns(r.runs || []);
      setSelected((cur) => cur || r.runs?.[0]?.id || '');
    } catch (e) { if (alive.current) setError(e?.error || 'Could not load the integration runs.'); }
  }, [projectId]);
  useEffect(() => { setSelected(''); setRun(null); refresh(); }, [projectId, refresh]);

  const load = useCallback(async () => {
    if (!selected) return;
    setLoading(true);
    try { const r = await getIntegrationRun(projectId, selected); if (alive.current) setRun(r.run); }
    catch (e) { if (alive.current) setError(e?.error || 'Could not load the run.'); }
    finally { if (alive.current) setLoading(false); }
  }, [projectId, selected]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!run || !['queued', 'running'].includes(run.status)) return undefined;
    const t = setInterval(() => { load(); refresh(); }, 2500);
    return () => clearInterval(t);
  }, [run, load, refresh]);

  const act = async (fn) => {
    setBusy(true); setError('');
    try { await fn(); await refresh(); } catch (e) { setError([e?.error || e?.message || 'Request failed.', ...errorsOf(e)].join(' ')); }
    finally { setBusy(false); }
  };
  const download = () => act(async () => {
    const text = await getIntegrationReport(projectId, run.id, 'markdown');
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
    const a = document.createElement('a'); a.href = url; a.download = `compatibility-${run.id}.md`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  if (!projectId) return <p className="text-xs text-text-muted">Select a generated project.</p>;
  const running = run && ['queued', 'running'].includes(run.status);
  const open = (run?.findings || []).filter((f) => OPEN.includes(f.status));
  const info = (run?.findings || []).filter((f) => f.status === 'info');
  const repaired = (run?.findings || []).filter((f) => f.status === 'repaired');
  const counts = run?.test_execution?.counts || {};
  const report = run?.report || {};
  const used = new Set();
  return (
    <div className="space-y-4">
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      <Card title={`Shared contract — ${projectName || projectId}`}><ContractPanel projectId={projectId} onChanged={refresh} /></Card>
      <Card title="Check compatibility">
        <div className="flex flex-wrap items-end gap-2 text-xs text-text-secondary">
          <button disabled={busy || running} onClick={() => act(async () => { const r = await analyzeIntegration(projectId); setSelected(r.run_id); })}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border-dark px-3 py-1.5 text-xs text-text-primary disabled:opacity-40"><FaSearch className="h-2.5 w-2.5" /> Analyze</button>
          <label className="flex flex-col text-[10px] uppercase text-text-muted">Max repair attempts (0–5)
            <input type="number" min="0" max="5" className={`${inputCls} w-20`} value={maxRepairs} onChange={(e) => setMaxRepairs(e.target.value)} /></label>
          <button disabled={busy || running} onClick={() => act(async () => { const r = await verifyIntegration(projectId, { max_repair_attempts: Number(maxRepairs) }); setSelected(r.run_id); })}
            className="inline-flex items-center gap-1.5 rounded-lg bg-accent-blue px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-40"><FaPlay className="h-2.5 w-2.5" /> Verify</button>
          <p className="text-[11px] text-text-muted">Analyze reads the code (nothing runs). Verify also generates contract tests and runs them in isolation, then repairs within the limit on a copy — repairs become an Autopilot plan for your approval.</p>
        </div>
        {runs.length > 0 ? <ul className="mt-3 space-y-1 text-[11px] text-text-secondary">{runs.slice(0, 8).map((x) => (
          <li key={x.id} className="flex flex-wrap items-center gap-2"><VerificationStatus status={x.status === 'running' ? 'RUNNING' : x.status} />
            <button className="underline" onClick={() => setSelected(x.id)}>{x.id}</button>
            <span className="text-text-muted">{x.kind} · {x.source} · contract v{x.contract_version ?? '—'} · {new Date(x.started_at).toLocaleString()} · {x.open_findings} open · {x.repairs} repair(s)</span></li>))}</ul>
          : <p className="mt-3 text-[11px] text-text-muted">No compatibility run yet.</p>}
      </Card>
      {loading && !run && <p className="text-xs text-text-muted">Loading…</p>}
      {run && (<>
        <Card title="Integration status" actions={<span className="flex items-center gap-2"><VerificationStatus status={running ? 'RUNNING' : run.status} />
          {running && <button disabled={busy || run.cancel_requested} onClick={() => act(() => cancelIntegrationRun(projectId, run.id))} className="inline-flex items-center gap-1 rounded border border-border-dark px-2 py-0.5 text-[11px]"><FaStop className="h-2 w-2" /> {run.cancel_requested ? 'Cancelling…' : 'Cancel'}</button>}</span>}>
          {!running && report.statement && <p className="mb-2 text-xs text-text-primary">{report.statement}</p>}
          <div className="grid gap-2 md:grid-cols-3">{['frontend', 'backend', 'database'].map((n) => {
            const s = componentStatus(run, n);
            return (<div key={n} className="rounded-lg border border-border-subtle p-2 text-[11px] text-text-secondary">
              <p className="mb-1 flex items-center justify-between"><span className="font-semibold capitalize text-text-primary">{n}</span><VerificationStatus status={s.status} /></p>
              <p>{s.detail}</p></div>);
          })}</div>
          <p className="mt-2 text-[11px] text-text-secondary"><span className="text-text-muted">Current operation: </span>{run.current_operation} ·
            <span className="text-text-muted"> contract </span>v{run.contract_version ?? '—'}</p>
          {run.error && <p className="mt-2 text-xs text-amber-200">{run.error}</p>}
          {report.why?.length > 0 && <ul className="mt-2 list-disc pl-5 text-[11px] text-rose-200">{report.why.map((w) => <li key={w}>{w}</li>)}</ul>}
          {report.warnings?.length > 0 && <ul className="mt-2 list-disc pl-5 text-[11px] text-amber-200/90">{report.warnings.slice(0, 12).map((w) => <li key={w}>{w}</li>)}</ul>}
        </Card>
        <Card title={`Findings (${open.length} open)`}>
          {!open.length && <p className="text-[11px] text-text-muted">No open finding{run.kind === 'analyze' ? ' (static analysis only)' : ''}.</p>}
          <div className="space-y-3 text-[11px] text-text-secondary">{GROUPS.map(([title, test]) => {
            const items = open.filter((f) => !used.has(f.id) && test(f));
            items.forEach((f) => used.add(f.id));
            return items.length ? <div key={title}><p className="mb-1 text-[10px] uppercase text-text-muted">{title}</p>
              <ul className="space-y-1">{items.map((f) => <Finding key={f.id} f={f} />)}</ul></div> : null;
          })}</div>
          {repaired.length > 0 && <p className="mt-3 text-[11px] text-emerald-200">Repaired in this run: {repaired.map((f) => `${f.rule} ${f.target}`).join('; ')}</p>}
          {info.length > 0 && <p className="mt-2 text-[11px] text-text-muted">Informational: {info.map((f) => `${f.rule} ${f.target}`).join('; ')}</p>}
        </Card>
        <Card title={`Contract tests (${run.tests?.length || 0} generated)`}>
          {run.kind === 'analyze' && <p className="text-[11px] text-text-muted">Analysis runs do not execute tests: use Verify.</p>}
          {run.test_execution?.status && <p className="mb-2 flex flex-wrap items-center gap-2 text-[11px] text-text-secondary"><VerificationStatus status={run.test_execution.status} />
            {counts.passed ?? 0} passed, {(counts.failed ?? 0) + (counts.error ?? 0)} failed, {counts.skipped ?? 0} skipped, {counts.not_run ?? 0} not run
            <span className="text-text-muted">{run.test_execution.environment}</span>
            {run.test_execution.reason && <span className="text-amber-200">{run.test_execution.reason}</span>}</p>}
          <ul className="max-h-72 space-y-0.5 overflow-auto text-[11px] text-text-secondary">{(run.tests || []).map((t) => (
            <li key={t.id} className="flex flex-wrap items-baseline gap-2"><VerificationStatus status={{ not_run: 'NOT_CHECKED', error: 'FAILED' }[t.status] || t.status.toUpperCase()} />
              <span className="font-mono">{t.kind}</span><span>{t.target}</span><span className="text-text-muted">{t.description}</span>
              {t.detail && t.status !== 'passed' && <span className="w-full pl-4 text-[10px] text-amber-200/90">{t.detail}</span>}</li>))}</ul>
        </Card>
        <Card title="Repair attempts">
          {!run.repairs?.length ? <p className="text-[11px] text-text-muted">No repair was attempted.</p> : (
            <ul className="space-y-2 text-[11px] text-text-secondary">{run.repairs.map((r, i) => (
              <li key={i} className="rounded-lg border border-border-subtle p-2">
                <p className="flex flex-wrap items-center gap-2"><span className="text-text-primary">Attempt {r.attempt} of {run.settings?.max_repair_attempts ?? '—'}</span>
                  <span>{r.agent} agent</span><span className="font-mono text-text-muted">{r.strategy}</span>
                  <span className={r.outcome === 'resolved' ? 'text-emerald-300' : r.outcome === 'improved' ? 'text-lime-300' : 'text-amber-200'}>{r.outcome.replace(/_/g, ' ')}</span>
                  {r.rolled_back && <span className="text-rose-200">rolled back</span>}</p>
                {r.files_changed?.length > 0 && <p className="font-mono text-[10px]">changed: {r.files_changed.join(', ')}</p>}
                {r.resolved?.length > 0 && <p className="text-[10px] text-emerald-200">resolved: {r.resolved.length} finding(s)</p>}
                {r.rejected_paths?.length > 0 && <p className="text-[10px] text-rose-200">rejected: {r.rejected_paths.map((x) => `${x.path} (${x.reason})`).join('; ')}</p>}
                {r.note && <p className="text-[10px] text-text-muted">{r.note}</p>}
              </li>))}</ul>)}
          {run.delivery?.autopilot_plan_id && <p className="mt-2 text-[11px] text-emerald-200">Repaired files ({run.delivery.files.join(', ')}) are Autopilot plan {run.delivery.autopilot_plan_id}, awaiting your approval. The project has not been changed.</p>}
          {run.delivery?.written?.length > 0 && <p className="mt-2 text-[11px] text-emerald-200">Written to the generated project: {run.delivery.written.join(', ')}</p>}
        </Card>
        <Card title="Activity">
          <ul className="max-h-48 space-y-0.5 overflow-auto text-[11px] text-text-secondary">{[...(run.activity || [])].reverse().map((x, i) => (
            <li key={i}><span className="font-mono text-text-muted">{x.at.slice(11, 19)}</span> <span className="text-text-primary">{x.actor}</span> — {x.text}</li>))}</ul>
        </Card>
        {!running && report.run_id && (
          <Card title="Compatibility report" actions={<button onClick={download} className="rounded border border-border-dark px-2 py-0.5 text-[11px] text-text-secondary">Download Markdown</button>}>
            <div className="grid gap-2 text-[11px] text-text-secondary md:grid-cols-4">
              <p><span className="text-text-muted">Contract: </span>v{report.contract_version} ({report.contract_revision})</p>
              <p><span className="text-text-muted">Tests executed: </span>{report.tests_executed} ({report.tests_passed} passed, {report.tests_failed} failed)</p>
              <p><span className="text-text-muted">Findings: </span>{Object.entries(report.findings_by_severity || {}).map(([k, v]) => `${v} ${k}`).join(', ')}</p>
              <p><span className="text-text-muted">Repairs: </span>{report.repairs?.length || 0}</p>
            </div>
            {report.coverage?.some((c) => c.status !== 'checked') && <ul className="mt-2 list-disc pl-5 text-[11px] text-text-muted">
              {report.coverage.filter((c) => c.status !== 'checked').map((c) => <li key={c.check}>not checked — {c.check}: {c.detail}</li>)}</ul>}
            <ul className="mt-2 list-disc pl-5 text-[10px] text-text-muted">{(report.limitations || []).map((l) => <li key={l}>{l}</li>)}</ul>
          </Card>)}
      </>)}
    </div>
  );
}
