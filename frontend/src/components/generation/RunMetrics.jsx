import React, { useEffect, useState } from 'react';
import { getGeneration, isTerminalStatus } from '../../services/generation';

const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString());

function elapsed(startedAt, completedAt) {
  if (!startedAt) return '—';
  const end = completedAt ? new Date(completedAt) : new Date();
  const secs = Math.max(0, Math.round((end - new Date(startedAt)) / 1000));
  const m = Math.floor(secs / 60);
  return m ? `${m}m ${String(secs % 60).padStart(2, '0')}s` : `${secs}s`;
}

function Cell({ label, value, hint, tone = 'text-text-primary' }) {
  return (
    <div className="min-w-0 rounded-xl bg-bg-base/60 px-3 py-2.5">
      <p className="truncate text-[10px] uppercase tracking-wide text-text-muted">{label}</p>
      <p className={`mt-0.5 truncate text-sm font-semibold tabular-nums ${tone}`}>{value}</p>
      {hint && <p className="truncate text-[10px] text-text-muted">{hint}</p>}
    </div>
  );
}

/**
 * Live numbers for one generation run: real token usage, build time, tests, code-quality gate,
 * auto-fixes, security and GitHub status. Polls the run while it is active; values that were
 * never measured show as "—".
 */
export default function RunMetrics({ generationId, status }) {
  const [run, setRun] = useState(null);
  const [, setTick] = useState(0);
  const active = status && !isTerminalStatus(status);

  useEffect(() => {
    if (!generationId) return undefined;
    let cancelled = false;
    const load = () => getGeneration(generationId).then((r) => !cancelled && setRun(r)).catch(() => {});
    load();
    const poll = active ? setInterval(load, 5000) : null;
    const clock = active ? setInterval(() => setTick((t) => t + 1), 1000) : null;
    return () => { cancelled = true; clearInterval(poll); clearInterval(clock); };
  }, [generationId, active]);

  const usage = run?.usage || {};
  const m = run?.metrics || {};
  const testsKnown = m.tests_total != null && m.tests_status != null;
  const sec = m.security_gate;

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Run metrics</h3>
        {active && <span className="text-[10px] text-cyan-400">live</span>}
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <Cell label="Build time" value={elapsed(run?.started_at, run?.completed_at)} />
        <Cell label="LLM tokens" value={fmt(usage.total_tokens)} hint={usage.llm_calls != null ? `${fmt(usage.llm_calls)} calls · ${fmt(usage.cached_calls)} cached` : null} tone="text-violet-300" />
        <Cell
          label="Tests"
          value={testsKnown ? `${fmt(m.tests_passed)} / ${fmt(m.tests_total)}` : '—'}
          hint={testsKnown ? (m.tests_status === 'PASS' ? 'passing' : `${fmt(m.tests_failed)} failing`) : 'not run yet'}
          tone={!testsKnown ? 'text-text-primary' : m.tests_status === 'PASS' ? 'text-emerald-400' : 'text-rose-400'}
        />
        <Cell label="Auto-fixes" value={fmt(m.auto_fixes ?? 0)} hint="debug → patch cycles applied" />
        <Cell
          label="Code-quality gate"
          value={m.lint_errors == null ? '—' : m.lint_errors === 0 ? 'Passing' : `${m.lint_errors} blocking`}
          hint={m.lint_warnings ? `${m.lint_warnings} warning(s)` : null}
          tone={m.lint_errors == null ? 'text-text-primary' : m.lint_errors === 0 ? 'text-emerald-400' : 'text-rose-400'}
        />
        <Cell
          label="Security"
          value={sec ? `${sec}${m.security_score != null ? ` · ${m.security_score}` : ''}` : '—'}
          hint={m.security_findings != null ? `${m.security_findings} finding(s)${m.security_critical ? `, ${m.security_critical} critical` : ''}` : null}
          tone={!sec ? 'text-text-primary' : sec === 'PASSED' ? 'text-emerald-400' : sec === 'FAILED' ? 'text-rose-400' : 'text-amber-400'}
        />
        <Cell label="API cost" value={usage.cost_usd ? `$${usage.cost_usd.toFixed(4)}` : '$0.00'} hint={usage.cost_usd ? 'at configured rates' : 'local models'} />
        <Cell label="GitHub" value={m.github_status ? m.github_status.replace(/_/g, ' ').toLowerCase() : '—'} hint={m.github_repo || null} />
      </div>
    </section>
  );
}
