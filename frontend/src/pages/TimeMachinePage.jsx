import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { FaChevronDown, FaChevronRight, FaHistory, FaPlay, FaSearch, FaStop, FaUndo } from 'react-icons/fa';
import {
  cancelJob, createCheckpoint, getGraph, getJob, getReplay, listCheckpoints, listEvents, listJobs, listLegacyEvents,
  previewRestore, restoreApproved, restoreIsolated, startInvestigation, startRerun,
} from '../services/timeMachine';
import { listAutopilotProjects } from '../services/evolutionAutopilot';

const GOOD = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
const BAD = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
const WARN = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
const GREY = 'bg-slate-700/50 text-slate-300 border-slate-600';
const TONE = {
  success: GOOD, passed: GOOD, completed: GOOD, confirmed: GOOD, restore: GOOD, recorded: GOOD,
  failure: BAD, failed: BAD, error: BAD, rejected: BAD, conflict: BAD,
  inconclusive: WARN, probable: WARN, hypothesis: WARN, flaky: WARN, temporal: WARN, unavailable: WARN, cancelled: GREY,
  info: GREY, not_reproduced: GREY, file: GREY,
};
const ACTIVE = new Set(['queued', 'running']);
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
const TYPES = ['task_created', 'agent_started', 'agent_completed', 'artifact_generated', 'test_executed', 'patch_applied', 'approval_granted',
  'approval_rejected', 'security_finding', 'security_verification', 'performance_measured', 'resilience_assessed', 'experiment_evaluated',
  'rollback_performed', 'checkpoint_created', 'restore_previewed', 'restore_performed', 'investigation_completed', 'rerun_completed',
  'task_completed', 'task_failed', 'correction'];
const PAGE = 50;

// --- timeline ------------------------------------------------------------------------------------------------------

function EventRow({ e, onTask }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="rounded-xl border border-border-subtle bg-bg-base/40">
      <button className="flex w-full flex-wrap items-center gap-2 px-3 py-2 text-left" onClick={() => setOpen((v) => !v)}>
        {open ? <FaChevronDown className="h-2.5 w-2.5 text-text-muted" /> : <FaChevronRight className="h-2.5 w-2.5 text-text-muted" />}
        <span className="font-mono text-[10px] text-text-muted">#{e.seq} {new Date(e.at).toLocaleString()}</span>
        <span className="rounded bg-bg-base px-1.5 text-[10px] text-text-secondary">{label(e.type)}</span>
        <Badge value={e.outcome} /><span className="text-[11px] text-text-muted">{e.source}</span>
        <span className="text-xs text-text-primary">{e.summary}</span>
      </button>
      {open && (
        <div className="space-y-1 border-t border-border-subtle px-3 py-2 text-[11px] text-text-secondary">
          <p className="text-[10px] uppercase text-text-muted">Recorded facts</p>
          <p>Task: {e.task_id ? <button className="font-mono underline" onClick={() => onTask(e.task_id)}>{e.task_id}</button> : '—'} · revision <span className="font-mono">{e.revision ? e.revision.slice(0, 12) : 'not recorded'}</span>{e.git_commit && <> · commit <span className="font-mono">{e.git_commit.slice(0, 10)}</span></>}</p>
          {e.parents.length > 0 && <p>Recorded causes: <span className="font-mono">{e.parents.join(', ')}</span></p>}
          {Object.keys(e.refs).length > 0 && <p>References: {Object.entries(e.refs).map(([k, v]) => `${k}=${v}`).join(' · ')}</p>}
          {e.files.length > 0 && <p>Files: {e.files.map((f) => `${f.path} (${f.change}${f.content_stored ? '' : ', content not stored'})`).join(', ')}</p>}
          {e.error && <p className="text-rose-200">{e.error}</p>}
          {Object.keys(e.data).length > 0 && <Pre>{JSON.stringify(e.data, null, 1).slice(0, 4000)}</Pre>}
          {Object.keys(e.config).length > 0 && <p className="text-text-muted">Configuration: {JSON.stringify(e.config).slice(0, 600)}</p>}
          <p className="font-mono text-[10px] text-text-muted">hash {e.hash.slice(0, 16)} · prev {e.prev_hash ? e.prev_hash.slice(0, 16) : '—'}</p>
        </div>
      )}
    </li>
  );
}

function Timeline({ projectId, onTask }) {
  const [filters, setFilters] = useState({ types: '', sources: '', outcome: '', q: '', file: '' });
  const [page, setPage] = useState({ items: [], total: 0, offset: 0 });
  const [offset, setOffset] = useState(0);
  const [legacy, setLegacy] = useState(null);
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    try {
      const params = Object.fromEntries(Object.entries({ ...filters, offset, limit: PAGE }).filter(([, v]) => v !== ''));
      setPage(await listEvents(projectId, params));
    } catch (e) { setError(e?.error || 'Could not load events.'); }
  }, [projectId, filters, offset]);
  useEffect(() => { load(); }, [load]);
  const set = (k) => (ev) => { setOffset(0); setFilters({ ...filters, [k]: ev.target.value }); };
  return (
    <Card title={`Engineering timeline (${page.total})`} actions={page.integrity && <span className="text-[11px]">ledger integrity <Badge value={page.integrity.valid ? 'success' : 'failure'} /> {!page.integrity.valid && page.integrity.reason}</span>}>
      {error && <p className="text-xs text-rose-200">{error}</p>}
      <div className="mb-2 flex flex-wrap gap-2">
        <select className={inputCls} value={filters.types} onChange={set('types')}><option value="">all event types</option>{TYPES.map((t) => <option key={t} value={t}>{label(t)}</option>)}</select>
        <input className={`${inputCls} w-36`} placeholder="agent / subsystem" value={filters.sources} onChange={set('sources')} />
        <select className={inputCls} value={filters.outcome} onChange={set('outcome')}><option value="">all outcomes</option>{['success', 'failure', 'rejected', 'inconclusive', 'cancelled', 'info', 'error'].map((o) => <option key={o}>{o}</option>)}</select>
        <input className={`${inputCls} w-40`} placeholder="file path" value={filters.file} onChange={set('file')} />
        <input className={`${inputCls} w-44`} placeholder="search" value={filters.q} onChange={set('q')} />
      </div>
      {page.items.length === 0 ? <p className="text-xs text-text-muted">No recorded events match. Only events that AIForge subsystems actually reported appear here — nothing is reconstructed or invented.</p> : (
        <ul className="space-y-1">{page.items.map((e) => <EventRow key={e.id} e={e} onTask={onTask} />)}</ul>
      )}
      <div className="mt-2 flex items-center gap-2 text-[11px] text-text-muted">
        <Btn disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Newer</Btn>
        <span>{page.total ? `${offset + 1}–${Math.min(offset + PAGE, page.total)} of ${page.total}` : ''}</span>
        <Btn disabled={offset + PAGE >= page.total} onClick={() => setOffset(offset + PAGE)}>Older</Btn>
        <Btn className="ml-auto" onClick={async () => setLegacy((await listLegacyEvents(projectId)).events)}>Legacy Flight Recorder events</Btn>
      </div>
      {legacy && <details open className="mt-2"><summary className="cursor-pointer text-[11px] text-amber-200">Legacy events ({legacy.length}) — not hash-chained; some came from simulated subsystems</summary>
        <ul className="mt-1 space-y-0.5 text-[11px] text-text-muted">{legacy.slice(0, 100).map((e) => <li key={e.id}>{e.timestamp} {e.agent} {e.event_type} {e.reason ? `— ${String(e.reason).slice(0, 120)}` : ''}</li>)}</ul></details>}
    </Card>
  );
}

// --- causal graph --------------------------------------------------------------------------------------------------

function Graph({ projectId, taskId }) {
  const [g, setG] = useState(null);
  const [sel, setSel] = useState(null);
  useEffect(() => { getGraph(projectId, taskId).then(setG).catch(() => setG(null)); }, [projectId, taskId]);
  const layout = useMemo(() => {
    if (!g) return null;
    const lanes = [...new Set(g.nodes.map((n) => n.source))];
    const pos = {};
    g.nodes.forEach((n, i) => { pos[n.id] = { x: 90 + lanes.indexOf(n.source) * 170, y: 30 + i * 46 }; });
    return { lanes, pos, height: 60 + g.nodes.length * 46, width: Math.max(400, 120 + lanes.length * 170) };
  }, [g]);
  if (!g || !layout) return <Card title="Causal graph"><p className="text-xs text-text-muted">Loading…</p></Card>;
  const stroke = { recorded: '#34d399', temporal: '#fbbf24', file: '#64748b' };
  return (
    <Card title={`Causal graph${taskId ? ` — task ${taskId}` : ''} (${g.nodes.length} events)`}>
      <div className="mb-2 flex flex-wrap gap-3 text-[11px] text-text-secondary">{Object.entries(g.legend).map(([k, v]) => <span key={k}><Badge value={k} /> {v}</span>)}</div>
      {g.nodes.length === 0 ? <p className="text-xs text-text-muted">No recorded events.</p> : (
        <div className="max-h-[520px] overflow-auto rounded-lg bg-black/30">
          <svg width={layout.width} height={layout.height} className="text-[10px]">
            {layout.lanes.map((l, i) => <text key={l} x={90 + i * 170} y={14} textAnchor="middle" fill="#94a3b8">{l.slice(0, 22)}</text>)}
            {g.edges.map((e, i) => {
              const a = layout.pos[e.from]; const b = layout.pos[e.to];
              if (!a || !b) return null;
              return <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={stroke[e.kind]} strokeWidth={e.kind === 'recorded' ? 1.6 : 1} strokeDasharray={e.kind === 'recorded' ? '' : '4 3'} opacity={0.8} />;
            })}
            {g.nodes.map((n) => {
              const p = layout.pos[n.id];
              const fill = { success: '#065f46', failure: '#9f1239', error: '#9f1239', rejected: '#9f1239', inconclusive: '#92400e' }[n.outcome] || '#334155';
              return (
                <g key={n.id} onClick={() => setSel(n)} className="cursor-pointer">
                  <rect x={p.x - 70} y={p.y - 13} width={140} height={26} rx={6} fill={fill} stroke={sel?.id === n.id ? '#e2e8f0' : 'transparent'} />
                  <text x={p.x} y={p.y + 4} textAnchor="middle" fill="#e2e8f0">{label(n.type).slice(0, 22)}</text>
                </g>
              );
            })}
          </svg>
        </div>
      )}
      {sel && <div className="mt-2 rounded-lg border border-border-subtle p-2 text-[11px] text-text-secondary">
        <p><span className="font-mono">{sel.id}</span> · {sel.source} · <Badge value={sel.outcome} /> · {new Date(sel.at).toLocaleString()}</p>
        <p className="text-text-primary">{sel.summary}</p>
        {sel.files.length > 0 && <p>Files: {sel.files.join(', ')}</p>}
        <p>Incoming: {g.edges.filter((e) => e.to === sel.id).map((e) => `${e.kind} from ${e.from}`).join('; ') || 'none'} · Outgoing: {g.edges.filter((e) => e.from === sel.id).map((e) => `${e.kind} to ${e.to}`).join('; ') || 'none'}</p>
      </div>}
    </Card>
  );
}

// --- replay ----------------------------------------------------------------------------------------------------------

function Replay({ projectId, taskId, onRerun, busy }) {
  const [r, setR] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => { setR(null); setError(''); getReplay(projectId, taskId).then(setR).catch((e) => setError(e?.error || 'No replay.')); }, [projectId, taskId]);
  const execution = r?.steps.map((s) => s.event.refs.execution_id).find(Boolean);
  const experiment = r?.steps.map((s) => s.event.refs.experiment_id).find(Boolean);
  return (
    <Card title={`Decision replay — ${taskId}`} actions={<div className="flex gap-2">
      {execution && <Btn disabled={busy} onClick={() => onRerun({ execution_id: execution })}><FaPlay className="h-2.5 w-2.5" /> Experimental rerun</Btn>}
      {!execution && experiment && <Btn disabled={busy} onClick={() => onRerun({ experiment_id: experiment })}><FaPlay className="h-2.5 w-2.5" /> Experimental rerun</Btn>}</div>}>
      {error && <p className="text-xs text-rose-200">{error}</p>}
      {r && <div className="space-y-2 text-xs text-text-secondary">
        <p className="text-[11px] text-text-muted">{r.mode}. A rerun executes the task again now, in isolation: models and environments can differ, so it is never presented as a reproduction.</p>
        {r.gaps.length > 0 && <p className="text-amber-200">Incomplete history: {r.gaps.join('; ')}</p>}
        <ol className="space-y-1">{r.steps.map((s) => (
          <li key={s.event.id} className="rounded-lg border border-border-subtle p-2">
            <p><span className="font-mono text-[10px] text-text-muted">#{s.event.seq}</span> {label(s.event.type)} <Badge value={s.event.outcome} /> <span className="text-text-muted">{s.event.source}</span> — {s.event.summary}</p>
            {s.diffs.map((d) => d.available ? <details key={d.path}><summary className="cursor-pointer text-[11px]">{d.path} ({d.change})</summary><Pre>{d.diff}</Pre></details>
              : <p key={d.path} className="text-[11px] text-amber-200">{d.path}: {d.reason}</p>)}
          </li>
        ))}</ol>
      </div>}
    </Card>
  );
}

// --- checkpoints and restore -------------------------------------------------------------------------------------------

function Restore({ projectId, target, setTarget, busy, act }) {
  const [cps, setCps] = useState([]);
  const [name, setName] = useState('');
  const [preview, setPreview] = useState(null);
  const [iso, setIso] = useState(null);
  const [done, setDone] = useState(null);
  const [consent, setConsent] = useState(false);
  const load = useCallback(() => listCheckpoints(projectId).then((r) => setCps(r.checkpoints || [])).catch(() => {}), [projectId]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { setPreview(null); setIso(null); setDone(null); setConsent(false); }, [target]);
  return (
    <Card title="Checkpoints and safe restore">
      <div className="space-y-2 text-xs text-text-secondary">
        <div className="flex flex-wrap items-center gap-2">
          <input className={`${inputCls} w-56`} placeholder="checkpoint name" value={name} onChange={(e) => setName(e.target.value)} />
          <Btn disabled={busy || !name.trim()} onClick={() => act(async () => { await createCheckpoint(projectId, name.trim()); setName(''); await load(); })}>Create checkpoint</Btn>
        </div>
        {cps.length > 0 && <ul className="space-y-0.5">{cps.map((c) => (
          <li key={c.id} className="flex flex-wrap items-center gap-2"><span className="text-text-primary">{c.name}</span><span className="text-[10px] text-text-muted">{new Date(c.at).toLocaleString()} · {c.file_count} files · rev {c.revision?.slice(0, 10)}{c.unstored?.length ? ` · ${c.unstored.length} not stored` : ''}</span>
            <Btn onClick={() => setTarget({ checkpoint_id: c.id })}>Select</Btn></li>
        ))}</ul>}
        {target && (
          <div className="space-y-2 rounded-lg border border-border-subtle p-2">
            <p>Target: <span className="font-mono">{JSON.stringify(target)}</span></p>
            <div className="flex flex-wrap gap-2">
              <Btn disabled={busy} onClick={() => act(async () => setPreview(await previewRestore(projectId, target)))}>Preview effect on the project</Btn>
              <Btn disabled={busy} onClick={() => act(async () => setIso(await restoreIsolated(projectId, target)))}>Restore into an isolated folder and test</Btn>
            </div>
            {iso && <p>Isolated restore of {iso.label}: {iso.files} files, tests <Badge value={iso.tests?.status} /> {iso.tests?.environment} {iso.failing_tests.length > 0 && `— failing: ${iso.failing_tests.join(', ')}`}</p>}
            {preview && <div className="space-y-1">
              <p>{preview.label}: <Badge value="restore" /> {preview.restore} · <Badge value="conflict" /> {preview.conflicts} (never overwritten) · <Badge value="unavailable" /> {preview.unavailable}</p>
              <table className="w-full text-left text-[11px]"><tbody>{preview.rows.map((r) => <tr key={r.path} className="border-t border-border-subtle"><td className="py-1 pr-2 font-mono">{r.path}</td><td className="pr-2"><Badge value={r.action} /></td><td className="pr-2">{r.operation}</td><td className="text-text-muted">{r.reason}</td></tr>)}</tbody></table>
              {preview.restore > 0 && !done && <div className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2">
                <label className="flex items-center gap-1.5 text-amber-100"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                  I approve replacing the {preview.restore} file(s) marked “restore” (a recovery checkpoint is created first; conflicts stay untouched)</label>
                <Btn tone="good" disabled={busy || !consent} onClick={() => act(async () => { setDone(await restoreApproved(projectId, target, preview.token)); await load(); })}><FaUndo className="h-2.5 w-2.5" /> Restore</Btn>
              </div>}
            </div>}
            {done && <p>Restored {done.restored.length} file(s); kept {done.conflicts_left.length} conflicting file(s); recovery checkpoint <span className="font-mono">{done.recovery_checkpoint}</span>; tests after restore <Badge value={done.tests.status} /> ({done.tests.environment})</p>}
          </div>
        )}
      </div>
    </Card>
  );
}

// --- jobs (detective, reruns) ---------------------------------------------------------------------------------------------

function Jobs({ projectId, jobs, onRevert, refresh, busy, act }) {
  const [open, setOpen] = useState('');
  const [job, setJob] = useState(null);
  useEffect(() => { if (open) getJob(projectId, open).then((r) => setJob(r.job)).catch(() => setJob(null)); }, [projectId, open, jobs]);
  useEffect(() => {
    if (!jobs.some((j) => ACTIVE.has(j.status))) return undefined;
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [jobs, refresh]);
  return (
    <Card title="Regression Detective and reruns" actions={<Btn tone="primary" disabled={busy} onClick={() => act(() => startInvestigation(projectId))}><FaSearch className="h-2.5 w-2.5" /> Investigate the current failure</Btn>}>
      <p className="mb-2 text-[11px] text-text-muted">The Detective runs the project's tests on reconstructed states in isolated folders (the project is not changed). Verdicts: confirmed (exact pass→fail transition and reverting only that change fixes it), probable, hypothesis, inconclusive, not reproduced.</p>
      {jobs.length === 0 ? <p className="text-xs text-text-muted">No investigations or reruns yet.</p> : (
        <ul className="space-y-1">{jobs.map((j) => (
          <li key={j.id} className="rounded-lg border border-border-subtle">
            <button className="flex w-full flex-wrap items-center gap-2 px-3 py-2 text-left text-xs" onClick={() => setOpen(open === j.id ? '' : j.id)}>
              <span className="font-mono text-[10px] text-text-muted">{j.id}</span>{label(j.kind)} <Badge value={j.status} />
              {j.result?.verdict && <Badge value={j.result.verdict} />}{j.result?.identical_output != null && <span className="text-[11px]">{j.result.identical_output ? 'identical output' : 'output differs'}</span>}
              <span className="text-[10px] text-text-muted">{new Date(j.created_at).toLocaleString()}</span>
              {ACTIVE.has(j.status) && <Btn tone="bad" className="ml-auto" onClick={(e) => { e.stopPropagation(); act(() => cancelJob(projectId, j.id)); }}><FaStop className="h-2.5 w-2.5" /> Cancel</Btn>}
            </button>
            {open === j.id && job && (
              <div className="space-y-1 border-t border-border-subtle px-3 py-2 text-[11px] text-text-secondary">
                {job.result?.summary && <p className="text-text-primary">{job.result.summary}</p>}
                {job.result?.known_good && <p>Known-good: <span className="font-mono">{job.result.known_good.revision?.slice(0, 12)}</span> — {job.result.known_good.how}</p>}
                {job.result?.suspect && <p>Suspected change: <span className="text-text-primary">{job.result.suspect.summary}</span> ({job.result.suspect.source}, files {job.result.suspect.files.join(', ')})</p>}
                {(job.result?.evidence || []).map((x, i) => <p key={i}>• {x}</p>)}
                {(job.result?.limitations || []).map((x, i) => <p key={i} className="text-amber-200">limitation: {x}</p>)}
                {job.result?.proposal && <Btn onClick={() => onRevert({ revert_change_id: job.result.proposal.revert_change_id })}>Use the proposed revert as restore target (tests after revert: {job.result.proposal.tests_after_revert})</Btn>}
                {job.result?.differences && <p>Differences: {job.result.differences.join('; ') || 'none recorded'}</p>}
                {job.result?.files && <ul>{job.result.files.map((f) => <li key={f.path}>{f.path}: {f.identical ? 'identical to the recorded output' : 'differs from the recorded output'}</li>)}</ul>}
                {job.result?.error && <p className="text-rose-200">{job.result.error}</p>}
                {job.steps.length > 0 && <table className="w-full text-left"><thead className="text-[10px] uppercase text-text-muted"><tr><th className="py-1 pr-2">State tested</th><th className="pr-2">Result</th><th className="pr-2">Environment</th><th>Failing tests</th></tr></thead>
                  <tbody>{job.steps.map((s, i) => <tr key={i} className="border-t border-border-subtle align-top"><td className="py-1 pr-2">{s.state}</td><td className="pr-2"><Badge value={s.status} /> {Object.entries(s.counts || {}).map(([k, v]) => `${v} ${k}`).join(', ')}</td><td className="pr-2">{s.environment}</td><td>{(s.failing || []).join(', ') || '—'}</td></tr>)}</tbody></table>}
              </div>
            )}
          </li>
        ))}</ul>
      )}
    </Card>
  );
}

// --- page ---------------------------------------------------------------------------------------------------------------------

/**
 * AIForge Time Machine: the recorded engineering history of a project (hash-chained ledger), how events relate,
 * what each task did, safe checkpoints and restores, the Regression Detective, and experimental reruns.
 * Recorded facts, temporal associations and reconstructions are labelled as such.
 */
export default function TimeMachinePage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [taskId, setTaskId] = useState('');
  const [target, setTarget] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listAutopilotProjects().then((r) => {
      setProjects(r.projects || []);
      const preferred = (r.projects || []).find((p) => p.project_id === activeProjectId);
      setProjectId((cur) => cur || preferred?.project_id || r.projects?.[0]?.project_id || '');
    }).catch((e) => setError(e?.error || 'Could not load projects.'));
  }, [activeProjectId]);
  const refreshJobs = useCallback(async () => {
    if (!projectId) return;
    try { setJobs((await listJobs(projectId)).jobs || []); } catch { /* shown on the next action */ }
  }, [projectId]);
  useEffect(() => { setTaskId(''); setTarget(null); setError(''); refreshJobs(); }, [projectId, refreshJobs]);
  const act = async (fn) => { setBusy(true); setError(''); try { await fn(); await refreshJobs(); } catch (e) { setError(e?.error || 'Request failed.'); } finally { setBusy(false); } };

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaHistory className="h-4 w-4" /> Time Machine</h1>
          <p className="text-xs text-text-muted">Every change has a history. Every failure has an explanation — when the evidence supports one.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {projectId && (<>
        <Timeline projectId={projectId} onTask={setTaskId} />
        <Graph projectId={projectId} taskId={taskId} />
        {taskId && <Replay projectId={projectId} taskId={taskId} busy={busy} onRerun={(t) => act(() => startRerun(projectId, t))} />}
        <Jobs projectId={projectId} jobs={jobs} refresh={refreshJobs} busy={busy} act={act} onRevert={setTarget} />
        <Restore projectId={projectId} target={target} setTarget={setTarget} busy={busy} act={act} />
      </>)}
    </div>
  );
}
