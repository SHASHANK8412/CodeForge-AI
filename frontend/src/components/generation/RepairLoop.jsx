import React from 'react';
import { FaWrench, FaExclamationTriangle, FaCheckCircle, FaRedo } from 'react-icons/fa';

export default function RepairLoop({ active = false, attempt = 1, maxAttempts = 3 }) {
  if (!active) return null;

  return (
    <div className="bg-amber-950/40 border border-amber-500/40 rounded-2xl p-5 mb-6 text-amber-200 font-sans shadow-xl">
      <div className="flex items-center justify-between mb-3 border-b border-amber-500/20 pb-2">
        <div className="flex items-center gap-2 font-bold text-white text-xs uppercase tracking-wider">
          <FaWrench className="text-amber-400 animate-bounce w-4 h-4" /> Bounded Self-Repair Loop Active
        </div>
        <span className="font-mono text-xs font-bold text-amber-400">
          Attempt {attempt} / {maxAttempts}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-center font-mono">
        <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
          <div className="text-rose-400 flex items-center justify-center gap-1 mb-1 font-bold">
            <FaExclamationTriangle className="w-3 h-3" /> Test Failures
          </div>
          <p className="text-[11px] text-slate-400">Empirical failure detected</p>
        </div>

        <div className="bg-slate-950 p-2.5 rounded-xl border border-amber-500/30">
          <div className="text-amber-400 flex items-center justify-center gap-1 mb-1 font-bold">
            <FaWrench className="w-3 h-3 animate-spin" /> DebugAgent
          </div>
          <p className="text-[11px] text-slate-400">Applying targeted patches</p>
        </div>

        <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
          <div className="text-cyan-400 flex items-center justify-center gap-1 mb-1 font-bold">
            <FaRedo className="w-3 h-3 animate-spin" /> Retesting
          </div>
          <p className="text-[11px] text-slate-400">Re-running pytest suite</p>
        </div>
      </div>
    </div>
  );
}
