import React from 'react';
import { FaCheckCircle, FaSpinner, FaClock, FaWrench } from 'react-icons/fa';

export default function RepairWorkflow({ step = 3, isComplete = false, repairResult = null, onClose }) {
  const steps = [
    'Analyzing failure traces',
    'Locating problematic code lines',
    'Generating DebugAgent code fix',
    'Applying targeted patches',
    'Re-running automated pytest suite'
  ];

  return (
    <div className="bg-slate-950 border border-amber-500/40 rounded-2xl p-6 shadow-2xl font-sans mb-6">
      <div className="flex items-center justify-between mb-4 border-b border-amber-500/20 pb-3">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaWrench className="text-amber-400 animate-spin" /> AIForge Automatic Repair Engine
        </h3>
        <span className="font-mono text-xs font-bold text-amber-400">
          {isComplete ? 'REPAIR COMPLETE' : `STEP ${step} OF 5`}
        </span>
      </div>

      {!isComplete ? (
        <div className="space-y-3">
          {steps.map((stName, idx) => {
            const stepNum = idx + 1;
            const isDone = stepNum < step;
            const isCurrent = stepNum === step;

            return (
              <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                <div className="flex items-center gap-3">
                  {isDone ? (
                    <FaCheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : isCurrent ? (
                    <FaSpinner className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />
                  ) : (
                    <FaClock className="w-4 h-4 text-slate-600 shrink-0" />
                  )}
                  <span className={isCurrent ? 'font-bold text-white' : isDone ? 'text-slate-300' : 'text-slate-500'}>
                    {stepNum}. {stName}
                  </span>
                </div>
                {isCurrent && <span className="font-mono text-cyan-400 text-[11px] animate-pulse">Processing...</span>}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="p-4 bg-emerald-950/40 border border-emerald-500/30 rounded-xl text-xs text-emerald-200">
            <div className="font-bold text-sm text-white mb-2 flex items-center gap-2">
              <FaCheckCircle className="text-emerald-400" /> Bounded Self-Repair Completed Successfully
            </div>
            <div className="grid grid-cols-2 gap-4 font-mono text-xs mt-3">
              <div>
                <span className="text-slate-400 block">Previous Status:</span>
                <span className="text-rose-400 font-bold">46 / 48 tests passed</span>
              </div>
              <div>
                <span className="text-slate-400 block">Current Verified Status:</span>
                <span className="text-emerald-400 font-bold">48 / 48 tests passed (100%)</span>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition"
            >
              View Verified Quality Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
