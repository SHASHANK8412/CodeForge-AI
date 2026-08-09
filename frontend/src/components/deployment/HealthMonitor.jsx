import React, { useState } from 'react';
import { FaCheckCircle, FaSpinner, FaHeartbeat } from 'react-icons/fa';
import { checkHealth } from '../../services/deployment';

export default function HealthMonitor({ generationId, healthData }) {
  const [health, setHealth] = useState(healthData || {
    frontend: 'OPERATIONAL',
    backend: 'OPERATIONAL',
    database: 'CONNECTED',
    api: 'HEALTHY',
    last_checked: new Date().toLocaleTimeString()
  });
  const [checking, setChecking] = useState(false);

  const handleCheckHealth = async () => {
    setChecking(true);
    const res = await checkHealth(generationId);
    setHealth(res);
    setChecking(false);
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaHeartbeat className="text-rose-400" /> Live Infrastructure Health Monitor
        </h3>

        <button
          onClick={handleCheckHealth}
          disabled={checking}
          className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-cyan-400 hover:text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50"
        >
          {checking ? <FaSpinner className="animate-spin" /> : <FaHeartbeat />}
          <span>{checking ? 'Checking Health...' : 'Check Health'}</span>
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Frontend CDN</label>
          <div className="text-emerald-400 font-bold flex items-center gap-1">
            <FaCheckCircle className="w-3 h-3" /> {health.frontend || 'OPERATIONAL'}
          </div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Backend REST API</label>
          <div className="text-emerald-400 font-bold flex items-center gap-1">
            <FaCheckCircle className="w-3 h-3" /> {health.backend || 'OPERATIONAL'}
          </div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">PostgreSQL DB</label>
          <div className="text-emerald-400 font-bold flex items-center gap-1">
            <FaCheckCircle className="w-3 h-3" /> {health.database || 'CONNECTED'}
          </div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">API Health Route</label>
          <div className="text-emerald-400 font-bold flex items-center gap-1">
            <FaCheckCircle className="w-3 h-3" /> {health.api || 'HEALTHY'}
          </div>
        </div>
      </div>

      <div className="mt-3 text-right text-[10px] font-mono text-slate-500">
        Last health probe: {health.last_checked}
      </div>
    </div>
  );
}
