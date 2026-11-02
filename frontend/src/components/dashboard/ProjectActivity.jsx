import React from 'react';
import { FaHistory, FaCheckCircle } from 'react-icons/fa';

export default function ProjectActivity({ activity = [] }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-3 flex items-center gap-2">
        <FaHistory className="text-cyan-400" /> Project Activity Log
      </h3>

      <div className="space-y-2 font-mono text-xs">
        {activity.map((act, idx) => (
          <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800/80 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <FaCheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span className="text-slate-300 font-sans">{act.message}</span>
            </div>
            <span className="text-slate-500 text-[11px] shrink-0 ml-2">{act.timestamp}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
