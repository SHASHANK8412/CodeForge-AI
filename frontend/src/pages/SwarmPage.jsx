import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { FaCheck, FaPlay, FaPlus, FaProjectDiagram, FaRocket, FaStop, FaTrash } from 'react-icons/fa';
import {
  cancelMission, createMission, decideConflict, deliverMission, getMission, getMissionReport, listMissions, listSwarmAgents, runMission,
} from '../services/swarm';
import { listAutopilotProjects } from '../services/evolutionAutopilot';

const GOOD = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
const BAD = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
const WARN = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
const GREY = 'bg-slate-700/50 text-slate-300 border-slate-600';
const TONE = {
  completed: GOOD, passed: GOOD, resolved: GOOD, valid: GOOD, ok: GOOD, selected: GOOD, SUCCEEDED: GOOD, repaired: GOOD, succeeded: GOOD,
  failed: BAD, blocked: BAD, invalid: BAD, mismatch: BAD, escalated: WARN, critical: BAD, high: BAD, FAILED: BAD, verified: BAD,
  repair_failed: BAD, BLOCKED: WARN, NEEDS_HUMAN_REVIEW: WARN, needs_human_review: WARN, unresolved: WARN, inconclusive: WARN,
  unverified: GREY, resolved_by_rerun: GREY,
  awaiting_review: WARN, awaiting_decision: WARN, resolving: WARN, medium: WARN, flaky: WARN, unavailable: WARN, interrupted: WARN,
  pending: GREY, planned: GREY, cancelled: GREY, not_applicable: GREY, not_run: GREY, low: GREY, rejected: BAD, escalate: WARN,
};
const ACTIVE = new Set(['running', 'ready']);
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
const split = (s) => s.split(',').map((x) => x.trim()).filter(Boolean);

// --- mission builder -------------------------------------------------------------------------------------------

function Builder({ projectId, agents, busy, act, onCreated }) {
  const [objective, setObjective] = useState('');
  const [constraints, setConstraints] = useState('');
  const [acceptance, setAcceptance] = useState('');
  const [endpoints, setEndpoints] = useState([{ method: 'POST', path: '/api/orders', request_fields: 'item, quantity', response_fields: 'id, item, quantity' }]);
  const [concurrency, setConcurrency] = useState(2);
  const [contractJson, setContractJson] = useState('');
  const set = (i, k) => (e) => setEndpoints(endpoints.map((x, j) => (j === i ? { ...x, [k]: e.target.value } : x)));
  const submit = () => act(async () => {
    let contract = { name: 'api', endpoints: endpoints.map((e) => ({ method: e.method, path: e.path.trim(), request_fields: split(e.request_fields), response_fields: split(e.response_fields) })) };
    if (contractJson.trim()) {
      try { contract = JSON.parse(contractJson); } catch (e) { throw { error: `The contract JSON is not valid: ${e.message}` }; }
    }
    const r = await createMission(projectId, {
      objective, constraints: split(constraints), acceptance: split(acceptance), settings: { concurrency: Number(concurrency) }, contract,
    });
    onCreated(r.mission);
  });
  return (
    <Card title="Mission builder">
      <div className="space-y-2 text-xs text-text-secondary">
        <textarea rows={2} className={`${inputCls} w-full`} placeholder="Engineering objective (e.g. an orders API and the frontend client that uses it)" value={objective} onChange={(e) => setObjective(e.target.value)} />
        <div className="grid gap-2 md:grid-cols-2">
          <input className={inputCls} placeholder="constraints, comma separated" value={constraints} onChange={(e) => setConstraints(e.target.value)} />
          <input className={inputCls} placeholder="acceptance criteria, comma separated" value={acceptance} onChange={(e) => setAcceptance(e.target.value)} />
        </div>
        <p className="text-[10px] uppercase tracking-wide text-text-muted">Shared API contract — both agents implement against it; the Integration Agent checks the code, not the agents' claims</p>
        <table className="w-full text-left text-[11px]"><thead className="text-[10px] uppercase text-text-muted"><tr><th>Method</th><th>Path</th><th>Request fields</th><th>Response fields</th><th /></tr></thead>
          <tbody>{endpoints.map((e, i) => (
            <tr key={i}><td className="pr-1"><select className={inputCls} value={e.method} onChange={set(i, 'method')}>{['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map((m) => <option key={m}>{m}</option>)}</select></td>
              <td className="pr-1"><input className={`${inputCls} w-48 font-mono`} value={e.path} onChange={set(i, 'path')} /></td>
              <td className="pr-1"><input className={`${inputCls} w-40`} value={e.request_fields} onChange={set(i, 'request_fields')} /></td>
              <td className="pr-1"><input className={`${inputCls} w-40`} value={e.response_fields} onChange={set(i, 'response_fields')} /></td>
              <td><button className="text-text-muted" onClick={() => setEndpoints(endpoints.filter((_, j) => j !== i))}><FaTrash className="h-2.5 w-2.5" /></button></td></tr>
          ))}</tbody></table>
        <details><summary className="cursor-pointer text-[11px] text-text-muted">Full contract (JSON Schema per endpoint: path/query params, auth, request schema, responses by status, documented errors) — replaces the table when filled</summary>
          <textarea rows={8} className={`${inputCls} mt-1 w-full font-mono`} value={contractJson} onChange={(e) => setContractJson(e.target.value)}
            placeholder={'{"name": "orders", "endpoints": [{"method": "POST", "path": "/api/orders", "auth": "none",\n  "request_schema": {"type": "object", "properties": {"item": {"type": "string"}}, "required": ["item"]},\n  "responses": {"201": {"content_type": "application/json", "schema": {"type": "object", "required": ["id"]}}},\n  "errors": {"422": {"description": "invalid order"}}}]}'} />
          <p className="text-[10px]">Field-name-only rows (the table) are upgraded automatically: their fields become required properties of open type.</p></details>
        <div className="flex flex-wrap items-center gap-2">
          <Btn onClick={() => setEndpoints([...endpoints, { method: 'GET', path: '/api/', request_fields: '', response_fields: '' }])}><FaPlus className="h-2.5 w-2.5" /> Endpoint</Btn>
          <label className="flex items-center gap-1 text-[11px]">concurrency <input type="number" min="1" max="4" className={`${inputCls} w-14`} value={concurrency} onChange={(e) => setConcurrency(e.target.value)} /></label>
          <Btn tone="primary" disabled={busy || objective.trim().length < 5 || !endpoints.length} onClick={submit}><FaProjectDiagram className="h-2.5 w-2.5" /> Plan mission</Btn>
        </div>
        <details><summary className="cursor-pointer text-[11px] text-text-muted">Agent capability registry ({agents.length})</summary>
          <ul className="mt-1 space-y-0.5 text-[11px]">{agents.map((a) => <li key={a.id}><span className="text-text-primary">{a.title}</span> — {a.capabilities.join(', ')} · tasks {a.task_kinds.join(', ')} · <span className="text-text-muted">limits: {a.limitations.join('; ')}</span></li>)}</ul></details>
      </div>
    </Card>
  );
}

// --- live graph -------------------------------------------------------------------------------------------------

function SwarmGraph({ m }) {
  const layout = useMemo(() => {
    const depth = {};
    const get = (t) => { if (depth[t.id] != null) return depth[t.id]; depth[t.id] = 0; depth[t.id] = t.depends_on.length ? 1 + Math.max(...t.depends_on.map((d) => get(m.tasks.find((x) => x.id === d) || { id: d, depends_on: [] }))) : 0; return depth[t.id]; };
    m.tasks.forEach(get);
    const cols = {};
    const pos = {};
    m.tasks.forEach((t) => { const d = depth[t.id]; cols[d] = (cols[d] || 0) + 1; pos[t.id] = { x: 90 + d * 190, y: 40 + (cols[d] - 1) * 78 }; });
    return { pos, width: 120 + (Math.max(...Object.values(depth), 0) + 1) * 190, height: 60 + Math.max(...Object.values(cols), 1) * 78 };
  }, [m]);
  const fill = { completed: '#065f46', running: '#155e75', failed: '#9f1239', blocked: '#9f1239', awaiting_review: '#92400e', cancelled: '#334155' };
  return (
    <Card title="Live swarm graph" actions={<span className="text-[11px]"><Badge value={m.status} /> {m.error}</span>}>
      <div className="overflow-auto rounded-lg bg-black/30">
        <svg width={layout.width} height={layout.height} className="text-[10px]">
          {m.tasks.flatMap((t) => t.depends_on.map((d) => { const a = layout.pos[d]; const b = layout.pos[t.id]; return a && b ? <line key={d + t.id} x1={a.x + 70} y1={a.y} x2={b.x - 70} y2={b.y} stroke="#64748b" strokeWidth={1.2} /> : null; }))}
          {m.tasks.map((t) => { const p = layout.pos[t.id]; return (
            <g key={t.id}>
              <rect x={p.x - 75} y={p.y - 24} width={150} height={48} rx={8} fill={fill[t.status] || '#1e293b'} />
              <text x={p.x} y={p.y - 8} textAnchor="middle" fill="#e2e8f0">{t.id} · {label(t.kind)}</text>
              <text x={p.x} y={p.y + 6} textAnchor="middle" fill="#94a3b8">{t.agent || 'unassigned'}</text>
              <text x={p.x} y={p.y + 19} textAnchor="middle" fill="#cbd5e1">{label(t.status)} · {t.artifacts.length} artifact(s)</text>
            </g>); })}
        </svg>
      </div>
      <ul className="mt-2 space-y-0.5 text-[11px] text-text-secondary">{m.tasks.filter((t) => t.error || t.feedback).map((t) => <li key={t.id}><span className="font-mono">{t.id}</span>: {t.error || ''} {t.feedback && <span className="text-amber-200">repair request: {t.feedback.slice(0, 200)}</span>}</li>)}</ul>
    </Card>
  );
}

// --- debate, integration, report -------------------------------------------------------------------------------------

function Debate({ m, busy, onDecide }) {
  if (!m.conflicts.length) return null;
  return (
    <Card title="Debate center — conflicts and competing proposals">
      <div className="space-y-2 text-xs text-text-secondary">
        {m.conflicts.map((c) => (
          <div key={c.id} className="rounded-lg border border-border-subtle p-2">
            <p className="flex flex-wrap items-center gap-2"><Badge value={c.status} /><Badge value={c.severity} /><span className="text-text-muted">{label(c.kind)} · {c.components.join(' vs ')}</span></p>
            <p className="mt-1 text-text-primary">{c.detail}</p>
            {c.decision && <p className="mt-1 text-[11px]"><span className="text-text-muted">Decision: </span><Badge value={c.decision.outcome} /> {c.decision.reason} {c.decision.by && `· by ${c.decision.by}`} {c.decision.verified && `· ${c.decision.verified}`}</p>}
            <div className="mt-1 grid gap-2 md:grid-cols-2">{c.proposals.map((p) => {
              const row = (c.decision?.rows || []).find((r) => r.proposal === p.id);
              return (
                <div key={p.id} className="rounded border border-border-subtle p-2 text-[11px]">
                  <p className="text-text-primary">{p.title} {row?.score != null && <span className="text-text-muted">· score {row.score}</span>}</p>
                  {p.violates.length > 0 && <p className="text-rose-200">violates: {p.violates.join('; ')}</p>}
                  <p><span className="text-text-muted">Evidence: </span>{p.evidence.join('; ')}</p>
                  <p><span className="text-text-muted">Risks: </span>{p.risks.join('; ') || '—'}</p>
                  {row && <p className="text-text-muted">{Object.entries(row.breakdown).map(([k, v]) => `${label(k)} ${v.score ?? 'n/a'}×${v.weight}`).join(' · ')}</p>}
                  {c.status === 'escalated' && !p.violates.length && <Btn className="mt-1" tone="good" disabled={busy} onClick={() => onDecide(c.id, p.id)}><FaCheck className="h-2.5 w-2.5" /> Choose this</Btn>}
                </div>
              );
            })}</div>
          </div>
        ))}
        <p className="text-[10px] text-text-muted">Decisions use mandatory constraints and evidence scores; how many agents back a proposal is never counted. Ties or missing evidence go to you.</p>
      </div>
    </Card>
  );
}

function Integration({ m }) {
  const rep = [...m.artifacts].reverse().find((a) => a.kind === 'integration_report');
  if (!rep && !m.gates.length) return null;
  return (
    <Card title="Integration center">
      <div className="space-y-2 text-xs text-text-secondary">
        {rep && <>
          <table className="w-full text-left text-[11px]"><thead className="text-[10px] uppercase text-text-muted"><tr><th className="py-1">Client call</th><th>Where</th><th>Result</th><th>Backend route</th></tr></thead>
            <tbody>{rep.content.calls.map((c, i) => <tr key={i} className="border-t border-border-subtle align-top"><td className="py-1 font-mono">{c.method} {c.path}</td><td>{c.file}:{c.line}</td><td><Badge value={c.status} /> {c.reason}</td><td className="font-mono">{c.route ? `${c.route.method} ${c.route.path} (${c.route.handler})` : '—'}</td></tr>)}</tbody></table>
          <p className="text-[11px]">File owners: {Object.entries(rep.content.file_owners).map(([f, t]) => `${f} → ${t}`).join(' · ')}</p>
        </>}
        {m.gates.length > 0 && <ul className="space-y-0.5">{m.gates.map((g) => <li key={g.name}><Badge value={g.status} /> {g.name}{g.mandatory ? '' : ' (optional)'} — <span className="text-text-muted">{g.detail}</span></li>)}</ul>}
      </div>
    </Card>
  );
}

const PHASES = ['PLANNING', 'CONTRACT_READY', 'PARALLEL_GENERATION', 'STATIC_VALIDATION', 'INTEGRATION_TESTING', 'FAILURE_CLASSIFICATION',
  'REPAIR_REQUIRED', 'REVALIDATION', 'SECURITY_VERIFICATION', 'AUTOPILOT_REVIEW'];

function Lifecycle({ m }) {
  const seen = new Set((m.phase_history || []).map((x) => x.phase));
  return (
    <Card title="Mission lifecycle" actions={<span className="flex items-center gap-2 text-[11px]">outcome <Badge value={m.outcome || 'in progress'} /></span>}>
      <ol className="flex flex-wrap gap-1 text-[10px]">{PHASES.map((ph) => (
        <li key={ph} className={`rounded border px-2 py-0.5 ${m.phase === ph ? 'border-cyan-400 text-cyan-200' : seen.has(ph) ? 'border-emerald-700 text-emerald-300' : 'border-slate-700 text-slate-500'}`}>{label(ph).toLowerCase()}</li>))}</ol>
      <details className="mt-2"><summary className="cursor-pointer text-[11px] text-text-muted">phase_history ({(m.phase_history || []).length})</summary>
        <ul className="text-[11px] text-text-secondary">{(m.phase_history || []).map((x, i) => <li key={i}><span className="font-mono text-text-muted">{x.at.slice(11, 19)}</span> {label(x.phase).toLowerCase()} — {x.note}</li>)}</ul></details>
    </Card>
  );
}

function RuntimeTests({ m }) {
  if (!(m.runtime || []).length) return null;
  return (
    <Card title="Integration testing — runtime contract tests in the isolated environment">
      <div className="space-y-3 text-[11px] text-text-secondary">
        {m.runtime.map((r) => (
          <div key={r.id} className="rounded-lg border border-border-subtle p-2">
            <p className="flex flex-wrap items-center gap-2"><span className="font-mono text-text-primary">{r.id}</span> round {r.round} <Badge value={r.status} />
              <span className="text-text-muted">{r.environment} · {Object.entries(r.counts || {}).map(([k, v]) => `${v} ${k}`).join(', ') || 'no checks'} · {r.seconds}s{r.rerun ? ' · failures re-run once' : ''}</span></p>
            {r.error && <p className="text-rose-200">{r.error}</p>}
            {(r.checks || []).length > 0 && <table className="mt-1 w-full text-left"><thead className="text-[10px] uppercase text-text-muted"><tr><th className="py-1">Check</th><th>Operation</th><th>Result</th><th>Expected / observed</th></tr></thead>
              <tbody>{r.checks.map((c) => <tr key={c.id} className="border-t border-border-subtle align-top"><td className="py-1 font-mono">{c.id}</td><td className="font-mono">{c.endpoint}</td><td><Badge value={c.status} /></td>
                <td><span className="text-text-muted">expected</span> {c.expected}<br /><span className="text-text-muted">observed</span> {c.observed}</td></tr>)}</tbody></table>}
            <p className="mt-1 text-text-muted">Isolation: {r.isolation?.verified === true ? 'verified from Docker' : r.isolation?.verified === false ? 'NOT verified' : 'not inspected'}{(r.egress || []).length > 0 && ` · outside reachable: ${r.egress.filter((x) => x.reachable).length}/${r.egress.length}`} · cleanup: {r.cleanup?.verified ? 'verified' : 'not verified'}</p>
          </div>))}
        {Object.keys(m.properties || {}).length > 0 && <details><summary className="cursor-pointer text-text-muted">Static (code) vs declared (OpenAPI) vs verified (runtime) — the runtime decides</summary><Pre>{JSON.stringify(m.properties, null, 1)}</Pre></details>}
      </div>
    </Card>
  );
}

function Findings({ m }) {
  const items = m.findings || [];
  if (!items.length) return null;
  return (
    <Card title={`Findings (${items.length})`}>
      <table className="w-full text-left text-[11px] text-text-secondary"><thead className="text-[10px] uppercase text-text-muted"><tr><th className="py-1">Status</th><th>Category</th><th>Operation</th><th>Basis</th><th>Responsible</th><th>Expected / observed</th><th>Correction</th></tr></thead>
        <tbody>{items.map((f) => <tr key={f.id} className="border-t border-border-subtle align-top"><td className="py-1"><Badge value={f.status} /><br /><span className="text-text-muted">round {f.round}</span></td>
          <td>{label(f.category)} <Badge value={f.severity} /></td><td className="font-mono">{f.endpoint}</td><td>{f.basis}</td><td>{f.responsible || <span className="text-amber-200">not established</span>}</td>
          <td><span className="text-text-muted">expected</span> {f.expected}<br /><span className="text-text-muted">observed</span> {f.observed}</td><td>{f.recommended_correction}</td></tr>)}</tbody></table>
      <p className="mt-1 text-[10px] text-text-muted">Verified = observed by a runtime check with an established responsible component. Static and declared findings stay unverified until a runtime check confirms them; agents' statements are never evidence.</p>
    </Card>
  );
}

function Repairs({ m }) {
  if (!(m.repairs || []).length) return null;
  return (
    <Card title="Repair history (at most one automatic repair per mismatch)">
      <ul className="space-y-2 text-[11px] text-text-secondary">{m.repairs.map((r) => (
        <li key={r.id} className="rounded-lg border border-border-subtle p-2">
          <p className="flex flex-wrap items-center gap-2"><span className="font-mono text-text-primary">{r.id}</span> {r.component} <Badge value={r.outcome} />
            <span className="text-text-muted">requested by {r.requested_by} at {r.requested_at.slice(0, 19)} · author {r.author || '—'} · {r.artifact_before} → {r.artifact_after || '…'}</span></p>
          <p>changed: {r.changed_files.join(', ') || '—'} · remaining mismatches: {(r.validation?.mismatches_remaining || []).length} · security after repair: {r.validation?.security_after_repair || '—'}</p>
          <details><summary className="cursor-pointer text-text-muted">repair request (evidence sent to the agent)</summary><Pre>{r.request}</Pre></details>
        </li>))}</ul>
    </Card>
  );
}

function AutopilotReview({ m, onDownload, busy }) {
  const r = m.autopilot_review || {};
  if (!r.outcome) return null;
  return (
    <Card title="Autopilot review" actions={<span className="flex gap-1"><Btn disabled={busy} onClick={() => onDownload('markdown')}>Report (md)</Btn><Btn disabled={busy} onClick={() => onDownload('json')}>Report (json)</Btn></span>}>
      <div className="grid gap-2 text-[11px] text-text-secondary md:grid-cols-2">
        <p>Outcome <Badge value={r.outcome} /> · contract version <span className="font-mono">{r.contract_version}</span></p>
        <p>Approval: {r.approval_status} · project modified: {String(r.project_modified)} · deployed: {String(r.deployed)}</p>
        <p>Backend version: <span className="font-mono">{r.backend_version ? `${r.backend_version.artifact} (v${r.backend_version.version}, ${r.backend_version.content_hash})` : '—'}</span></p>
        <p>Frontend version: <span className="font-mono">{r.frontend_version ? `${r.frontend_version.artifact} (v${r.frontend_version.version}, ${r.frontend_version.content_hash})` : '—'}</span></p>
        <p>Integration tests: {r.integration_tests?.status} {JSON.stringify(r.integration_tests?.counts || {})}</p>
        <p>Security: {r.security?.status || '—'} · isolation: {r.isolation?.status || '—'} · generated tests: {r.generated_tests?.status || '—'}</p>
      </div>
      <p className="mt-2 text-[10px] uppercase text-text-muted">Proposed actions</p>
      <ul className="text-[11px] text-text-secondary">{(r.proposed_actions || []).map((a, i) => <li key={i}>• {a}</li>)}</ul>
    </Card>
  );
}

function Timeline({ m }) {
  return (
    <Card title={`Collaboration timeline (${m.messages.length} messages)`}>
      <ul className="max-h-72 space-y-0.5 overflow-auto text-[11px] text-text-secondary">{[...m.messages].reverse().map((x) => (
        <li key={x.id}><span className="font-mono text-text-muted">{x.at.slice(11, 19)}</span> <span className="text-text-primary">{x.sender}</span> → {x.recipient} <Badge value={x.type} /> {x.summary}{x.artifact_refs.length > 0 && <span className="text-text-muted"> [{x.artifact_refs.join(', ')}]</span>}</li>
      ))}</ul>
      <details className="mt-2"><summary className="cursor-pointer text-[11px] text-text-muted">Artifacts ({m.artifacts.length}) with provenance</summary>
        <table className="w-full text-left text-[11px]"><thead className="text-[10px] uppercase text-text-muted"><tr><th className="py-1">Artifact</th><th>Kind</th><th>Creator / task</th><th>Validation</th><th>Hash</th></tr></thead>
          <tbody>{m.artifacts.map((a) => <tr key={a.id} className="border-t border-border-subtle"><td className="py-1 font-mono">{a.id}{a.supersedes && <span className="text-text-muted"> (supersedes {a.supersedes})</span>}</td><td>{label(a.kind)}</td><td>{a.creator} / {a.task_id}</td><td><Badge value={a.validation} /> {a.validation_errors.join('; ')}</td><td className="font-mono text-text-muted">{a.content_hash.slice(0, 10)}</td></tr>)}</tbody></table></details>
    </Card>
  );
}

function Report({ m, busy, onDeliver }) {
  const r = m.report || {};
  if (!r.status) return null;
  return (
    <Card title="Final report" actions={m.status === 'completed' && !m.delivery?.autopilot_plan_id && <Btn tone="primary" disabled={busy} onClick={onDeliver}><FaRocket className="h-2.5 w-2.5" /> Deliver as an Autopilot plan</Btn>}>
      <div className="grid gap-2 text-[11px] text-text-secondary md:grid-cols-2">
        <div><p className="text-text-muted">Completed tasks</p>{(r.completed_tasks || []).map((x) => <p key={x}>✓ {x}</p>)}</div>
        <div><p className="text-text-muted">Failed / blocked tasks</p>{(r.failed_tasks || []).map((x) => <p key={x} className="text-rose-200">✗ {x}</p>)}{!r.failed_tasks?.length && <p>none</p>}</div>
        <div><p className="text-text-muted">Unresolved conflicts</p>{(r.unresolved_conflicts || []).map((x) => <p key={x}>{x}</p>)}{!r.unresolved_conflicts?.length && <p>none</p>}</div>
        <div><p className="text-text-muted">Known limitations</p>{(r.limitations || []).map((x) => <p key={x}>• {x}</p>)}</div>
      </div>
      {m.delivery?.autopilot_plan_id && <p className="mt-2 text-xs text-emerald-200">{m.delivery.kind === 'review' ? 'Review' : 'Delivery'} plan {m.delivery.autopilot_plan_id} is awaiting approval in Autopilot{m.delivery.files?.length ? ` (${m.delivery.files.join(', ')})` : ' (proposed actions only)'}. Nothing has been written to the project.</p>}
    </Card>
  );
}

// --- page --------------------------------------------------------------------------------------------------------------

/**
 * AIForge Swarm Intelligence: specialised agents work on one mission's task graph in parallel, exchange validated
 * artifacts, challenge each other (Critical Reviewer), resolve conflicts by evidence (or by you), and integrate only
 * what passes real tests. Everything shown is stored mission state.
 */
export default function SwarmPage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [agents, setAgents] = useState([]);
  const [missions, setMissions] = useState([]);
  const [selected, setSelected] = useState('');
  const [m, setM] = useState(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listSwarmAgents().then((r) => setAgents(r.agents || [])).catch(() => {});
    listAutopilotProjects().then((r) => {
      setProjects(r.projects || []);
      const preferred = (r.projects || []).find((p) => p.project_id === activeProjectId);
      setProjectId((cur) => cur || preferred?.project_id || r.projects?.[0]?.project_id || '');
    }).catch((e) => setError(e?.error || 'Could not load projects.'));
  }, [activeProjectId]);
  const refresh = useCallback(async () => {
    if (!projectId) return;
    try { const r = await listMissions(projectId); setMissions(r.missions || []); setSelected((cur) => cur || r.missions?.[0]?.id || ''); }
    catch (e) { setError(e?.error || 'Could not load missions.'); }
  }, [projectId]);
  useEffect(() => { setSelected(''); setM(null); refresh(); }, [projectId, refresh]);
  const load = useCallback(async () => {
    if (!selected) return;
    try { setM((await getMission(projectId, selected)).mission); } catch (e) { setError(e?.error || 'Could not load the mission.'); }
  }, [projectId, selected]);
  useEffect(() => { setConsent(false); load(); }, [load]);
  useEffect(() => {
    if (!m || m.status !== 'running') return undefined;
    const t = setInterval(() => { load(); refresh(); }, 2500);
    return () => clearInterval(t);
  }, [m, load, refresh]);
  const act = async (fn) => { setBusy(true); setError(''); try { await fn(); await refresh(); await load(); } catch (e) { setError(e?.error || 'Request failed.'); } finally { setBusy(false); } };

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaProjectDiagram className="h-4 w-4" /> Swarm Intelligence</h1>
          <p className="text-xs text-text-muted">One problem. Multiple AI engineers. One verified solution — verified by tests, not by agreement.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {projectId && (<>
        <Builder projectId={projectId} agents={agents} busy={busy} act={act} onCreated={(x) => setSelected(x.id)} />
        {missions.length > 0 && <Card title="Missions">
          <ul className="space-y-1 text-[11px] text-text-secondary">{missions.map((x) => (
            <li key={x.id} className="flex flex-wrap items-center gap-2"><Badge value={x.outcome || x.status} /><span className="text-text-primary">{x.objective.slice(0, 90)}</span>
              <span className="text-text-muted">{new Date(x.created_at).toLocaleString()} · {x.conflicts} conflict(s)</span><Btn onClick={() => setSelected(x.id)}>Open</Btn></li>))}</ul>
        </Card>}
        {m && (<>
          {m.plan_errors.length > 0 && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">Plan rejected: {m.plan_errors.join('; ')}</p>}
          {['planned', 'interrupted', 'blocked'].includes(m.status) && (
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-xs">
              <label className="flex items-center gap-1.5 text-amber-100"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                I approve running these agents: they generate code with the local model and run it only in isolated copies, the Docker sandbox and an internal Docker network (backend + node client harness)</label>
              <Btn tone="good" disabled={busy || !consent} onClick={() => act(() => runMission(projectId, m.id))}><FaPlay className="h-2.5 w-2.5" /> {m.status === 'planned' ? 'Run' : 'Resume'} mission</Btn>
            </div>
          )}
          {m.status === 'running' && <Btn tone="bad" disabled={busy || m.cancel_requested} onClick={() => act(() => cancelMission(projectId, m.id))}><FaStop className="h-2.5 w-2.5" /> {m.cancel_requested ? 'Cancelling…' : 'Cancel mission'}</Btn>}
          <Lifecycle m={m} />
          <SwarmGraph m={m} />
          <RuntimeTests m={m} />
          <Findings m={m} />
          <Repairs m={m} />
          <Debate m={m} busy={busy} onDecide={(c, p) => act(() => decideConflict(projectId, m.id, c, p))} />
          <Integration m={m} />
          <Timeline m={m} />
          <Report m={m} busy={busy} onDeliver={() => act(() => deliverMission(projectId, m.id))} />
          <AutopilotReview m={m} busy={busy} onDownload={(format) => act(async () => {
            const r = await getMissionReport(projectId, m.id, format);
            const blob = new Blob([format === 'json' ? JSON.stringify(r, null, 2) : r], { type: format === 'json' ? 'application/json' : 'text/markdown' });
            const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `swarm-${m.id}.${format === 'json' ? 'json' : 'md'}`; a.click();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
          })} />
          {m.contract && <details className="text-[11px] text-text-muted"><summary className="cursor-pointer">Mission contract and settings</summary><Pre>{JSON.stringify({ contract: m.contract, settings: m.settings, constraints: m.constraints, acceptance: m.acceptance }, null, 1)}</Pre></details>}
        </>)}
      </>)}
    </div>
  );
}
