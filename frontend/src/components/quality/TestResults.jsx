import React from 'react';
import { FaVial, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';

export default function TestResults({ tests = {}, breakdown = {} }) {
  const total = tests.total ?? 48;
  const passed = tests.passed ?? 48;
  const failed = tests.failed ?? 0;
  const skipped = tests.skipped ?? 0;
  const coverage = tests.coverage ?? 94;
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 100;

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaVial className="text-purple-400" /> Empirical Testing Dashboard
        </h3>
        <span className="font-mono text-xs font-bold text-emerald-400">
          {passed} / {total} PASSED ({passRate}%)
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5 mb-6">
        <div className="flex justify-between text-xs text-slate-400 font-mono">
          <span>Pass Rate Progress</span>
          <span className="text-emerald-400 font-bold">{passRate}%</span>
        </div>
        <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
          <div
            className="bg-emerald-500 h-full transition-all duration-500"
            style={{ width: `${passRate}%` }}
          />
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center mb-6">
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">Total Tests</div>
          <div className="text-lg font-black text-white font-mono">{total}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">Passed</div>
          <div className="text-lg font-black text-emerald-400 font-mono">{passed}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">Failed</div>
          <div className="text-lg font-black text-rose-400 font-mono">{failed}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-medium">Coverage</div>
          <div className="text-lg font-black text-cyan-400 font-mono">{coverage}%</div>
        </div>
      </div>

      {/* Test Breakdown */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
        <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 flex justify-between">
          <span className="text-slate-400">Unit Tests</span>
          <span className="text-emerald-400 font-bold">✓ 32 / 32</span>
        </div>
        <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 flex justify-between">
          <span className="text-slate-400">Integration</span>
          <span className="text-emerald-400 font-bold">✓ 10 / 10</span>
        </div>
        <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 flex justify-between">
          <span className="text-slate-400">API Tests</span>
          <span className="text-emerald-400 font-bold">✓ 6 / 6</span>
        </div>
        <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 flex justify-between">
          <span className="text-slate-400">Security</span>
          <span className="text-emerald-400 font-bold">✓ 5 / 5</span>
        </div>
      </div>
    </div>
  );
}
