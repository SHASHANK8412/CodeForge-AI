import React, { useEffect, useState } from 'react';
import { FaShieldAlt } from 'react-icons/fa';
import VerificationDashboard from '../components/verification/VerificationDashboard';
import { listAutopilotProjects } from '../services/evolutionAutopilot';

/**
 * AIForge Execution Guardian: a generated project is verified by running it - checks chosen from its stack, run in
 * isolation, failures classified and routed to the responsible agent, repaired within bounds, and reported
 * honestly (VERIFIED only when every required check actually passed).
 */
export default function ExecutionGuardianPage({ activeProjectId }) {
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
          <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary"><FaShieldAlt className="h-4 w-4" /> Execution Guardian</h1>
          <p className="text-xs text-text-muted">Generated code is not working code until it runs: verified by execution, repaired within limits, reported as it is.</p>
        </div>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className="min-w-[16rem] rounded-lg border border-border-dark bg-surface-card px-3 py-2 text-xs text-text-primary">
          {projects.length === 0 && <option value="">No generated projects</option>}
          {projects.map((p) => <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>)}
        </select>
      </header>
      {error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">{error}</p>}
      <VerificationDashboard projectId={projectId} projectName={name} />
    </div>
  );
}
