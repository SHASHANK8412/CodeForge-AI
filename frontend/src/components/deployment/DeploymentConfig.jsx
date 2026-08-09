import React from 'react';
import { FaCogs, FaCheckCircle } from 'react-icons/fa';

export default function DeploymentConfig({ config = {} }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-3 flex items-center gap-2">
        <FaCogs className="text-cyan-400" /> Production Build & Server Settings
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Environment Target</label>
          <div className="text-white font-bold">{config.environment || 'Production'}</div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Deployment Region</label>
          <div className="text-white font-bold">{config.region || 'Auto (US-East)'}</div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Build Command</label>
          <div className="text-cyan-400 font-bold">{config.build_command || 'npm run build'}</div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Start Command</label>
          <div className="text-cyan-400 font-bold">{config.start_command || 'uvicorn main:app --host 0.0.0.0 --port $PORT'}</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mt-4 text-xs">
        <div className="p-2.5 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
          <span className="text-slate-300 font-medium">Docker</span>
          <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1"><FaCheckCircle /> Enabled</span>
        </div>
        <div className="p-2.5 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
          <span className="text-slate-300 font-medium">HTTPS</span>
          <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1"><FaCheckCircle /> Enabled</span>
        </div>
        <div className="p-2.5 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between">
          <span className="text-slate-300 font-medium">Health Check</span>
          <span className="text-cyan-400 font-mono text-[11px]">{config.health_check_path || '/health'}</span>
        </div>
      </div>
    </div>
  );
}
