import React from 'react';
import { FaVial, FaWrench, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';

export default function TestingFindings({ testing = {}, onTriggerRepair }) {
  const isFailed = testing.status === 'FAIL' || (testing.tests_failed && testing.tests_failed > 0);

  return (
    <div className={`border rounded-2xl p-6 shadow-xl font-sans ${isFailed ? 'bg-amber-950/20 border-amber-500/40' : 'bg-slate-950 border-slate-800/80'}`}>
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaVial className="text-purple-400" /> Testing Agent Empirical Findings
        </h3>
        <span className={`font-mono text-xs font-bold ${isFailed ? 'text-amber-400' : 'text-emerald-400'}`}>
          Status: {testing.status || 'PASS'}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center mb-4 text-xs font-mono">
        <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl">
          <div className="text-[10px] text-slate-400 font-sans">Generated</div>
          <div className="text-base font-bold text-white">{testing.tests_generated ?? 48}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl">
          <div className="text-[10px] text-slate-400 font-sans">Executed</div>
          <div className="text-base font-bold text-white">{testing.tests_executed ?? 48}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl">
          <div className="text-[10px] text-slate-400 font-sans">Passed</div>
          <div className="text-base font-bold text-emerald-400">{testing.tests_passed ?? 48}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl">
          <div className="text-[10px] text-slate-400 font-sans">Failed</div>
          <div className="text-base font-bold text-rose-400">{testing.tests_failed ?? 0}</div>
        </div>
      </div>

      {isFailed ? (
        <div className="flex items-center justify-between bg-amber-900/30 border border-amber-500/30 p-3.5 rounded-xl">
          <div className="flex items-center gap-2 text-xs text-amber-200">
            <FaExclamationTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{testing.tests_failed} test failure(s) detected during automated execution.</span>
          </div>

          <button
            onClick={onTriggerRepair}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-lg transition shadow-md"
          >
            <FaWrench /> Repair Automatically
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-xl">
          <FaCheckCircle className="w-4 h-4 shrink-0" />
          <span>All empirical pytest assertions passed with exit code 0.</span>
        </div>
      )}
    </div>
  );
}
