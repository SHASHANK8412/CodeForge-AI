import React, { useEffect, useState } from 'react';
import { FaProjectDiagram } from 'react-icons/fa';
import IntegrationDashboard from '../components/integration/IntegrationDashboard';
import { listAutopilotProjects } from '../services/evolutionAutopilot';

/**
 * AIForge Integration & Compatibility Engine: independently generated frontend, backend and database components are
 * checked against one shared contract - statically, then by contract tests run in isolation - mismatches are routed
 * to the responsible agent and repaired within limits, and the result is reported as it is (compiling is not
 * compatibility).
 */
export default function IntegrationEnginePage({ activeProjectId }) {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    listAutopilotProjects().then((r) => {
      setProjects(r.projects || []);
      const preferred = (r.projects || []).find((p) => p.project_id === activeProjectId);
      setProjectId((cur) => cur || preferred?.project_id || r.projects?.[0]?.project_id || '');
    }).catch((e) => setError(e?.error || 'Could not load projects.'));
  }, [activeProjectId]);
  const name = projects.find((p) => p.project_id === projectId)?.name;
  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaProjectDiagram className="h-4 w-4" /> Integration Engine</h1>
          <p className="text-xs text-text-muted">One shared contract for the frontend, backend and database — mismatches found, routed to the responsible agent, and verified by tests that ran.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error}</p>}
      <IntegrationDashboard projectId={projectId} projectName={name} />
    </div>
  );
}
