import React from 'react';

const TONES = {
  VERIFIED: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  PASSED: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  VERIFIED_WITH_WARNINGS: 'bg-lime-500/15 text-lime-300 border-lime-500/30',
  FAILED: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  BLOCKED: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  SKIPPED: 'bg-slate-700/50 text-slate-300 border-slate-600',
  PENDING: 'bg-slate-700/50 text-slate-300 border-slate-600',
  CANCELLED: 'bg-slate-700/50 text-slate-300 border-slate-600',
  RUNNING: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  COMPATIBLE: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  COMPATIBLE_WITH_WARNINGS: 'bg-lime-500/15 text-lime-300 border-lime-500/30',
  INCOMPATIBLE: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  NOT_CHECKED: 'bg-slate-700/50 text-slate-300 border-slate-600',
};

/** A status badge. Labels come from the API; nothing is assumed to have passed. */
export default function VerificationStatus({ status }) {
  if (!status) return null;
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${TONES[status] || TONES.PENDING}`}>
      {status === 'RUNNING' && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
      {String(status).replace(/_/g, ' ')}
    </span>
  );
}
