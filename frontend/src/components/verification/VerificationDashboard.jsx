import React, { useCallback, useEffect, useRef, useState } from 'react';
import { FaPlay, FaShieldAlt, FaStop } from 'react-icons/fa';
import {
  cancelVerification, getVerification, getVerificationReport, listVerifications, startVerification,
} from '../../services/executionGuardian';
import ErrorSummary from './ErrorSummary';
import RepairHistory from './RepairHistory';
import VerificationReport from './VerificationReport';
import VerificationStatus from './VerificationStatus';
import VerificationStep from './VerificationStep';

const Card = ({ title, actions, children }) => (
  <section className="rounded-2xl border border-border-dark bg-surface-card p-4">
    {(title || actions) && <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
      {title && <h2 className="text-xs font-bold uppercase tracking-wider text-text-secondary">{title}</h2>}{actions}</div>}
    {children}
  </section>
);
const inputCls = 'rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-xs text-text-primary outline-none';

/**
 * The Execution Guardian dashboard for one project: start a verification (an isolated copy is checked and
 * repaired; the project itself is not changed), follow its checks, failures, agent activity and repairs live
 * (polling), and read the report. Everything shown comes from the API.
 */
export default function VerificationDashboard({ projectId, projectName }) {
  const [list, setList] = useState([]);
  const [selected, setSelected] = useState('');
  const [v, setV] = useState(null);
  const [maxRepairs, setMaxRepairs] = useState(3);
  const [timeout, setTimeoutS] = useState(600);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);

  const refresh = useCallback(async () => {
    if (!projectId) return;
    try {
      const r = await listVerifications(projectId);
      if (!alive.current) return;
      setList(r.verifications || []);
      setSelected((cur) => cur || r.verifications?.[0]?.id || '');
    } catch (e) { if (alive.current) setError(e?.error || 'Could not load verifications.'); }
  }, [projectId]);
  useEffect(() => { setSelected(''); setV(null); refresh(); }, [projectId, refresh]);

  const load = useCallback(async () => {
    if (!selected) return;
    setLoading((cur) => cur || !v);
    try { const r = await getVerification(projectId, selected); if (alive.current) setV(r.verification); }
    catch (e) { if (alive.current) setError(e?.error || 'Could not load the verification.'); }
    finally { if (alive.current) setLoading(false); }
  }, [projectId, selected]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!v || v.status !== 'RUNNING') return undefined;
    const t = setInterval(() => { load(); refresh(); }, 2500);           // polling, cleared when done or unmounted
    return () => clearInterval(t);
  }, [v, load, refresh]);

  const act = async (fn) => {
    setBusy(true); setError('');
    try { await fn(); await refresh(); await load(); } catch (e) { setError(e?.error || e?.message || 'Request failed.'); }
    finally { setBusy(false); }
  };
  const start = () => act(async () => {
    const r = await startVerification(projectId, { max_repair_attempts: Number(maxRepairs), check_timeout_seconds: Number(timeout) });
    setSelected(r.verification_id);
  });
  const download = () => act(async () => {
    const text = await getVerificationReport(projectId, v.id, 'markdown');
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }));
    const a = document.createElement('a'); a.href = url; a.download = `verification-${v.id}.md`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  if (!projectId) return <p className="text-xs text-text-muted">Select a generated project to verify.</p>;
  const checks = v?.checks || [];
  const tests = checks.find((c) => c.name === 'python_tests')?.counts || {};
  const totalSeconds = checks.reduce((s, c) => s + (c.duration_seconds || 0), 0);
  return (
    <div className="space-y-4">
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      <Card title={`Verify ${projectName || projectId}`}>
        <div className="flex flex-wrap items-end gap-2 text-xs text-text-secondary">
          <label className="flex flex-col text-[10px] uppercase text-text-muted">Max repair attempts (0–5)
            <input type="number" min="0" max="5" className={`${inputCls} w-20`} value={maxRepairs} onChange={(e) => setMaxRepairs(e.target.value)} /></label>
          <label className="flex flex-col text-[10px] uppercase text-text-muted">Per-check timeout (s)
            <input type="number" min="60" max="1800" className={`${inputCls} w-24`} value={timeout} onChange={(e) => setTimeoutS(e.target.value)} /></label>
          <button disabled={busy || v?.status === 'RUNNING'} onClick={start} className="inline-flex items-center gap-1.5 rounded-lg bg-accent-blue px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-40"><FaPlay className="h-2.5 w-2.5" /> Verify</button>
          <p className="text-[11px] text-text-muted">Checks run on an isolated copy in containers (no network for the app's code). Repairs that pass become an Autopilot plan for your approval — the project is not changed here.</p>
        </div>
        {list.length > 0 && <ul className="mt-3 space-y-1 text-[11px] text-text-secondary">{list.slice(0, 8).map((x) => (
          <li key={x.id} className="flex flex-wrap items-center gap-2"><VerificationStatus status={x.status} /><button className="underline" onClick={() => setSelected(x.id)}>{x.id}</button>
            <span className="text-text-muted">{x.source} · {new Date(x.started_at).toLocaleString()} · {x.repairs} repair(s)</span></li>))}</ul>}
        {!list.length && <p className="mt-3 text-[11px] text-text-muted">No verification has run for this project yet.</p>}
      </Card>
      {loading && !v && <p className="text-xs text-text-muted">Loading…</p>}
      {v && (<>
        <Card title="Verification" actions={<span className="flex items-center gap-2"><VerificationStatus status={v.status} />
          {v.status === 'RUNNING' && <button disabled={busy || v.cancel_requested} onClick={() => act(() => cancelVerification(projectId, v.id))} className="inline-flex items-center gap-1 rounded border border-border-dark px-2 py-0.5 text-[11px]"><FaStop className="h-2 w-2" /> {v.cancel_requested ? 'Cancelling…' : 'Cancel'}</button>}</span>}>
          <div className="grid gap-2 text-[11px] text-text-secondary md:grid-cols-4">
            <p><span className="text-text-muted">Current operation: </span>{v.current_operation}</p>
            <p><span className="text-text-muted">Tests: </span>{tests.passed ?? 0} passed, {tests.failed ?? 0} failed{tests.errors ? `, ${tests.errors} errors` : ''}</p>
            <p><span className="text-text-muted">Execution time: </span>{totalSeconds.toFixed(1)}s</p>
            <p><span className="text-text-muted">Repair attempt: </span>{v.repairs.length} of {v.settings?.max_repair_attempts}</p>
            <p className="md:col-span-4"><span className="text-text-muted">Stack: </span>{(v.stack?.languages || []).join(', ') || '—'} {(v.stack?.frameworks || []).length ? `(${v.stack.frameworks.join(', ')})` : ''}</p>
          </div>
          {v.error && <p className="mt-2 text-xs text-amber-200">{v.error}</p>}
          <ul className="mt-3 space-y-1">{checks.map((c) => <VerificationStep key={c.name} check={c} />)}</ul>
        </Card>
        <Card title="Errors"><ErrorSummary failures={v.failures} title="Current failures" />{!v.failures?.length && <p className="text-[11px] text-text-muted">No current failure.</p>}
          {v.original_failures?.length > 0 && v.repairs.length > 0 && <div className="mt-3"><ErrorSummary failures={v.original_failures} title="Originally found" /></div>}</Card>
        <Card title="Repair history"><RepairHistory repairs={v.repairs} max={v.settings?.max_repair_attempts} />
          {v.delivery?.autopilot_plan_id && <p className="mt-2 text-[11px] text-emerald-200">Repaired files ({v.delivery.files.join(', ')}) are Autopilot plan {v.delivery.autopilot_plan_id}, awaiting your approval. The project has not been changed.</p>}</Card>
        <Card title={<span className="flex items-center gap-1"><FaShieldAlt className="h-3 w-3" /> Agent activity</span>}>
          <ul className="max-h-60 space-y-0.5 overflow-auto text-[11px] text-text-secondary">{[...(v.activity || [])].reverse().map((x, i) => (
            <li key={i}><span className="font-mono text-text-muted">{x.at.slice(11, 19)}</span> <span className="text-text-primary">{x.actor}</span> — {x.text}</li>))}</ul>
        </Card>
        {v.status !== 'RUNNING' && <Card title="Verification report"><VerificationReport report={v.report} onDownload={download} /></Card>}
      </>)}
    </div>
  );
}
