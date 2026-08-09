import React from 'react';
import { FaUserCheck, FaInfoCircle, FaExclamationTriangle } from 'react-icons/fa';

export default function ReviewerFindings({ findings = [] }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaUserCheck className="text-cyan-400" /> Reviewer Agent Assessment & Findings
        </h3>
        <span className="font-mono text-xs font-bold text-emerald-400">Assessment: Excellent</span>
      </div>

      <div className="space-y-2">
        {findings && findings.length > 0 ? (
          findings.map((item, idx) => {
            const isMedium = item.severity === 'MEDIUM';
            const isInfo = item.severity === 'INFO';
            return (
              <div
                key={idx}
                className={`p-3 rounded-xl border flex items-start gap-3 text-xs ${
                  isMedium
                    ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                    : isInfo
                    ? 'bg-slate-900/80 border-slate-800 text-slate-300'
                    : 'bg-slate-900 border-slate-800 text-slate-300'
                }`}
              >
                {isMedium ? (
                  <FaExclamationTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                ) : (
                  <FaInfoCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <span className="font-mono font-bold text-[10px] uppercase tracking-wider text-cyan-400 mr-2">
                    [{item.severity}]
                  </span>
                  <span className="leading-relaxed">{item.message}</span>
                </div>
              </div>
            );
          })
        ) : (
          <p className="text-xs text-slate-500 italic">No static review findings reported.</p>
        )}
      </div>
    </div>
  );
}
