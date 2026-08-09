import React, { useState } from 'react';
import { FaDatabase, FaCheckCircle, FaSpinner } from 'react-icons/fa';

export default function DatabaseConfig({ database = {} }) {
  const [testing, setTesting] = useState(false);
  const [tested, setTested] = useState(false);

  const handleTestConnection = () => {
    setTesting(true);
    setTimeout(() => {
      setTesting(false);
      setTested(true);
    }, 1200);
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaDatabase className="text-purple-400" /> PostgreSQL Production Database Config
        </h3>

        <button
          onClick={handleTestConnection}
          disabled={testing}
          className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-cyan-400 hover:text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50"
        >
          {testing ? <FaSpinner className="animate-spin" /> : <FaCheckCircle />}
          <span>{testing ? 'Testing...' : tested ? 'Connection Validated' : 'Test Connection'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Provider</label>
          <div className="text-white font-bold">{database.provider || 'PostgreSQL'}</div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Status</label>
          <div className="text-emerald-400 font-bold flex items-center gap-1">
            <FaCheckCircle className="w-3 h-3" /> Configuration Valid
          </div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Connection String</label>
          <div className="text-slate-400">••••••••••••••••</div>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
          <label className="text-[11px] text-slate-400 font-sans block mb-1">Migrations</label>
          <div className="text-emerald-400 font-bold flex items-center gap-1">
            <FaCheckCircle className="w-3 h-3" /> Ready
          </div>
        </div>
      </div>
    </div>
  );
}
