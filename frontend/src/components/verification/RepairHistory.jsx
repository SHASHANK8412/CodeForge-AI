import React from 'react';
import VerificationStatus from './VerificationStatus';

/** Every repair attempt: the agent, the strategy, files changed or rejected, and the checks before and after. */
export default function RepairHistory({ repairs, max }) {
  if (!repairs?.length) return <p className="text-[11px] text-text-muted">No repair was attempted{max != null ? ` (limit ${max})` : ''}.</p>;
  return (
    <ul className="space-y-2 text-[11px] text-text-secondary">{repairs.map((r) => (
      <li key={r.attempt} className="rounded-lg border border-border-subtle p-2">
        <p className="flex flex-wrap items-center gap-2"><span className="text-text-primary">Attempt {r.attempt}{max != null ? ` of ${max}` : ''}</span>
          <span>{r.agent} agent</span><span className="font-mono text-text-muted">{r.strategy}</span>
          <span className={r.outcome === 'resolved' ? 'text-emerald-300' : r.outcome === 'improved' ? 'text-lime-300' : 'text-amber-200'}>{r.outcome.replace(/_/g, ' ')}</span>
          {r.rolled_back && <span className="text-rose-200">rolled back</span>}</p>
        {r.files_changed?.length > 0 && <p className="font-mono text-[10px]">changed: {r.files_changed.join(', ')}</p>}
        {r.rejected_paths?.length > 0 && <p className="text-[10px] text-rose-200">rejected: {r.rejected_paths.map((x) => `${x.path} (${x.reason})`).join('; ')}</p>}
        {r.note && <p className="text-[10px] text-text-muted">{r.note}</p>}
        {Object.keys(r.after || {}).length > 0 && (
          <div className="mt-1 flex flex-wrap gap-2 text-[10px]">{Object.entries(r.after).map(([name, after]) => (
            <span key={name} className="flex items-center gap-1">{name}: <VerificationStatus status={r.before?.[name]} />→<VerificationStatus status={after} /></span>))}</div>)}
      </li>))}</ul>
  );
}
