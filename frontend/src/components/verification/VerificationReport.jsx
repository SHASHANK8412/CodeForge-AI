import React from 'react';
import VerificationStatus from './VerificationStatus';

/** The final report: what was tested, what was not, the failures found / resolved / remaining, and how to run. */
export default function VerificationReport({ report, onDownload }) {
  if (!report?.status) return null;
  return (
    <div className="space-y-2 text-[11px] text-text-secondary">
      <p className="flex flex-wrap items-center gap-2"><VerificationStatus status={report.status} /> <span className="text-text-primary">{report.statement}</span>
        {onDownload && <button className="ml-auto rounded border border-border-dark px-2 py-0.5" onClick={onDownload}>Download (md)</button>}</p>
      <div className="grid gap-2 md:grid-cols-2">
        <div><p className="text-[10px] uppercase text-text-muted">What was tested</p>{(report.what_was_tested || []).map((x) => <p key={x}>• {x}</p>)}{!report.what_was_tested?.length && <p>nothing ran</p>}</div>
        <div><p className="text-[10px] uppercase text-text-muted">What was not tested</p>{(report.what_was_not_tested || []).map((x) => <p key={x} className="text-amber-200">• {x}</p>)}{!report.what_was_not_tested?.length && <p>—</p>}</div>
        <div><p className="text-[10px] uppercase text-text-muted">Failures discovered / resolved / remaining</p>
          <p>{report.failures_discovered?.length ?? 0} / {report.failures_resolved?.length ?? 0} / {report.remaining_failures?.length ?? 0} · {report.repair_attempts} repair attempt(s)</p>
          {(report.remaining_failures || []).map((f, i) => <p key={i} className="text-rose-200">• [{f.category}] {f.summary}</p>)}</div>
        <div><p className="text-[10px] uppercase text-text-muted">Runtime startup</p><p>{report.runtime_startup?.status}: {report.runtime_startup?.detail}</p>
          <p className="mt-1 text-[10px] uppercase text-text-muted">How to run it</p>{(report.how_to_run || []).map((x) => <p key={x} className="font-mono">{x}</p>)}</div>
      </div>
      {(report.warnings || []).length > 0 && <ul className="text-amber-200">{report.warnings.map((w) => <li key={w}>warning: {w}</li>)}</ul>}
      <ul className="text-[10px] text-text-muted">{(report.limitations || []).map((x) => <li key={x}>limitation: {x}</li>)}</ul>
    </div>
  );
}
