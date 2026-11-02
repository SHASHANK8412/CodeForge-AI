import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaProjectDiagram, FaServer, FaDatabase, FaCube, FaArrowRight, FaFolderOpen } from 'react-icons/fa';
import { BACKEND_URL } from '../config/backend';

const TABS = [
  { id: 'routes', label: 'API routes', Icon: FaServer },
  { id: 'database', label: 'Database', Icon: FaDatabase },
  { id: 'components', label: 'Components', Icon: FaCube },
];

function Stat({ label, value, Icon }) {
  return (
    <div className="rounded-2xl border border-border-dark bg-surface-card p-4">
      <div className="flex items-center gap-2 text-xs text-text-secondary"><Icon size={11} /> {label}</div>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-text-primary">{value ?? '—'}</p>
    </div>
  );
}

function Empty({ children }) {
  return <p className="rounded-xl border border-dashed border-border-dark px-4 py-8 text-center text-sm text-text-secondary">{children}</p>;
}

/** Static analysis of the selected generated project: routes, tables and the component tree. */
export default function ProjectXRayPage({ projectId, setView }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('routes');

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    setData(null);
    setError(null);
    axios.get(`${BACKEND_URL}/api/projects/${encodeURIComponent(projectId)}/xray`, { timeout: 30000 })
      .then((res) => !cancelled && setData(res.data))
      .catch((err) => !cancelled && setError(err?.response?.status === 404
        ? `No generated project named "${projectId}" was found.`
        : (err?.message || 'Request failed')));
    return () => { cancelled = true; };
  }, [projectId]);

  if (!projectId) {
    return (
      <div className="mx-auto max-w-3xl p-8">
        <Empty>
          Select a project first.{' '}
          <button onClick={() => setView?.('projects')} className="font-medium text-violet-300 hover:underline cursor-pointer">Open projects</button>
        </Empty>
      </div>
    );
  }

  const components = Object.entries(data?.components || {});

  return (
    <div className="mx-auto min-h-full max-w-6xl space-y-6 p-4 font-sans text-text-primary sm:p-6 lg:p-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs text-text-muted"><FaProjectDiagram size={11} /> Project X-Ray</div>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{data?.project_name || projectId}</h1>
          <p className="mt-1 text-sm text-text-secondary">What the generated code actually contains, read from the files on disk.</p>
        </div>
        <button
          onClick={() => setView?.('code')}
          className="inline-flex items-center gap-2 rounded-lg border border-border-dark bg-surface-elevated px-3 py-1.5 text-xs font-medium transition hover:border-accent-violet/50 cursor-pointer"
        >
          <FaFolderOpen size={11} /> Open code
        </button>
      </header>

      {error && <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</p>}

      {!error && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat label="Files" value={data?.file_count} Icon={FaFolderOpen} />
            <Stat label="API routes" value={data?.routes?.length} Icon={FaServer} />
            <Stat label="Tables" value={data?.tables?.length} Icon={FaDatabase} />
            <Stat label="Components" value={data ? components.length : undefined} Icon={FaCube} />
          </div>

          <div role="tablist" className="flex w-fit gap-1 rounded-xl border border-border-dark bg-surface-card p-1">
            {TABS.map(({ id, label, Icon }) => (
              <button
                key={id}
                role="tab"
                aria-selected={tab === id}
                onClick={() => setTab(id)}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition cursor-pointer ${
                  tab === id ? 'bg-surface-hover text-text-primary' : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                <Icon size={10} /> {label}
              </button>
            ))}
          </div>

          {!data ? (
            <div className="space-y-2">{[0, 1, 2].map((i) => <div key={i} className="h-12 animate-pulse rounded-xl bg-surface-card" />)}</div>
          ) : tab === 'routes' ? (
            data.routes.length === 0 ? <Empty>No backend routes were found.</Empty> : (
              <ul className="divide-y divide-border-subtle overflow-hidden rounded-2xl border border-border-dark bg-surface-card">
                {data.routes.map((r) => (
                  <li key={`${r.file}${r.route}`} className="flex items-center justify-between gap-4 px-5 py-3">
                    <span className="truncate font-mono text-sm text-text-primary">{r.route}</span>
                    <span className="shrink-0 font-mono text-xs text-text-muted">{r.file}</span>
                  </li>
                ))}
              </ul>
            )
          ) : tab === 'database' ? (
            data.tables.length === 0 ? <Empty>No database tables were found.</Empty> : (
              <div className="grid gap-4 lg:grid-cols-2">
                <ul className="divide-y divide-border-subtle overflow-hidden rounded-2xl border border-border-dark bg-surface-card">
                  {data.tables.map((t) => (
                    <li key={t.table} className="flex items-center justify-between gap-4 px-5 py-3">
                      <span className="font-mono text-sm text-text-primary">{t.table}</span>
                      <span className="font-mono text-xs text-text-muted">{t.file}</span>
                    </li>
                  ))}
                </ul>
                <div className="rounded-2xl border border-border-dark bg-surface-card p-5">
                  <p className="text-xs uppercase tracking-wider text-text-muted">Relationships</p>
                  {data.relationships.length === 0 ? <p className="mt-3 text-sm text-text-secondary">None detected.</p> : (
                    <ul className="mt-3 space-y-2">
                      {data.relationships.map((r) => (
                        <li key={`${r.source_table}-${r.target_table}`} className="flex items-center gap-2 font-mono text-xs text-text-secondary">
                          <span className="text-text-primary">{r.source_table}</span>
                          <FaArrowRight size={9} className="text-text-muted" />
                          <span className="text-text-primary">{r.target_table}</span>
                          <span className="text-text-muted">({r.relation})</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )
          ) : (
            components.length === 0 ? <Empty>No React components were found.</Empty> : (
              <ul className="space-y-3">
                {components.map(([parent, children]) => (
                  <li key={parent} className="rounded-2xl border border-border-dark bg-surface-card px-5 py-4">
                    <p className="font-mono text-sm text-text-primary">
                      {parent}
                      {data.root_components.includes(parent) && <span className="ml-2 rounded bg-accent-violet/15 px-1.5 py-0.5 text-[10px] text-violet-300">root</span>}
                    </p>
                    {children.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {children.map((c) => (
                          <span key={c} className="rounded-md border border-border-dark bg-bg-base px-2 py-0.5 font-mono text-[11px] text-text-secondary">{c}</span>
                        ))}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )
          )}
        </>
      )}
    </div>
  );
}
