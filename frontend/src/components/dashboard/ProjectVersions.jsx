import React from 'react';
import { FaCodeBranch, FaCheckCircle } from 'react-icons/fa';

export default function ProjectVersions({ versions = [], onViewVersion }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-3 flex items-center gap-2">
        <FaCodeBranch className="text-purple-400" /> Project Versions
      </h3>

      <div className="space-y-2">
        {versions.map((ver, idx) => (
          <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-3">
              <span className="font-bold text-cyan-400 text-sm">{ver.version}</span>
              <span className="text-emerald-400 text-[10px] font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
                <FaCheckCircle className="w-2.5 h-2.5" /> {ver.status}
              </span>
            </div>

            <div className="flex items-center gap-4 text-slate-400 text-[11px]">
              <span>Score: <strong className="text-white">{ver.quality_score}</strong></span>
              <span>Tests: <strong className="text-white">{ver.tests}</strong></span>
              <button
                onClick={() => onViewVersion && onViewVersion(ver)}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded font-sans text-[11px] font-semibold transition"
              >
                View Version
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
