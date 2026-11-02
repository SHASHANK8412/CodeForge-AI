import React from 'react';
import { FaShieldAlt, FaCheckCircle, FaExclamationTriangle, FaTimesCircle } from 'react-icons/fa';

const LOOK = {
  PASSED: { icon: FaCheckCircle, color: 'text-emerald-400' },
  WARNING: { icon: FaExclamationTriangle, color: 'text-amber-400' },
  FAILED: { icon: FaTimesCircle, color: 'text-rose-400' },
};

/** Only the security checks that ran are listed; severity counts appear only when a check produced them. */
export default function SecurityDashboard({ security = {} }) {
  const counts = ['critical', 'high', 'medium', 'low'].map((k) => [k, security[k]]);
  const hasCounts = counts.some(([, v]) => v != null);
  const checks = Object.entries(security.checks || {});

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaShieldAlt className="text-emerald-400" /> Security Checks
        </h3>
        <span className="font-mono text-[11px] text-slate-400">{checks.length} check(s) recorded</span>
      </div>

      {hasCounts && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center mb-6 font-mono">
          {counts.map(([k, v]) => (
            <div key={k} className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
              <div className="text-[11px] text-slate-400 font-sans capitalize">{k}</div>
              <div className="text-lg font-black text-white">{v ?? '—'}</div>
            </div>
          ))}
        </div>
      )}

      {checks.length ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-sans">
          {checks.map(([key, st]) => {
            const look = LOOK[st] || { icon: FaExclamationTriangle, color: 'text-slate-400' };
            const Icon = look.icon;
            return (
              <div key={key} className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between">
                <span className="text-slate-300 font-medium">{key.replace(/_/g, ' ')}</span>
                <span className={`font-mono text-[11px] flex items-center gap-1 ${look.color}`}>
                  <Icon className="w-3 h-3" /> {st}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-xs text-slate-500">No security check is recorded for this project. Run the Execution Guardian to scan it.</p>
      )}
    </div>
  );
}
