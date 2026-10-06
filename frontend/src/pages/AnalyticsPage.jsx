import React, { useState, useEffect } from "react";
import { FaChartLine } from "react-icons/fa";
import { fetchAnalyticsMetrics } from "../services/analyticsApi";

const fmt = (n) => (n == null ? "—" : Number(n).toLocaleString());

function Kpi({ label, value, hint, tone = "text-text-primary" }) {
  return (
    <div className="rounded-2xl border border-border-dark bg-surface-card p-4">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className={`mt-1 text-2xl font-semibold tabular-nums ${tone}`}>{value}</p>
      {hint && <p className="mt-0.5 text-[11px] text-text-muted">{hint}</p>}
    </div>
  );
}

/** Usage aggregated from recorded generation runs: real token counts from Ollama. */
export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalyticsMetrics().then((res) => (res.error ? setError(res.error) : setMetrics(res)));
  }, []);

  if (error) {
    return <p className="m-8 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">Could not load analytics: {error}</p>;
  }
  if (!metrics) {
    return <div className="flex h-full items-center justify-center text-sm text-text-muted">Loading usage…</div>;
  }

  const { summary, model_distribution, top_agents, daily_activity } = metrics;
  const maxDaily = Math.max(1, ...daily_activity.map((d) => d.tokens));

  return (
    <div className="mx-auto min-h-full max-w-6xl space-y-6 p-4 font-sans text-text-primary sm:p-6 lg:p-8">
      <header>
        <div className="flex items-center gap-2 text-xs text-text-muted"><FaChartLine size={11} /> Usage</div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Token usage and runs</h1>
        <p className="mt-1 text-sm text-text-secondary">
          Real token counts reported by your local models for every generation run.
          {summary.runs_with_token_data < summary.total_runs && ` ${summary.total_runs - summary.runs_with_token_data} older run(s) predate token tracking.`}
        </p>
      </header>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="Generation runs" value={fmt(summary.total_runs)} hint={`${fmt(summary.completed_runs)} completed · ${fmt(summary.failed_runs)} failed`} />
        <Kpi label="Tokens" value={fmt(summary.total_tokens)} hint={`${fmt(summary.prompt_tokens)} in · ${fmt(summary.completion_tokens)} out`} tone="text-violet-300" />
        <Kpi label="LLM calls" value={fmt(summary.llm_calls)} hint={`${fmt(summary.cached_calls)} served from cache`} tone="text-cyan-300" />
        <Kpi label="API cost" value={`$${(summary.cost_usd || 0).toFixed(2)}`} hint={summary.cost_usd ? "At your configured rates" : "Local models: no API cost"} tone="text-emerald-300" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-border-dark bg-surface-card p-5">
          <h2 className="text-sm font-semibold">Tokens by model</h2>
          {model_distribution.length === 0 ? <p className="mt-3 text-sm text-text-secondary">No token data yet. Start a generation run.</p> : (
            <ul className="mt-4 space-y-3">
              {model_distribution.map((m) => (
                <li key={m.model}>
                  <div className="flex justify-between font-mono text-xs">
                    <span className="text-text-primary">{m.model}</span>
                    <span className="text-text-secondary">{fmt(m.tokens)} · {m.usage_pct}%</span>
                  </div>
                  <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-elevated">
                    <div className="h-full rounded-full bg-accent-violet" style={{ width: `${m.usage_pct}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-border-dark bg-surface-card p-5">
          <h2 className="text-sm font-semibold">Tokens by agent</h2>
          {top_agents.length === 0 ? <p className="mt-3 text-sm text-text-secondary">No token data yet.</p> : (
            <ul className="mt-3 divide-y divide-border-subtle">
              {top_agents.map((a) => (
                <li key={a.agent} className="flex items-center justify-between py-2.5 text-sm">
                  <span className="capitalize text-text-primary">{a.agent.replace(/^project_/, "").replace(/_/g, " ")}</span>
                  <span className="font-mono text-xs text-text-secondary">{fmt(a.tokens)} tokens · {fmt(a.calls)} calls</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="rounded-2xl border border-border-dark bg-surface-card p-5">
        <h2 className="text-sm font-semibold">Last 7 days</h2>
        <div className="mt-6 flex h-40 items-end gap-3 border-b border-border-subtle px-2">
          {daily_activity.map((d) => (
            <div key={d.date} className="group flex h-full flex-1 flex-col items-center justify-end gap-2" title={`${d.date}: ${d.runs} run(s), ${fmt(d.tokens)} tokens`}>
              <span className="text-[10px] text-text-muted opacity-0 transition group-hover:opacity-100">{fmt(d.tokens)}</span>
              <div className="w-full rounded-t-lg bg-gradient-to-t from-accent-blue to-accent-violet" style={{ height: `${Math.max(2, (d.tokens / maxDaily) * 100)}%`, opacity: d.tokens ? 1 : 0.25 }} />
              <span className="text-[11px] text-text-secondary">{d.day}</span>
            </div>
          ))}
        </div>
        <p className="mt-2 text-[11px] text-text-muted">Bar height: tokens per day. Hover for runs and exact counts.</p>
      </section>
    </div>
  );
}
