import React, { useCallback, useEffect, useState } from 'react';
import { FaDownload, FaFlask, FaGlobe, FaPlay, FaPlus, FaStop, FaTrash } from 'react-icons/fa';
import {
  cancelSimulation, getApplicationModel, getCalibration, getSimulation, getSimulationReport, listSimulations, startSimulation,
} from '../services/reality';
import { listAutopilotProjects } from '../services/evolutionAutopilot';

const GOOD = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
const BAD = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
const WARN = 'bg-amber-500/15 text-amber-300 border-amber-500/30';
const GREY = 'bg-slate-700/50 text-slate-300 border-slate-600';
const TONE = {
  completed: GOOD, measured: GOOD, 'measured bottleneck': BAD, failed: BAD, unavailable: WARN, cancelled: GREY,
  'model-predicted bottleneck': WARN, 'static-analysis suspicion': GREY, 'insufficient evidence': GREY, predicted: 'bg-violet-500/15 text-violet-300 border-violet-500/30',
  assumption: 'bg-sky-500/10 text-sky-200 border-sky-500/25', 'insufficient history': GREY, 'measured accuracy': GOOD,
};
const label = (s) => String(s ?? '').replace(/_/g, ' ');
const Badge = ({ value }) => (value == null ? null :
  <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${TONE[value] || (value === 'running' ? 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30' : 'border-slate-700 bg-slate-800 text-slate-400')}`}>{label(value)}</span>
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
const F = ({ name, children }) => <label className="flex flex-col gap-0.5 text-[10px] uppercase tracking-wide text-text-muted">{name}{children}</label>;
const fmt = (v, u = '') => (v == null ? '—' : `${v}${u}`);

// --- scenario builder ------------------------------------------------------------------------------------------

function Builder({ projectId, model, busy, act, onStarted }) {
  const endpoints = (model?.routes || []).filter((r) => r.measurable).map((r) => r.endpoint);
  const [name, setName] = useState('growth scenario');
  const [traffic, setTraffic] = useState({ pattern: 'constant', rps: 20, start_rps: 2, burst_seconds: 5, duration_seconds: 30 });
  const [mix, setMix] = useState({});
  const [alts, setAlts] = useState([{ id: 'current', title: 'current (1 worker, 1 CPU)', workers: 1, cpus: 1, memory_mb: 1024, dep: '' },
    { id: 'two_workers', title: '2 workers, 2 CPUs', workers: 2, cpus: 2, memory_mb: 1024, dep: '' }]);
  const [dependent, setDependent] = useState('');
  const [dependency, setDependency] = useState({ name: 'payments', env_var: 'PAYMENTS_URL', routes: '{"/charge": {"ok": true}}' });
  const [prices, setPrices] = useState({ vcpu_hour: '', gb_hour: '' });
  const [assumptions, setAssumptions] = useState('');
  const [consent, setConsent] = useState(false);
  useEffect(() => { setMix((cur) => (Object.keys(cur).length ? cur : Object.fromEntries(endpoints.slice(0, 3).map((e) => [e, 1])))); }, [model]); // eslint-disable-line react-hooks/exhaustive-deps
  const t = (k) => (e) => setTraffic({ ...traffic, [k]: e.target.value });
  const a = (i, k) => (e) => setAlts(alts.map((x, j) => (j === i ? { ...x, [k]: e.target.value } : x)));
  const scenario = () => {
    const hasDep = alts.some((x) => x.dep !== '');
    let routes = {};
    if (hasDep) { try { routes = JSON.parse(dependency.routes || '{}'); } catch { throw new Error('stub routes must be JSON'); } }
    return {
      name, assumptions: assumptions.split('\n').map((x) => x.trim()).filter(Boolean),
      traffic: { pattern: traffic.pattern, rps: Number(traffic.rps), start_rps: Number(traffic.start_rps), burst_seconds: Number(traffic.burst_seconds),
        duration_seconds: Number(traffic.duration_seconds), mix: Object.fromEntries(Object.entries(mix).filter(([, w]) => Number(w) > 0).map(([k, w]) => [k, Number(w)])) },
      alternatives: alts.map((x) => ({ id: x.id, title: x.title, resources: { workers: Number(x.workers), cpus: Number(x.cpus), memory_mb: Number(x.memory_mb) },
        dependency_latency_ms: x.dep === '' ? null : Number(x.dep) })),
      dependent_endpoints: hasDep ? dependent.split(',').map((x) => x.trim()).filter(Boolean) : [],
      dependency: hasDep ? { name: dependency.name, env_var: dependency.env_var, routes } : null,
      prices: prices.vcpu_hour !== '' ? { vcpu_hour: Number(prices.vcpu_hour), gb_hour: Number(prices.gb_hour || 0) } : null,
    };
  };
  const go = (runLoad) => act(async () => onStarted((await startSimulation(projectId, scenario(), runLoad)).simulation));
  return (
    <Card title="Scenario builder">
      <div className="space-y-2 text-xs text-text-secondary">
        <p className="text-[11px] text-text-muted"><Badge value="assumption" /> Everything entered here is your assumption about the future. The simulator measures a low-load baseline of your app, predicts with a documented queueing model, and — only if you approve — runs the workload against isolated copies.</p>
        <div className="flex flex-wrap items-end gap-2">
          <F name="Name"><input className={`${inputCls} w-44`} value={name} onChange={(e) => setName(e.target.value)} /></F>
          <F name="Pattern"><select className={inputCls} value={traffic.pattern} onChange={t('pattern')}><option>constant</option><option>ramp</option><option>burst</option></select></F>
          <F name={traffic.pattern === 'constant' ? 'Requests/s' : 'Peak requests/s'}><input type="number" className={`${inputCls} w-20`} value={traffic.rps} onChange={t('rps')} /></F>
          {traffic.pattern !== 'constant' && <F name="Start / base rps"><input type="number" className={`${inputCls} w-20`} value={traffic.start_rps} onChange={t('start_rps')} /></F>}
          {traffic.pattern === 'burst' && <F name="Burst seconds"><input type="number" className={`${inputCls} w-20`} value={traffic.burst_seconds} onChange={t('burst_seconds')} /></F>}
          <F name="Duration s (≤120)"><input type="number" className={`${inputCls} w-20`} value={traffic.duration_seconds} onChange={t('duration_seconds')} /></F>
        </div>
        <div><p className="text-[10px] uppercase text-text-muted">Endpoint mix (weights) — measurable GET routes from the Digital Twin</p>
          <div className="flex flex-wrap gap-2">{endpoints.map((e) => <label key={e} className="flex items-center gap-1 font-mono text-[11px]">{e}<input type="number" min="0" className={`${inputCls} w-14`} value={mix[e] ?? 0} onChange={(ev) => setMix({ ...mix, [e]: ev.target.value })} /></label>)}
            {!endpoints.length && <span className="text-amber-200">No measurable GET route was found in the project.</span>}</div></div>
        <div><p className="text-[10px] uppercase text-text-muted">Alternatives (configuration-level)</p>
          <table className="text-[11px]"><tbody>{alts.map((x, i) => (
            <tr key={i}><td className="pr-1"><input className={`${inputCls} w-24 font-mono`} value={x.id} onChange={a(i, 'id')} /></td>
              <td className="pr-1"><input className={`${inputCls} w-40`} value={x.title} onChange={a(i, 'title')} /></td>
              <td className="pr-1">workers <input type="number" min="1" max="4" className={`${inputCls} w-12`} value={x.workers} onChange={a(i, 'workers')} /></td>
              <td className="pr-1">CPUs <input type="number" step="0.25" min="0.25" max="2" className={`${inputCls} w-14`} value={x.cpus} onChange={a(i, 'cpus')} /></td>
              <td className="pr-1">MB <input type="number" className={`${inputCls} w-16`} value={x.memory_mb} onChange={a(i, 'memory_mb')} /></td>
              <td className="pr-1">dependency +ms <input type="number" className={`${inputCls} w-16`} placeholder="none" value={x.dep} onChange={a(i, 'dep')} /></td>
              <td><button onClick={() => setAlts(alts.filter((_, j) => j !== i))}><FaTrash className="h-2.5 w-2.5 text-text-muted" /></button></td></tr>))}</tbody></table>
          {alts.length < 4 && <Btn className="mt-1" onClick={() => setAlts([...alts, { id: `alt${alts.length + 1}`, title: 'alternative', workers: 1, cpus: 1, memory_mb: 1024, dep: '' }])}><FaPlus className="h-2.5 w-2.5" /> Alternative</Btn>}</div>
        {alts.some((x) => x.dep !== '') && <div className="flex flex-wrap items-end gap-2 rounded-lg border border-border-subtle p-2">
          <F name="Endpoints that call it"><input className={`${inputCls} w-56 font-mono`} placeholder="GET /api/checkout" value={dependent} onChange={(e) => setDependent(e.target.value)} /></F>
          <F name="Stub name"><input className={`${inputCls} w-28`} value={dependency.name} onChange={(e) => setDependency({ ...dependency, name: e.target.value })} /></F>
          <F name="App env var with its URL"><input className={`${inputCls} w-36 font-mono`} value={dependency.env_var} onChange={(e) => setDependency({ ...dependency, env_var: e.target.value })} /></F>
          <F name="Stub routes (JSON)"><input className={`${inputCls} w-56 font-mono`} value={dependency.routes} onChange={(e) => setDependency({ ...dependency, routes: e.target.value })} /></F>
        </div>}
        <div className="flex flex-wrap items-end gap-2">
          <F name="Price per vCPU-hour (optional)"><input type="number" className={`${inputCls} w-24`} value={prices.vcpu_hour} onChange={(e) => setPrices({ ...prices, vcpu_hour: e.target.value })} /></F>
          <F name="Price per GB-hour"><input type="number" className={`${inputCls} w-24`} value={prices.gb_hour} onChange={(e) => setPrices({ ...prices, gb_hour: e.target.value })} /></F>
          <F name="Your assumptions (one per line)"><textarea rows={1} className={`${inputCls} w-72`} value={assumptions} onChange={(e) => setAssumptions(e.target.value)} /></F>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Btn tone="primary" disabled={busy || !Object.values(mix).some((w) => Number(w) > 0)} onClick={() => go(false)}><FaFlask className="h-2.5 w-2.5" /> Predict (baseline measurement + model)</Btn>
          <label className="flex items-center gap-1.5 text-amber-100"><input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} /> I approve running this workload against isolated copies of the app (bounded: ≤200 rps, ≤120 s, ≤20,000 requests)</label>
          <Btn tone="good" disabled={busy || !consent || !Object.values(mix).some((w) => Number(w) > 0)} onClick={() => go(true)}><FaPlay className="h-2.5 w-2.5" /> Predict and run</Btn>
        </div>
      </div>
    </Card>
  );
}

// --- results ---------------------------------------------------------------------------------------------------

function Results({ s }) {
  const sc = s.scenario;
  return (
    <>
      <Card title="Simulation monitor" actions={<Badge value={s.status} />}>
        <ul className="space-y-0.5 text-[11px] text-text-secondary">{s.stages.map((x, i) => <li key={i}><span className="font-mono text-text-muted">{x.at.slice(11, 19)}</span> {x.stage} <Badge value={x.status} /> <span className="text-text-muted">{x.detail}</span></li>)}</ul>
        {s.error && <p className="mt-1 text-xs text-amber-200">{s.error}</p>}
        {s.baseline?.endpoints && <p className="mt-2 text-[11px]"><Badge value="measured" /> baseline (one request at a time): {Object.entries(s.baseline.endpoints).map(([k, v]) => `${k} ${v.median_ms} ms [${(v.rep_medians_ms || []).join(', ')}]`).join(' · ')}</p>}
      </Card>
      <Card title="Alternatives — predicted vs measured">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-[11px] text-text-secondary">
            <thead className="text-[10px] uppercase text-text-muted"><tr><th className="py-1 pr-2">Alternative</th><th className="pr-2">Utilisation</th><th className="pr-2">Throughput rps</th><th className="pr-2">Mean ms</th><th className="pr-2">p95 ms</th><th className="pr-2">Errors</th><th>Comparison</th></tr></thead>
            <tbody>{sc.alternatives.map((alt) => {
              const p = s.predictions[alt.id] || {}; const m = s.measurements[alt.id] || {}; const c = s.comparisons[alt.id] || {};
              const measured = m.status === 'measured' && m.mean_ms !== undefined;
              return (
                <React.Fragment key={alt.id}>
                  <tr className="border-t border-border-subtle align-top"><td className="py-1 pr-2 text-text-primary" rowSpan={2}>{alt.title}<div className="text-[10px] text-text-muted">{alt.resources.workers} worker(s), {alt.resources.cpus} CPU{alt.dependency_latency_ms != null ? `, dependency +${alt.dependency_latency_ms} ms` : ''}</div></td>
                    <td className="pr-2"><Badge value="predicted" /> {fmt(p.utilization)}</td><td className="pr-2">{fmt(p.throughput_rps)}</td><td className="pr-2">{fmt(p.mean_ms)}</td><td className="pr-2">{fmt(p.p95_ms)}</td><td className="pr-2">—</td>
                    <td rowSpan={2}>{c.rows ? c.rows.map((r) => <p key={r.metric}>{r.metric}: {r.predicted} → {r.observed} ({r.error_pct > 0 ? '+' : ''}{r.error_pct}%) {r.within_bounds ? '✓' : '✗'}</p>) : <span className="text-text-muted">{c.reason || 'not run'}</span>}
                      {c.onset && <p>saturation onset: predicted {fmt(c.onset.predicted_s, ' s')} / observed {fmt(c.onset.observed_s, ' s')}</p>}
                      {(c.explanation || []).map((x, i) => <p key={i} className="text-amber-200">{x}</p>)}</td></tr>
                  <tr className="align-top"><td className="pr-2">{measured ? <><Badge value="measured" /> CPU {fmt(m.resources?.cpu_avg_pct, '%')}</> : <Badge value={m.status || 'not run'} />}</td>
                    <td className="pr-2">{measured ? fmt(m.throughput_rps) : m.slowed ? '—' : ''}</td><td className="pr-2">{measured ? fmt(m.mean_ms) : m.slowed ? `${fmt(m.normal?.mean_ms)} → ${fmt(m.slowed?.mean_ms)}` : ''}</td>
                    <td className="pr-2">{measured ? fmt(m.p95_ms) : ''}</td><td className="pr-2">{measured ? `${m.error_rate_pct}%${m.dropped_by_generator ? `, ${m.dropped_by_generator} dropped by the generator` : ''}` : ''}</td></tr>
                  {p.note && <tr><td /><td colSpan={6} className="pb-1 text-[10px] text-amber-200">{p.note}</td></tr>}
                  {p.calibrated && <tr><td /><td colSpan={6} className="pb-1 text-[10px] text-text-muted">calibrated estimate: {Object.entries(p.calibrated).map(([k, v]) => `${k} ${v.value != null ? `${v.value} (×${v.factor}, ${v.records} runs)` : v.note}`).join(' · ')}</td></tr>}
                </React.Fragment>);
            })}</tbody>
          </table>
        </div>
        {Object.values(s.predictions)[0]?.formulas && <details className="mt-2"><summary className="cursor-pointer text-[11px] text-text-muted">Model formulas and assumptions</summary>
          <ul className="mt-1 list-disc pl-4 font-mono text-[10px] text-text-secondary">{Object.values(s.predictions)[0].formulas.map((f) => <li key={f}>{f}</li>)}</ul>
          <ul className="mt-1 list-disc pl-4 text-[11px] text-text-secondary">{Object.values(s.predictions)[0].assumptions.map((f) => <li key={f}>{f}</li>)}</ul></details>}
      </Card>
      <Card title="Capacity analysis and recommendation">
        <ul className="space-y-0.5 text-[11px] text-text-secondary">{s.bottlenecks.map((b, i) => <li key={i}><Badge value={b.label} /> {b.alternative || b.endpoint} — {b.detail}</li>)}{!s.bottlenecks.length && <li>No bottleneck found in the available evidence (this is not proof there is none).</li>}</ul>
        {s.recommendation?.reason && <p className="mt-2 text-xs"><span className="text-text-muted">Recommendation: </span><span className="text-text-primary">{s.recommendation.recommendation || 'none'}</span> <Badge value={s.recommendation.basis} /> — {s.recommendation.reason}</p>}
        {s.recommendation?.cost && <p className="text-[11px] text-text-secondary">Resources: {s.recommendation.cost.vcpus_needed} vCPU at {s.recommendation.cost.target_utilization} target utilisation{s.recommendation.cost.monthly_cost != null ? ` · ≈ ${s.recommendation.cost.monthly_cost} ${s.recommendation.cost.currency}/month (from your prices)` : ` · ${s.recommendation.cost.note}`}</p>}
        {(s.recommendation?.recommended_experiments || []).map((x) => <p key={x} className="text-[11px] text-text-muted">• {x}</p>)}
        {s.limitations.length > 0 && <ul className="mt-2 text-[11px] text-amber-200">{s.limitations.map((x) => <li key={x}>limitation: {x}</li>)}</ul>}
      </Card>
    </>
  );
}

/**
 * AIForge Reality Simulator: scenarios evaluated with an explicit queueing model built on measured service times,
 * and validated by bounded runs against isolated copies of the app. Predictions and measurements stay labelled.
 */
export default function RealitySimulatorPage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [model, setModel] = useState(null);
  const [sims, setSims] = useState([]);
  const [selected, setSelected] = useState('');
  const [sim, setSim] = useState(null);
  const [cal, setCal] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    listAutopilotProjects().then((r) => {
      setProjects(r.projects || []);
      const preferred = (r.projects || []).find((p) => p.project_id === activeProjectId);
      setProjectId((cur) => cur || preferred?.project_id || r.projects?.[0]?.project_id || '');
    }).catch((e) => setError(e?.error || 'Could not load projects.'));
    getCalibration().then(setCal).catch(() => {});
  }, [activeProjectId]);
  const refresh = useCallback(async () => {
    if (!projectId) return;
    try { const r = await listSimulations(projectId); setSims(r.simulations || []); setSelected((c) => c || r.simulations?.[0]?.id || ''); }
    catch (e) { setError(e?.error || 'Could not load simulations.'); }
  }, [projectId]);
  useEffect(() => {
    setModel(null); setSelected(''); setSim(null); refresh();
    if (projectId) getApplicationModel(projectId).then((r) => setModel(r.model)).catch((e) => setError(e?.error || 'Could not build the application model.'));
  }, [projectId, refresh]);
  const load = useCallback(async () => { if (selected) { try { setSim((await getSimulation(projectId, selected)).simulation); } catch { /* shown below */ } } }, [projectId, selected]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!sim || !['queued', 'running'].includes(sim.status)) return undefined;
    const t = setInterval(() => { load(); refresh(); getCalibration().then(setCal).catch(() => {}); }, 3000);
    return () => clearInterval(t);
  }, [sim, load, refresh]);
  const act = async (fn) => { setBusy(true); setError(''); try { await fn(); await refresh(); } catch (e) { setError(e?.error || e?.message || 'Request failed.'); } finally { setBusy(false); } };
  const download = (id, format) => act(async () => {
    const r = await getSimulationReport(projectId, id, format);
    const blob = new Blob([format === 'json' ? JSON.stringify(r, null, 2) : r], { type: format === 'json' ? 'application/json' : 'text/markdown' });
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `reality-${id}.${format === 'json' ? 'json' : 'md'}`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaGlobe className="h-4 w-4" /> Reality Simulator</h1>
          <p className="text-xs text-text-muted">Test the future before building it — predictions are labelled as predictions until a run measures them.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error} <button className="ml-2 underline" onClick={() => setError('')}>dismiss</button></p>}
      {projectId && (<>
        {model && <Card title="Application architecture (Digital Twin evidence)">
          <div className="grid gap-2 text-[11px] text-text-secondary md:grid-cols-3">
            <div><p className="text-text-muted">Routes ({model.routes.length})</p>{model.routes.slice(0, 12).map((r) => <p key={r.endpoint + r.evidence} className="font-mono">{r.endpoint} <span className="text-text-muted">{r.evidence}</span></p>)}</div>
            <div><p className="text-text-muted">External calls / data access</p>{[...model.external_dependencies, ...model.data_access].slice(0, 10).map((d) => <p key={d.evidence}>{d.kind}: <span className="font-mono">{d.evidence}</span></p>)}{!model.external_dependencies.length && !model.data_access.length && <p>none detected</p>}</div>
            <div><p className="text-text-muted">Not known</p>{model.unknown.map((x) => <p key={x}>• {x}</p>)}{model.static_suspicions.slice(0, 4).map((x) => <p key={x.evidence} className="text-amber-200">suspicion: {x.title}</p>)}</div>
          </div>
        </Card>}
        <Builder projectId={projectId} model={model} busy={busy} act={act} onStarted={(s) => setSelected(s.id)} />
        {sims.length > 0 && <Card title="Simulations">
          <ul className="space-y-1 text-[11px] text-text-secondary">{sims.map((x) => (
            <li key={x.id} className="flex flex-wrap items-center gap-2"><Badge value={x.status} /><span className="text-text-primary">{x.name}</span><span className="text-text-muted">{x.run_load ? 'predicted + measured' : 'predicted only'} · {new Date(x.created_at).toLocaleString()}</span>
              <Btn onClick={() => setSelected(x.id)}>Open</Btn>{['queued', 'running'].includes(x.status) && <Btn tone="bad" onClick={() => act(() => cancelSimulation(projectId, x.id))}><FaStop className="h-2.5 w-2.5" /> Cancel</Btn>}
              {x.status === 'completed' && <><Btn onClick={() => download(x.id, 'markdown')}><FaDownload className="h-2.5 w-2.5" /> .md</Btn><Btn onClick={() => download(x.id, 'json')}><FaDownload className="h-2.5 w-2.5" /> .json</Btn></>}</li>))}</ul>
        </Card>}
        {sim && <Results s={sim} />}
        <Card title="Prediction calibration (all projects)">
          {!cal?.groups?.length ? <p className="text-xs text-text-muted">No prediction has been compared with a measurement yet.</p> : (
            <table className="w-full text-left text-[11px] text-text-secondary"><thead className="text-[10px] uppercase text-text-muted"><tr><th className="py-1">Comparable group</th><th>Records</th><th>Mean |error|</th><th>Within bounds</th><th>Assessment</th></tr></thead>
              <tbody>{cal.groups.map((g) => <tr key={g.key} className="border-t border-border-subtle"><td className="py-1 font-mono">{g.key}</td><td>{g.records}</td><td>{g.mean_abs_error_pct}%</td><td>{g.within_bounds_pct}%</td><td><Badge value={g.assessment} /></td></tr>)}</tbody></table>)}
          {cal?.note && <p className="mt-1 text-[10px] text-text-muted">{cal.note}</p>}
        </Card>
      </>)}
    </div>
  );
}
