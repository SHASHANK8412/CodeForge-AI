import React, { useState } from 'react';
import { FaCheckCircle, FaExclamationTriangle, FaChevronDown, FaChevronUp, FaShieldAlt } from 'react-icons/fa';

function QualityGateItem({ gate }) {
  const [isOpen, setIsOpen] = useState(false);

  const isPassed = gate.status === 'PASSED' || gate.status === 'PASS';

  return (
    <div className="border border-slate-800/80 rounded-xl bg-slate-950 overflow-hidden transition">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-900/60 font-sans select-none"
      >
        <div className="flex items-center gap-3">
          {isPassed ? (
            <FaCheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <FaExclamationTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          )}
          <span className="text-xs font-bold text-slate-200">{gate.name}</span>
        </div>

        <div className="flex items-center gap-3">
          <span className="font-mono text-xs font-bold text-cyan-400 bg-slate-900 px-2.5 py-0.5 rounded border border-slate-800">
            {gate.score} / 100
          </span>
          {isOpen ? <FaChevronUp className="w-3 h-3 text-slate-500" /> : <FaChevronDown className="w-3 h-3 text-slate-500" />}
        </div>
      </div>

      {isOpen && (
        <div className="p-4 bg-[#070b13] border-t border-slate-800/80 text-xs font-sans space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
            <span className="text-[11px] font-mono text-slate-400">Status: <strong className="text-emerald-400">{gate.status}</strong></span>
            <div className="flex gap-2 font-mono text-[10px]">
              <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">Critical: {gate.critical || 0}</span>
              <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Medium: {gate.medium || 0}</span>
              <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">Low: {gate.low || 0}</span>
            </div>
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-1.5">Findings</div>
            {gate.findings && gate.findings.length > 0 ? (
              <ul className="space-y-1 list-disc list-inside text-slate-300">
                {gate.findings.map((f, idx) => (
                  <li key={idx}>{f}</li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-500 italic">No issues detected for this quality gate.</p>
            )}
          </div>

          {gate.recommendation && (
            <div className="p-2.5 bg-indigo-950/40 border border-indigo-500/20 rounded-lg text-indigo-200">
              <strong className="font-bold text-cyan-400">Recommendation:</strong> {gate.recommendation}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function QualityGates({ gates = [], passedCount = 15, totalCount = 15 }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaShieldAlt className="text-cyan-400" /> Automated Quality Gates Breakdown
        </h3>
        <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
          {passedCount} / {totalCount} PASSED
        </span>
      </div>

      <div className="space-y-2">
        {gates.map((gate) => (
          <QualityGateItem key={gate.id || gate.name} gate={gate} />
        ))}
      </div>
    </div>
  );
}
