import React, { useState } from 'react';
import { FaCheckCircle, FaExclamationTriangle, FaTimesCircle, FaMinusCircle, FaChevronDown, FaChevronUp, FaShieldAlt } from 'react-icons/fa';

const LOOK = {
  PASSED: { icon: FaCheckCircle, color: 'text-emerald-400' },
  WARNING: { icon: FaExclamationTriangle, color: 'text-amber-400' },
  FAILED: { icon: FaTimesCircle, color: 'text-rose-400' },
  BLOCKED: { icon: FaExclamationTriangle, color: 'text-orange-400' },
  SKIPPED: { icon: FaMinusCircle, color: 'text-slate-400' },
  NOT_EVALUATED: { icon: FaMinusCircle, color: 'text-slate-500' },
};

function QualityGateItem({ gate }) {
  const [isOpen, setIsOpen] = useState(false);
  const look = LOOK[gate.status] || LOOK.NOT_EVALUATED;
  const Icon = look.icon;
  const evaluated = !['NOT_EVALUATED', 'SKIPPED'].includes(gate.status);

  return (
    <div className="border border-slate-800/80 rounded-xl bg-slate-950 overflow-hidden transition">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-900/60 font-sans select-none"
      >
        <div className="flex items-center gap-3">
          <Icon className={`w-4 h-4 shrink-0 ${look.color}`} />
          <span className="text-xs font-bold text-slate-200">{gate.name}</span>
        </div>

        <div className="flex items-center gap-3">
          <span className={`font-mono text-[10px] font-bold px-2.5 py-0.5 rounded border border-slate-800 bg-slate-900 ${look.color}`}>
            {String(gate.status).replace(/_/g, ' ')}
          </span>
          {isOpen ? <FaChevronUp className="w-3 h-3 text-slate-500" /> : <FaChevronDown className="w-3 h-3 text-slate-500" />}
        </div>
      </div>

      {isOpen && (
        <div className="p-4 bg-[#070b13] border-t border-slate-800/80 text-xs font-sans space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-2">
            <span className="text-[11px] font-mono text-slate-400">Source: <strong className="text-slate-200">{gate.source || 'unknown'}</strong></span>
            {evaluated && (
              <div className="flex gap-2 font-mono text-[10px]">
                <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">Critical: {gate.critical ?? 0}</span>
                <span className="px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20">High: {gate.high ?? 0}</span>
                <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">Medium: {gate.medium ?? 0}</span>
                <span className="px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">Low: {gate.low ?? 0}</span>
              </div>
            )}
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-1.5">{evaluated ? 'Result' : 'Why it was not evaluated'}</div>
            {gate.findings && gate.findings.length > 0 ? (
              <ul className="space-y-1 list-disc list-inside text-slate-300">
                {gate.findings.map((f, idx) => (
                  <li key={idx}>{f}</li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-500 italic">No details were recorded.</p>
            )}
          </div>

          {gate.recommendation && gate.recommendation !== 'None' && (
            <div className="p-2.5 bg-indigo-950/40 border border-indigo-500/20 rounded-lg text-indigo-200">
              <strong className="font-bold text-cyan-400">Next step:</strong> {gate.recommendation}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** Gates computed from recorded checks. "Passed" counts only gates that were evaluated and passed. */
export default function QualityGates({ gates = [], passedCount = 0, evaluatedCount = 0, totalCount = 0 }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaShieldAlt className="text-cyan-400" /> Quality Gates (from recorded checks)
        </h3>
        <span className="font-mono text-xs font-bold text-slate-200 bg-slate-900 px-3 py-1 rounded-full border border-slate-800">
          {passedCount} passed · {evaluatedCount} evaluated · {totalCount} total
        </span>
      </div>

      {gates.length ? (
        <div className="space-y-2">
          {gates.map((gate) => (
            <QualityGateItem key={gate.id || gate.name} gate={gate} />
          ))}
        </div>
      ) : <p className="text-xs text-slate-500">No gates were reported.</p>}
    </div>
  );
}
