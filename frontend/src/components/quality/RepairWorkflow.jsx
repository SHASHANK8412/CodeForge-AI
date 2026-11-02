import React, { useEffect, useState } from 'react';
import { FaCheckCircle, FaSpinner, FaWrench, FaExclamationTriangle } from 'react-icons/fa';
import { getVerification } from '../../services/executionGuardian';

const DONE = ['VERIFIED', 'VERIFIED_WITH_WARNINGS', 'FAILED', 'BLOCKED', 'CANCELLED'];

/**
 * A real Execution Guardian verification of the project (checks run on an isolated copy, failures repaired within
 * limits). Everything shown is the verification's own state, polled from the API - no simulated progress.
 */
export default function RepairWorkflow({ projectId, verificationId, error, onClose, onFinished }) {
  const [v, setV] = useState(null);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    if (!verificationId) return undefined;
    let alive = true;
    const load = async () => {
      try {
        const r = await getVerification(projectId, verificationId);
        if (!alive) return;
        setV(r.verification);
        if (DONE.includes(r.verification.status)) {
          clearInterval(timer);
          onFinished?.(r.verification);
        }
      } catch (e) { if (alive) setLoadError(e?.error || 'Could not load the verification.'); }
    };
    const timer = setInterval(load, 2500);
    load();
    return () => { alive = false; clearInterval(timer); };
  }, [projectId, verificationId]); // eslint-disable-line react-hooks/exhaustive-deps

  const finished = v && DONE.includes(v.status);
  const ok = v && v.status.startsWith('VERIFIED');
  return (
    <div className="bg-slate-950 border border-amber-500/40 rounded-2xl p-6 shadow-2xl font-sans mb-6">
      <div className="flex items-center justify-between mb-4 border-b border-amber-500/20 pb-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaWrench className={`text-amber-400 ${finished ? '' : 'animate-spin'}`} /> Execution Guardian verification
        </h3>
        <span className="font-mono text-xs font-bold text-amber-400">{v ? v.status.replace(/_/g, ' ') : error ? 'NOT STARTED' : 'STARTING'}</span>
      </div>

      {(error || loadError) && <p className="mb-3 text-xs text-rose-300">{error || loadError}</p>}
      {v && (
        <div className="space-y-2 text-xs text-slate-300">
          <p className="flex items-center gap-2">
            {finished ? (ok ? <FaCheckCircle className="text-emerald-400" /> : <FaExclamationTriangle className="text-amber-400" />)
              : <FaSpinner className="animate-spin text-cyan-400" />}
            {finished ? (v.report?.statement || v.status) : v.current_operation}
          </p>
          <ul className="space-y-1 font-mono text-[11px]">
            {(v.checks || []).map((c) => <li key={c.name}>{c.label}: {c.status}{c.error_summary ? ` — ${c.error_summary}` : ''}</li>)}
          </ul>
          <p>Repair attempts: {(v.repairs || []).length} of {v.settings?.max_repair_attempts ?? '—'}</p>
          {v.delivery?.autopilot_plan_id && (
            <p className="text-emerald-200">Repaired files are Autopilot plan {v.delivery.autopilot_plan_id}, awaiting your approval. The project has not been changed.</p>
          )}
        </div>
      )}
      <div className="mt-4 flex justify-end">
        <button onClick={onClose} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition">
          {finished ? 'Close' : 'Hide (keeps running)'}
        </button>
      </div>
    </div>
  );
}
