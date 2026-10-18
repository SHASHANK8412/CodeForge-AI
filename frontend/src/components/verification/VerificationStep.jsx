import React, { useState } from 'react';
import VerificationStatus from './VerificationStatus';

/** One check: its status, duration, environment, and the real output excerpt when it failed. */
export default function VerificationStep({ check }) {
  const [open, setOpen] = useState(false);
  const counts = Object.entries(check.counts || {}).map(([k, v]) => `${v} ${k}`).join(', ');
  return (
    <li className="rounded-lg border border-border-subtle p-2 text-[11px] text-text-secondary">
      <div className="flex flex-wrap items-center gap-2">
        <VerificationStatus status={check.status} />
        <span className="text-text-primary">{check.label}</span>
        {!check.required && <span className="text-text-muted">(optional)</span>}
        {check.duration_seconds != null && <span className="text-text-muted">{check.duration_seconds}s</span>}
        {counts && <span className="text-text-muted">· {counts}</span>}
        {check.timed_out && <span className="text-rose-200">· timed out</span>}
      </div>
      {(check.error_summary || check.reason) && <p className="mt-1">{check.error_summary || check.reason}</p>}
      <p className="text-[10px] text-text-muted">{check.profile}{check.environment ? ` · ${check.environment}` : ''}</p>
      {check.log_excerpt && (
        <>
          <button className="mt-1 text-[10px] text-text-muted underline" onClick={() => setOpen(!open)}>{open ? 'hide' : 'show'} output</button>
          {open && <pre className="mt-1 max-h-56 overflow-auto whitespace-pre-wrap break-words rounded bg-black/50 p-2 font-mono text-[10px] text-slate-300">{check.log_excerpt}</pre>}
        </>
      )}
    </li>
  );
}
