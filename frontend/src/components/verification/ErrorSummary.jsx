import React from 'react';

const SEV = { critical: 'text-rose-300', high: 'text-amber-200', medium: 'text-slate-300' };

/** Classified failures: category, severity, the agent they are routed to, the evidence and the next action. */
export default function ErrorSummary({ failures, title = 'Failures' }) {
  if (!failures?.length) return null;
  return (
    <div className="text-[11px] text-text-secondary">
      <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">{title} ({failures.length})</p>
      <ul className="mt-1 space-y-1">{failures.map((f) => (
        <li key={f.id} className="rounded border border-border-subtle p-2">
          <p><span className={`font-semibold ${SEV[f.severity] || ''}`}>{f.category.replace(/_/g, ' ')}</span> · {f.severity} · check {f.check}
            {f.responsible_agent ? <> · routed to <span className="text-text-primary">{f.responsible_agent}</span></> : <> · <span className="text-amber-200">not repairable automatically</span></>}</p>
          <p className="text-text-primary">{f.summary}</p>
          {f.files?.length > 0 && <p className="font-mono text-[10px] text-text-muted">files: {f.files.join(', ')}</p>}
          {f.failing_tests?.length > 0 && <p className="font-mono text-[10px] text-text-muted">tests: {f.failing_tests.join(', ')}</p>}
          <p className="text-[10px] text-text-muted">next: {f.next_action} · classified by {f.classified_by}</p>
        </li>))}</ul>
    </div>
  );
}
