import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { FaSync, FaSearch, FaPlay, FaCheck, FaTimes, FaPlus, FaExclamationTriangle } from 'react-icons/fa';
import {
  createPlanFromReport, getDependencies, getImpactReport, getLatestTwinAnalysis, getReportOutcome, getTwinAccuracy,
  getTwinGraph, listImpactReports, simulateChange, startTwinAnalysis,
} from '../services/digitalTwin';
import { decidePlan, executePlan, listAutopilotProjects, listExecutions, listPlans } from '../services/evolutionAutopilot';

const TYPE_COLOR = {
  file: '#6366F1', test: '#10B981', config: '#94A3B8', function: '#06B6D4', class: '#0EA5E9', model: '#F59E0B',
  route: '#F43F5E', component: '#8D5CF6', package: '#64748B',
};
const RISK_TONE = {
  low: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  medium: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  high: 'bg-orange-500/20 text-orange-200 border-orange-500/40',
  critical: 'bg-rose-500/20 text-rose-200 border-rose-500/40',
};
const STATUS_TONE = {
  completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  approved: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  failed: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  rejected: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  running: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  queued: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  awaiting_approval: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  needs_approval: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  established: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25',
  inferred: 'bg-amber-500/10 text-amber-300 border-amber-500/25',
};
const ACTIVE = new Set(['queued', 'running']);
const label = (s) => String(s ?? '').replace(/_/g, ' ');
const short = (p) => (p && p.length > 34 ? `…${p.slice(-33)}` : p);

const Badge = ({ value, tone }) => (
  <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${tone || STATUS_TONE[value] || RISK_TONE[value] || 'border-slate-700 bg-slate-800 text-slate-400'}`}>
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

const Stat = ({ name, value }) => (
  <div className="rounded-xl bg-bg-base/60 px-3 py-2">
    <p className="text-[10px] uppercase tracking-wide text-text-muted">{name}</p>
    <p className="mt-0.5 text-sm font-semibold text-text-primary">{value}</p>
  </div>
);

const Section = ({ title, children, empty }) => (
  <div>
    <p className="mb-1 text-[10px] uppercase tracking-wide text-text-muted">{title}</p>
    {children || <p className="text-xs text-text-muted">{empty || 'none'}</p>}
  </div>
);

// --- overview ---------------------------------------------------------------------------------------

function Overview({ latest, onAnalyze, busy }) {
  const a = latest?.analysis;
  const s = a?.stats || {};
  return (
    <Card title="Project overview" actions={
      <div className="flex items-center gap-2">
        {latest?.stale && <Badge value="graph out of date" tone="bg-amber-500/15 text-amber-300 border-amber-500/30" />}
        <Btn tone="primary" disabled={busy || !!latest?.active_job} onClick={onAnalyze}>
          <FaSync className={`h-2.5 w-2.5 ${ACTIVE.has(a?.status) ? 'animate-spin' : ''}`} /> {a ? 'Rebuild graph' : 'Build graph'}
        </Btn>
      </div>
    }>
      {!a && <p className="text-xs text-text-muted">No dependency graph yet. Building it reads the source files (Python ast, JS/TS imports); nothing is executed.</p>}
      {a && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-text-muted">
            <Badge value={a.status} />
            <span>last analysis {a.finished_at ? new Date(a.finished_at).toLocaleString() : '-'}</span>
            {a.error && <span className="text-rose-300">{a.error}</span>}
          </div>
          {a.status === 'completed' && (
            <>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7">
                <Stat name="Technologies" value={(s.stack || []).join(', ') || '-'} />
                <Stat name="Files analyzed" value={`${s.parsed_files ?? 0} / ${s.files ?? 0}`} />
                <Stat name="Nodes" value={s.nodes ?? 0} />
                <Stat name="Relationships" value={s.edges ?? 0} />
                <Stat name="Inferred" value={s.inferred_edges ?? 0} />
                <Stat name="Unresolved imports" value={s.unresolved ?? 0} />
                <Stat name="Import cycles" value={s.cycles ?? 0} />
              </div>
              {a.limits?.length > 0 && (
                <ul className="list-disc space-y-0.5 pl-4 text-[11px] text-text-muted">{a.limits.map((l, i) => <li key={i}>{l}</li>)}</ul>
              )}
            </>
          )}
        </div>
      )}
    </Card>
  );
}

// --- dependency explorer ------------------------------------------------------------------------------

const COL_LIMIT = 12;

function GraphView({ focus, outgoing, incoming, onSelect }) {
  // Columns: indirect dependencies | dependencies | focus | dependents | indirect dependents
  const cols = [
    outgoing.filter((n) => n.distance === 2), outgoing.filter((n) => n.distance === 1), [focus],
    incoming.filter((n) => n.distance === 1), incoming.filter((n) => n.distance === 2),
  ].map((c) => c.slice(0, COL_LIMIT));
  const hidden = [outgoing.filter((n) => n.distance === 2).length, outgoing.filter((n) => n.distance === 1).length, 0,
    incoming.filter((n) => n.distance === 1).length, incoming.filter((n) => n.distance === 2).length]
    .map((n, i) => Math.max(0, n - cols[i].length));
  // Only columns that have nodes take space (the focus column always does).
  const shown = cols.map((c, i) => i === 2 || c.length > 0);
  const order = shown.map((s, i) => (s ? i : -1)).filter((i) => i >= 0);
  const colW = 195;
  const W = order.length * colW;
  const xs = cols.map((_, i) => (order.indexOf(i) >= 0 ? colW / 2 + order.indexOf(i) * colW : -1000));
  const rowH = 34; const H = Math.max(120, Math.max(...cols.map((c) => c.length)) * rowH + 50);
  const pos = {};
  cols.forEach((c, i) => c.forEach((n, j) => { pos[`${i}:${n.id}`] = { x: xs[i], y: 40 + j * rowH + (H - 50 - c.length * rowH) / 2 }; }));
  const at = (i, id) => pos[`${i}:${id}`];
  const lines = [];
  const link = (a, b, edge, key) => a && b && lines.push({ a, b, edge, key });
  cols[1].forEach((n) => link(at(2, focus.id), at(1, n.id), n.via, `o1${n.id}`));
  cols[0].forEach((n) => { const p = cols[1].find((m) => n.parents?.includes(m.id)); link(at(1, p?.id), at(0, n.id), n.via, `o2${n.id}`); });
  cols[3].forEach((n) => link(at(3, n.id), at(2, focus.id), n.via, `i1${n.id}`));
  cols[4].forEach((n) => { const p = cols[3].find((m) => n.parents?.includes(m.id)); link(at(4, n.id), at(3, p?.id), n.via, `i2${n.id}`); });
  const name = (n) => (n.symbol && n.type !== 'file' ? n.symbol : short(n.path || n.id));
  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} style={{ minWidth: `${order.length * 150}px`, maxWidth: `${W}px` }} className="w-full" role="img" aria-label="Dependency graph around the selected node">
        {['indirect dependencies', 'uses', 'selected', 'used by', 'indirectly used by'].map((t, i) => shown[i] && (
          <text key={t} x={xs[i]} y={16} textAnchor="middle" className="fill-slate-500" fontSize="10">{t.toUpperCase()}</text>
        ))}
        {lines.map(({ a, b, edge, key }) => (
          <path key={key} d={`M${a.x},${a.y} C${(a.x + b.x) / 2},${a.y} ${(a.x + b.x) / 2},${b.y} ${b.x},${b.y}`}
                fill="none" stroke={edge?.certainty === 'inferred' ? '#F59E0B' : '#475569'} strokeOpacity="0.7"
                strokeDasharray={edge?.certainty === 'inferred' ? '4 3' : undefined} strokeWidth="1.2">
            <title>{edge ? `${edge.type} (${edge.certainty})\n${edge.evidence}` : ''}</title>
          </path>
        ))}
        {cols.map((c, i) => c.map((n) => {
          const p = at(i, n.id);
          const isFocus = i === 2;
          return (
            <g key={`${i}:${n.id}`} transform={`translate(${p.x},${p.y})`} className="cursor-pointer" onClick={() => !isFocus && onSelect(n.id)}>
              <rect x={-85} y={-12} width={170} height={24} rx={7} fill={isFocus ? '#1E2330' : '#0F1117'}
                    stroke={TYPE_COLOR[n.type] || '#64748B'} strokeWidth={isFocus ? 2 : 1} />
              <circle cx={-74} cy={0} r={3.5} fill={TYPE_COLOR[n.type] || '#64748B'} />
              <text x={-66} y={4} fontSize="10" className="fill-slate-200">{name(n).slice(0, 26)}</text>
              <title>{`${n.type}: ${n.path || ''}${n.symbol ? ` · ${n.symbol}` : ''}`}</title>
            </g>
          );
        }))}
        {hidden.map((h, i) => h > 0 && (
          <text key={`h${i}`} x={xs[i]} y={H - 6} textAnchor="middle" fontSize="10" className="fill-slate-500">+{h} more</text>
        ))}
      </svg>
      <div className="mt-1 flex flex-wrap gap-3 text-[10px] text-text-muted">
        {Object.entries(TYPE_COLOR).map(([t, c]) => <span key={t} className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: c }} />{t}</span>)}
        <span className="flex items-center gap-1"><span className="inline-block w-5 border-t border-dashed border-amber-500" />inferred</span>
      </div>
    </div>
  );
}

function layer(resp, focusId, direction) {
  // distance-1 and distance-2 nodes in one direction, each with the edge that reaches it from the previous layer
  const byId = Object.fromEntries((resp?.nodes || []).map((n) => [n.id, n]));
  const out = [];
  (resp?.nodes || []).forEach((n) => {
    if (n.id === focusId || n.distance > 2) return;
    const edges = (resp.edges || []).filter((e) => (direction === 'out' ? e.target === n.id : e.source === n.id));
    const parentEdges = edges.filter((e) => {
      const other = direction === 'out' ? e.source : e.target;
      return byId[other] && byId[other].distance === n.distance - 1;
    });
    const via = parentEdges[0] || edges[0];
    out.push({ ...n, via, parents: parentEdges.map((e) => (direction === 'out' ? e.source : e.target)) });
  });
  return out.sort((a, b) => (a.type + (a.path || '')).localeCompare(b.type + (b.path || '')));
}

function Explorer({ projectId, version, onAddTarget, onError }) {
  const [filters, setFilters] = useState({ type: 'file,test', language: '' });
  const [q, setQ] = useState('');
  const [nodes, setNodes] = useState({ nodes: [], total: 0 });
  const [selected, setSelected] = useState('');
  const [view, setView] = useState(null);

  useEffect(() => {
    const params = { limit: 300 };
    if (filters.type) params.type = filters.type;
    if (filters.language) params.language = filters.language;
    if (q.trim()) params.q = q.trim();
    getTwinGraph(projectId, params).then(setNodes).catch((e) => { if (e?.status !== 404) onError(e?.error || 'Could not load the graph.'); });
  }, [projectId, filters, q, version, onError]);

  useEffect(() => {
    if (!selected) { setView(null); return; }
    Promise.all([getDependencies(projectId, selected, { depth: 2, direction: 'out', limit: 80 }),
      getDependencies(projectId, selected, { depth: 2, direction: 'in', limit: 80 })])
      .then(([o, i]) => {
        if (!o.files) {
          setView({ focus: o.focus, outgoing: layer(o, selected, 'out'), incoming: layer(i, selected, 'in'), files: null });
          return;
        }
        // A file: show file-level links, which include uses of the symbols it defines.
        const asNode = (d, distance, parents = []) => ({
          id: `file:${d.path}`, type: d.path.match(/(^|\/)(test_[^/]*\.py|[^/]*_test\.py|[^/]*\.(test|spec)\.\w+)$/) ? 'test' : 'file',
          path: d.path, distance, parents, via: { type: d.type || 'depends', certainty: d.certainty, evidence: d.evidence || (d.chain || []).join(' → ') },
        });
        setView({
          focus: o.focus, files: o.files,
          outgoing: o.files.dependencies.map((d) => asNode(d, 1)),
          incoming: [...o.files.dependents.map((d) => asNode(d, 1)),
            ...o.files.indirect_dependents.filter((d) => d.depth === 2).map((d) => asNode(d, 2, [`file:${d.chain[d.chain.length - 2]}`]))],
        });
      })
      .catch((e) => onError(e?.error || 'Could not load dependencies.'));
  }, [projectId, selected, version, onError]);

  return (
    <Card title="Dependency explorer">
      <div className="grid gap-3 lg:grid-cols-[18rem_1fr]">
        <div className="space-y-2">
          <div className="flex items-center gap-1 rounded-lg border border-border-dark bg-bg-base px-2">
            <FaSearch className="h-2.5 w-2.5 text-text-muted" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="search files and symbols"
                   className="w-full bg-transparent py-1.5 text-xs text-text-primary outline-none" />
          </div>
          <div className="flex gap-2">
            <select value={filters.type} onChange={(e) => setFilters((f) => ({ ...f, type: e.target.value }))}
                    className="flex-1 rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-[11px] text-text-secondary">
              <option value="file,test">files &amp; tests</option>
              {Object.keys(TYPE_COLOR).map((t) => <option key={t} value={t}>{t}</option>)}
              <option value="">all types</option>
            </select>
            <select value={filters.language} onChange={(e) => setFilters((f) => ({ ...f, language: e.target.value }))}
                    className="flex-1 rounded-lg border border-border-dark bg-bg-base px-2 py-1 text-[11px] text-text-secondary">
              <option value="">any language</option><option value="python">python</option><option value="javascript">javascript/ts</option>
            </select>
          </div>
          <ul className="max-h-[26rem] space-y-0.5 overflow-auto pr-1">
            {nodes.nodes.map((n) => (
              <li key={n.id}>
                <button onClick={() => setSelected(n.id)}
                        className={`flex w-full items-center gap-2 rounded-lg px-2 py-1 text-left text-[11px] ${selected === n.id ? 'bg-accent-blue/15 text-text-primary' : 'text-text-secondary hover:bg-surface-hover'}`}>
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: TYPE_COLOR[n.type] }} />
                  <span className="min-w-0 flex-1 truncate font-mono">{n.symbol && n.type !== 'file' && n.type !== 'test' ? `${n.symbol} · ${n.path || ''}` : n.path || n.symbol}</span>
                  <span className="shrink-0 text-[10px] text-text-muted" title="used by / uses">{n.in_degree}/{n.out_degree}</span>
                </button>
              </li>
            ))}
          </ul>
          {nodes.total > nodes.nodes.length && <p className="text-[10px] text-text-muted">showing {nodes.nodes.length} of {nodes.total}; refine the search</p>}
        </div>
        <div className="min-w-0">
          {!view && <p className="text-xs text-text-muted">Select a file or symbol to see what it uses and what depends on it.</p>}
          {view && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-xs text-text-primary"><span className="text-text-muted">{view.focus.type}</span> <span className="font-mono">{view.focus.path}{view.focus.symbol && view.focus.type !== 'file' ? ` · ${view.focus.symbol}` : ''}</span></p>
                {view.focus.path && <Btn onClick={() => onAddTarget(view.focus.path)}><FaPlus className="h-2.5 w-2.5" /> Add to change targets</Btn>}
              </div>
              <GraphView focus={view.focus} outgoing={view.outgoing} incoming={view.incoming} onSelect={setSelected} />
              {view.files && (
                <div className="grid gap-3 text-[11px] md:grid-cols-3">
                  {[['Direct dependencies', view.files.dependencies], ['Direct dependents', view.files.dependents]].map(([t, list]) => (
                    <Section key={t} title={`${t} (${list.length})`}>
                      {list.length > 0 && <ul className="space-y-1">{list.map((d) => (
                        <li key={d.path} title={d.evidence}><button className="font-mono text-text-primary hover:underline" onClick={() => setSelected(`file:${d.path}`)}>{d.path}</button> <span className="text-text-muted">{d.type}</span> {d.certainty === 'inferred' && <Badge value="inferred" />}</li>
                      ))}</ul>}
                    </Section>
                  ))}
                  <Section title={`Indirect dependents (${view.files.indirect_dependents.length})`}>
                    {view.files.indirect_dependents.length > 0 && <ul className="space-y-1">{view.files.indirect_dependents.map((d) => (
                      <li key={d.path} title={d.chain.join(' → ')}><span className="font-mono text-text-primary">{d.path}</span> <span className="text-text-muted">depth {d.depth}</span> {d.certainty === 'inferred' && <Badge value="inferred" />}</li>
                    ))}</ul>}
                  </Section>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

// --- simulation -------------------------------------------------------------------------------------------

function SimulationForm({ targets, setTargets, onSubmit, busy }) {
  const [request, setRequest] = useState('');
  const [alts, setAlts] = useState([]);
  const [useModel, setUseModel] = useState(false);
  const [newTarget, setNewTarget] = useState('');
  const submit = () => onSubmit({ request, target_files: targets, alternatives: alts.filter((a) => a.trim()), use_model: useModel });
  return (
    <Card title="Change simulation (read-only)">
      <div className="space-y-2">
        <textarea value={request} onChange={(e) => setRequest(e.target.value)} rows={2} placeholder="e.g. Add Google login without breaking the existing login"
                  className="w-full rounded-lg border border-border-dark bg-bg-base px-3 py-2 text-xs text-text-primary outline-none" />
        {alts.map((a, i) => (
          <div key={i} className="flex gap-2">
            <textarea value={a} rows={1} onChange={(e) => setAlts((xs) => xs.map((x, j) => (j === i ? e.target.value : x)))}
                      placeholder={`Alternative ${String.fromCharCode(66 + i)}: another way to make the change`}
                      className="flex-1 rounded-lg border border-border-dark bg-bg-base px-3 py-1.5 text-xs text-text-primary outline-none" />
            <Btn onClick={() => setAlts((xs) => xs.filter((_, j) => j !== i))}><FaTimes className="h-2.5 w-2.5" /></Btn>
          </div>
        ))}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] uppercase tracking-wide text-text-muted">Target files</span>
          {targets.map((t) => (
            <span key={t} className="flex items-center gap-1 rounded-full border border-border-dark px-2 py-0.5 font-mono text-[10px] text-text-secondary">
              {t}<button onClick={() => setTargets(targets.filter((x) => x !== t))}><FaTimes className="h-2 w-2" /></button>
            </span>
          ))}
          <input value={newTarget} onChange={(e) => setNewTarget(e.target.value)} placeholder="path/to/file.py"
                 onKeyDown={(e) => { if (e.key === 'Enter' && newTarget.trim()) { setTargets([...new Set([...targets, newTarget.trim()])]); setNewTarget(''); } }}
                 className="w-40 rounded-lg border border-border-dark bg-bg-base px-2 py-0.5 font-mono text-[10px] text-text-primary outline-none" />
          {!targets.length && <span className="text-[10px] text-text-muted">optional: without targets they are inferred from the request</span>}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-1.5 text-[11px] text-text-secondary" title="Ask the local planner model to map the request onto files; its answer is checked against the graph.">
            <input type="checkbox" checked={useModel} onChange={(e) => setUseModel(e.target.checked)} /> use planner model
          </label>
          {alts.length < 2 && <Btn onClick={() => setAlts([...alts, ''])}><FaPlus className="h-2.5 w-2.5" /> Compare an alternative</Btn>}
          <Btn tone="primary" disabled={busy || request.trim().length < 3} onClick={submit}><FaPlay className="h-2.5 w-2.5" /> Simulate</Btn>
          <span className="text-[10px] text-text-muted">Reads the graph only: no code runs and no file is changed.</span>
        </div>
      </div>
    </Card>
  );
}

const PathList = ({ items, render }) => (
  items?.length ? <ul className="space-y-1">{items.map(render)}</ul> : null
);

function OptionDetail({ o }) {
  return (
    <div className="space-y-4 text-xs text-text-secondary">
      <div className="flex flex-wrap items-center gap-2">
        <Badge value={o.risk} /><span className="text-text-muted">{o.risk_points} risk points</span>
        {o.security_review && <Badge value="security review required" tone="bg-rose-500/15 text-rose-200 border-rose-500/30" />}
        {o.change_kinds.map((k) => <Badge key={k} value={k} tone="border-border-dark bg-bg-base text-text-secondary" />)}
      </div>
      {o.uncertainties.length > 0 && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-amber-100">
          {o.uncertainties.map((u, i) => <p key={i} className="flex gap-1.5"><FaExclamationTriangle className="mt-0.5 h-2.5 w-2.5 shrink-0" />{u}</p>)}
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        <Section title={`Expected modification scope (${o.modify_scope.length})`}>
          <PathList items={o.seeds} render={(s) => <li key={s.path}><span className="font-mono text-text-primary">{s.path}</span> <span className="text-text-muted">— {s.source}: {s.reason}</span></li>} />
          {o.create_scope.length > 0 && <p className="mt-1">New files may be created in: <span className="font-mono">{o.create_scope.join(', ')}</span></p>}
        </Section>
        <Section title={`Directly affected (${o.direct.length})`}>
          <PathList items={o.direct} render={(d) => <li key={d.path} title={d.evidence}><span className="font-mono text-text-primary">{d.path}</span> <span className="text-text-muted">{d.via}</span> {d.certainty === 'inferred' && <Badge value="inferred" />}</li>} />
        </Section>
        <Section title={`Transitively affected (${o.transitive.length})`}>
          <PathList items={o.transitive} render={(d) => <li key={d.path} title={d.chain.join(' → ')}><span className="font-mono text-text-primary">{d.path}</span> <span className="text-text-muted">depth {d.depth}</span> {d.certainty === 'inferred' && <Badge value="inferred" />}</li>} />
        </Section>
        <Section title={`APIs (${o.apis.length})`}>
          <PathList items={o.apis} render={(a) => <li key={a.route + a.file}><span className="font-mono text-text-primary">{a.route}</span> <span className="text-text-muted">{a.file} — {a.relation}{a.frontend_callers.length ? `; called from ${a.frontend_callers.join(', ')} (URL match)` : ''}</span></li>} />
        </Section>
        <Section title={`Models (${o.models.length})`}>
          <PathList items={o.models} render={(m) => <li key={m.model + m.file}><span className="text-text-primary">{m.model}</span> <span className="text-text-muted">{m.kind} · {m.file} — {m.relation}</span></li>} />
        </Section>
        <Section title={`Components (${o.components.length})`}>
          <PathList items={o.components} render={(c) => <li key={c.component + c.file}><span className="text-text-primary">{c.component}</span> <span className="text-text-muted">{c.file}{c.rendered_by.length ? ` · rendered by ${c.rendered_by.join(', ')}` : ''}</span></li>} />
        </Section>
        <Section title={`Interfaces other files use (${o.interfaces_at_risk.length})`} empty="none: no other file uses symbols from the changed files">
          <PathList items={o.interfaces_at_risk} render={(i) => <li key={i.symbol + i.file}><span className="font-mono text-text-primary">{i.symbol}</span> <span className="text-text-muted">({i.type}) used by {i.used_by.join(', ')}</span></li>} />
        </Section>
        <Section title={`Configuration (${o.configs.length})`}>
          <PathList items={o.configs} render={(c) => <li key={c.file}><span className="font-mono text-text-primary">{c.file}</span> <span className="text-text-muted">— {c.reason}</span></li>} />
        </Section>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Section title="Risk factors">
          <table className="w-full text-left text-[11px]">
            <tbody>{o.risk_factors.map((f, i) => (
              <tr key={i} className="border-t border-border-subtle align-top"><td className="py-1 pr-2 text-text-primary">{f.factor}</td><td className="pr-2 font-mono">+{f.points}</td><td>{f.reason}</td></tr>
            ))}</tbody>
          </table>
          <p className="mt-1 text-[10px] text-text-muted">0–3 low · 4–7 medium · 8–11 high · 12+ critical. A ranking for review effort, not a measured failure probability.</p>
        </Section>
        <Section title={`Selected tests (${o.tests.length})`} empty="no tests are linked to the affected files">
          <PathList items={o.tests} render={(t) => <li key={t.path}><span className="font-mono text-text-primary">{t.path}</span> <Badge value={t.kind} tone="border-border-dark bg-bg-base text-text-secondary" /> {t.certainty === 'inferred' && <Badge value="inferred" />}<p className="text-[10px] text-text-muted">{t.reasons.join('; ')}</p></li>} />
          {o.untested.length > 0 && <p className="mt-1 text-amber-200">No test linked to: <span className="font-mono">{o.untested.join(', ')}</span></p>}
        </Section>
      </div>
      <Section title="Recommended validation steps">
        <ol className="list-decimal space-y-0.5 pl-4">{o.validation_steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
      </Section>
    </div>
  );
}

function Comparison({ options }) {
  return (
    <table className="w-full text-left text-[11px]">
      <thead className="text-[10px] uppercase tracking-wide text-text-muted">
        <tr><th className="py-1 pr-2">Option</th><th className="pr-2">Files changed</th><th className="pr-2">Affected</th><th className="pr-2">APIs</th><th className="pr-2">Tests</th><th className="pr-2">Uncertainties</th><th>Risk</th></tr>
      </thead>
      <tbody>{options.map((o) => (
        <tr key={o.label} className="border-t border-border-subtle">
          <td className="py-1 pr-2 text-text-primary">{o.label}<p className="text-[10px] text-text-muted">{o.request.slice(0, 80)}</p></td>
          <td className="pr-2">{o.modify_scope.length}</td><td className="pr-2">{o.direct.length + o.transitive.length}</td>
          <td className="pr-2">{o.apis.length}</td><td className="pr-2">{o.tests.length}</td><td className="pr-2">{o.uncertainties.length}</td>
          <td><Badge value={o.risk} /></td>
        </tr>
      ))}</tbody>
    </table>
  );
}

// --- approval and prediction vs reality ------------------------------------------------------------------

function ApprovalPanel({ projectId, report, option, onChanged, onError }) {
  const [plan, setPlan] = useState(null);
  const [execution, setExecution] = useState(null);
  const [reviewed, setReviewed] = useState(false);
  const [runTests, setRunTests] = useState(true);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!report.plan_id) { setPlan(null); setExecution(null); return; }
    try {
      const [p, e] = await Promise.all([listPlans(projectId), listExecutions(projectId)]);
      setPlan((p.plans || []).find((x) => x.id === report.plan_id) || null);
      setExecution((e.executions || []).find((x) => x.plan_id === report.plan_id) || null);
    } catch (err) { onError(err?.error || 'Could not load the plan.'); }
  }, [projectId, report.plan_id, onError]);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (!execution || !ACTIVE.has(execution.status)) return undefined;
    const t = setInterval(async () => { await refresh(); }, 3000);
    return () => clearInterval(t);
  }, [execution, refresh]);
  useEffect(() => { if (execution && !ACTIVE.has(execution.status)) onChanged(); }, [execution?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (fn) => { setBusy(true); try { await fn(); await refresh(); } catch (e) { onError(e?.error || 'Request failed.'); } finally { setBusy(false); } };
  const o = report.options[option];
  return (
    <Card title="Impact report → approval">
      <div className="space-y-2 text-xs text-text-secondary">
        {!plan && (
          <>
            <p>Turning the report into an Autopilot plan limits the change to the expected scope ({o.modify_scope.length} file(s){o.create_scope.length ? ' + new files in the listed folders' : ''}). Files outside it stop the run for your approval and are recorded as unexpected.</p>
            <Btn tone="primary" disabled={busy || !o.modify_scope.length && !o.create_scope.length}
                 onClick={() => act(async () => { await createPlanFromReport(projectId, report.id, option); onChanged(); })}>
              Create plan from "{o.label}"
            </Btn>
          </>
        )}
        {plan && (
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2"><span className="text-text-primary">Plan {plan.id}</span><Badge value={plan.status} />
              {execution && <><span>execution</span><Badge value={execution.status} /></>}</div>
            {['awaiting_approval', 'draft'].includes(plan.status) && (
              <div className="flex flex-wrap items-center gap-2">
                {plan.security_review_required && (
                  <label className="flex items-center gap-1.5 text-rose-200"><input type="checkbox" checked={reviewed} onChange={(e) => setReviewed(e.target.checked)} />
                    I reviewed the security impact of this authentication change</label>
                )}
                <Btn tone="good" disabled={busy || (plan.security_review_required && !reviewed)}
                     onClick={() => act(() => decidePlan(projectId, plan.id, 'approve', { security_reviewed: reviewed }))}><FaCheck className="h-2.5 w-2.5" /> Approve</Btn>
                <Btn tone="bad" disabled={busy} onClick={() => act(() => decidePlan(projectId, plan.id, 'reject'))}><FaTimes className="h-2.5 w-2.5" /> Reject</Btn>
              </div>
            )}
            {plan.status === 'approved' && (
              <div className="flex flex-wrap items-center gap-2">
                <label className="flex items-center gap-1.5"><input type="checkbox" checked={runTests} onChange={(e) => setRunTests(e.target.checked)} /> run tests (Docker sandbox)</label>
                <Btn tone="primary" disabled={busy} onClick={() => act(() => executePlan(projectId, plan.id, runTests))}><FaPlay className="h-2.5 w-2.5" /> Implement in an isolated copy</Btn>
              </div>
            )}
            {execution && <p className="text-[11px] text-text-muted">Stages, checks and the diff are in AIForge Autopilot → Execution. {execution.error}</p>}
          </div>
        )}
      </div>
    </Card>
  );
}

function OutcomePanel({ outcome, accuracy }) {
  if (!outcome) return null;
  const pct = (v) => (v == null ? 'n/a' : `${Math.round(v * 100)}%`);
  return (
    <Card title="Prediction versus reality" actions={<Badge value={outcome.execution_status} />}>
      <div className="space-y-3 text-xs text-text-secondary">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat name="Predicted files" value={outcome.predicted_files.length} />
          <Stat name="Actually modified" value={outcome.actual_files.length} />
          <Stat name="Precision" value={pct(outcome.precision)} />
          <Stat name="Recall" value={pct(outcome.recall)} />
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <Section title="Predicted">{outcome.predicted_files.length > 0 && <p className="font-mono">{outcome.predicted_files.join(', ')}</p>}</Section>
          <Section title="Actually modified">{outcome.actual_files.length > 0 && <p className="font-mono">{outcome.actual_files.join(', ')}</p>}</Section>
          <Section title="Unexpected modifications">{outcome.unexpected_files.length > 0 && <p className="font-mono text-amber-200">{outcome.unexpected_files.join(', ')}</p>}</Section>
          <Section title="Predicted but not changed">{outcome.predicted_not_changed.length > 0 && <p className="font-mono">{outcome.predicted_not_changed.join(', ')}</p>}</Section>
          <Section title="Validation failures">{outcome.validation_failures.length > 0 && <ul className="list-disc pl-4 text-rose-200">{outcome.validation_failures.map((f, i) => <li key={i}>{f}</li>)}</ul>}</Section>
          <Section title="Where the analysis was incomplete"><ul className="list-disc pl-4">{outcome.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul></Section>
        </div>
        {accuracy?.compared > 0 && (
          <p className="text-[11px] text-text-muted">Across {accuracy.compared} compared change(s) in this project: precision {pct(accuracy.mean_precision)}, recall {pct(accuracy.mean_recall)}. {accuracy.note}</p>
        )}
      </div>
    </Card>
  );
}

// --- page --------------------------------------------------------------------------------------------------

/**
 * AIForge Digital Twin: the project's dependency graph, read-only what-if simulations of a change,
 * approval through Autopilot, and what the change actually did compared with the prediction.
 * Everything shown comes from the backend; inferred relationships are marked as such.
 */
export default function DigitalTwinPage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [latest, setLatest] = useState(null);
  const [reports, setReports] = useState([]);
  const [reportId, setReportId] = useState('');
  const [report, setReport] = useState(null);
  const [option, setOption] = useState(0);
  const [outcome, setOutcome] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [targets, setTargets] = useState([]);
  const [version, setVersion] = useState(0);
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
      const [l, r] = await Promise.all([getLatestTwinAnalysis(projectId), listImpactReports(projectId)]);
      setLatest(l); setReports(r.reports || []);
    } catch (e) { setError(e?.error || 'Could not load the Digital Twin.'); }
  }, [projectId]);
  useEffect(() => { setLatest(null); setReports([]); setReportId(''); setReport(null); setTargets([]); setError(''); refresh(); }, [projectId, refresh]);
  useEffect(() => {
    if (!ACTIVE.has(latest?.analysis?.status) && !latest?.active_job) return undefined;
    const t = setInterval(async () => { await refresh(); setVersion((v) => v + 1); }, 2000);
    return () => clearInterval(t);
  }, [latest, refresh]);

  const loadReport = useCallback(async () => {
    if (!reportId) { setReport(null); setOutcome(null); return; }
    try {
      const r = (await getImpactReport(projectId, reportId)).report;
      setReport(r);
      if (r.plan_id) {
        setOutcome((await getReportOutcome(projectId, reportId)).outcome);
        setAccuracy(await getTwinAccuracy(projectId));
      } else { setOutcome(null); }
    } catch (e) { setError(e?.error || 'Could not load the report.'); }
  }, [projectId, reportId]);
  useEffect(() => { setOption(0); loadReport(); }, [loadReport]);
  useEffect(() => {
    if (!ACTIVE.has(report?.status)) return undefined;
    const t = setInterval(loadReport, 2000);
    return () => clearInterval(t);
  }, [report?.status, loadReport]);

  const analyze = async () => {
    setBusy(true); setError('');
    try { await startTwinAnalysis(projectId); await refresh(); } catch (e) { setError(e?.error || 'Could not start the analysis.'); } finally { setBusy(false); }
  };
  const simulate = async (body) => {
    setBusy(true); setError('');
    try {
      const r = (await simulateChange(projectId, body)).report;
      setReportId(r.id); setReport(r); refresh();
    } catch (e) { setError(e?.error || 'Could not start the simulation.'); } finally { setBusy(false); }
  };
  const hasGraph = latest?.graph_id;
  const opt = useMemo(() => report?.options?.[option], [report, option]);

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-text-primary">Digital Twin</h1>
          <p className="text-xs text-text-muted">Predict the impact of a change from the project's dependency graph before anything is modified.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)}
                className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {projectId && (
        <>
          <Overview latest={latest} onAnalyze={analyze} busy={busy} />
          {hasGraph && <Explorer projectId={projectId} version={version} onError={onError} onAddTarget={(p) => setTargets((t) => [...new Set([...t, p])])} />}
          {hasGraph && <SimulationForm targets={targets} setTargets={setTargets} onSubmit={simulate} busy={busy || !!latest?.active_job} />}
          {reports.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 text-xs text-text-secondary">
              <span className="text-[10px] uppercase tracking-wide text-text-muted">Reports</span>
              {reports.slice(0, 8).map((r) => (
                <button key={r.id} onClick={() => setReportId(r.id)}
                        className={`flex items-center gap-1.5 rounded-lg border px-2 py-1 ${r.id === reportId ? 'border-accent-blue bg-accent-blue/10' : 'border-border-dark hover:bg-surface-hover'}`}>
                  <span className="max-w-[14rem] truncate">{r.request}</span>{r.risk ? <Badge value={r.risk} /> : <Badge value={r.status} />}
                </button>
              ))}
            </div>
          )}
          {report && (
            <Card title="Impact report" actions={<Badge value={report.status} />}>
              {ACTIVE.has(report.status) && <p className="text-xs text-text-muted">Simulating… (rebuilding the graph first if the project changed)</p>}
              {report.error && <p className="text-xs text-rose-300">{report.error}</p>}
              {report.status === 'completed' && opt && (
                <div className="space-y-4">
                  <p className="text-sm text-text-primary">{report.request}</p>
                  <p className="text-[11px] text-text-muted">
                    Planner: {report.planner?.used ? `model (${report.planner.status})` : 'not used — targets from your selection and keyword matching'}
                    {report.planner?.notes ? ` · ${report.planner.notes}` : ''} · files written during the simulation: {report.files_written}
                  </p>
                  {report.options.length > 1 && <Comparison options={report.options} />}
                  {report.options.length > 1 && (
                    <div className="flex gap-1">{report.options.map((o, i) => (
                      <button key={o.label} onClick={() => setOption(i)} className={`rounded-md px-2 py-0.5 text-[11px] ${option === i ? 'bg-surface-hover text-text-primary' : 'text-text-muted hover:text-text-primary'}`}>{o.label}</button>
                    ))}</div>
                  )}
                  <OptionDetail o={opt} />
                  <div className="grid gap-3 text-[11px] text-text-muted md:grid-cols-2">
                    <Section title="Assumptions"><ul className="list-disc pl-4">{report.assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul></Section>
                    <Section title="Limitations of this analysis"><ul className="list-disc pl-4">{report.limitations.map((a, i) => <li key={i}>{a}</li>)}</ul></Section>
                  </div>
                </div>
              )}
            </Card>
          )}
          {report?.status === 'completed' && opt && (
            <ApprovalPanel projectId={projectId} report={report} option={option} onChanged={loadReport} onError={onError} />
          )}
          <OutcomePanel outcome={outcome} accuracy={accuracy} />
        </>
      )}
    </div>
  );
}
