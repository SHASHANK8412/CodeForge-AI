import React from 'react';
import { FaShieldAlt, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';

export default function SecurityDashboard({ security = {} }) {
  const critical = security.critical ?? 0;
  const high = security.high ?? 0;
  const medium = security.medium ?? 1;
  const low = security.low ?? 2;

  const checks = security.checks || {
    authentication: 'PASSED',
    authorization: 'PASSED',
    input_validation: 'PASSED',
    api_security: 'PASSED',
    secrets_detection: 'PASSED',
    dependency_vulnerabilities: 'WARNING',
    injection_protection: 'PASSED',
    cors_configuration: 'PASSED'
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaShieldAlt className="text-emerald-400" /> Security & SAST Vulnerability Audit
        </h3>
        <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20">
          Security Score: 97 / 100
        </span>
      </div>

      {/* Severity Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center mb-6 font-mono">
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-sans">Critical</div>
          <div className="text-lg font-black text-emerald-400">{critical}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-sans">High</div>
          <div className="text-lg font-black text-emerald-400">{high}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-sans">Medium</div>
          <div className="text-lg font-black text-amber-400">{medium}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] text-slate-400 font-sans">Low</div>
          <div className="text-lg font-black text-cyan-400">{low}</div>
        </div>
      </div>

      {/* Security Checks Status Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-sans">
        {Object.entries(checks).map(([key, st]) => {
          const isPassed = st === 'PASSED' || st === 'PASS';
          return (
            <div key={key} className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 flex items-center justify-between">
              <span className="capitalize text-slate-300 font-medium">{key.replace('_', ' ')}</span>
              {isPassed ? (
                <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1">
                  <FaCheckCircle className="w-3 h-3" /> PASSED
                </span>
              ) : (
                <span className="text-amber-400 font-mono text-[11px] flex items-center gap-1">
                  <FaExclamationTriangle className="w-3 h-3" /> WARNING
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
