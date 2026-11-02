import React from 'react';
import { FaVial, FaWrench, FaCheckCircle, FaExclamationTriangle, FaMinusCircle } from 'react-icons/fa';

/** The project's own tests as the Execution Guardian ran them. Tests that never ran are never shown as passing. */
export default function TestingFindings({ testing = {}, onTriggerRepair }) {
  const status = testing.status || 'NOT_RUN';
  const isFailed = status === 'FAIL' || (testing.tests_failed && testing.tests_failed > 0);
  const notRun = status === 'NOT_RUN';
  const cell = (v) => (v == null ? '—' : v);

  return (
    <div className={`border rounded-2xl p-6 shadow-xl font-sans ${isFailed ? 'bg-amber-950/20 border-amber-500/40' : 'bg-slate-950 border-slate-800/80'}`}>
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaVial className="text-purple-400" /> Project Tests
        </h3>
        <span className={`font-mono text-xs font-bold ${isFailed ? 'text-amber-400' : notRun ? 'text-slate-400' : 'text-emerald-400'}`}>
          Status: {status.replace(/_/g, ' ')}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center mb-4 text-xs font-mono">
        <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl">
          <div className="text-[10px] text-slate-400 font-sans">Executed</div>
          <div className="text-base font-bold text-white">{cell(testing.tests_executed)}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl">
          <div className="text-[10px] text-slate-400 font-sans">Passed</div>
          <div className="text-base font-bold text-emerald-400">{cell(testing.tests_passed)}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl">
          <div className="text-[10px] text-slate-400 font-sans">Failed</div>
          <div className="text-base font-bold text-rose-400">{cell(testing.tests_failed)}</div>
        </div>
      </div>

      {isFailed ? (
        <div className="flex items-center justify-between gap-3 bg-amber-900/30 border border-amber-500/30 p-3.5 rounded-xl">
          <div className="text-xs text-amber-200">
            <div className="flex items-center gap-2">
              <FaExclamationTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>{testing.tests_failed} test(s) failed.</span>
            </div>
            {testing.failed_tests?.length > 0 && (
              <ul className="mt-1 list-disc pl-6 font-mono text-[10px]">{testing.failed_tests.slice(0, 8).map((t) => <li key={t}>{t}</li>)}</ul>
            )}
          </div>
          {onTriggerRepair && (
            <button
              onClick={onTriggerRepair}
              className="flex shrink-0 items-center gap-1.5 px-3.5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-lg transition shadow-md"
            >
              <FaWrench /> Verify & repair
            </button>
          )}
        </div>
      ) : notRun ? (
        <div className="flex items-center justify-between gap-3 text-xs text-slate-300 bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <span className="flex items-center gap-2"><FaMinusCircle className="w-4 h-4 shrink-0 text-slate-500" />No test run is recorded for this project.</span>
          {onTriggerRepair && (
            <button onClick={onTriggerRepair} className="shrink-0 rounded-lg border border-slate-700 px-3 py-1.5 font-bold text-slate-200">
              Run verification
            </button>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-xl">
          <FaCheckCircle className="w-4 h-4 shrink-0" />
          <span>All {testing.tests_executed} executed test(s) passed.</span>
        </div>
      )}
    </div>
  );
}
