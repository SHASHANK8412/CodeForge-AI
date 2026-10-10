import React, { useEffect, useState } from "react";
import { listGenerations } from "../../services/generation";
import { FaArrowRight, FaCheckCircle, FaExclamationTriangle, FaHourglassHalf, FaUserCheck, FaRedo } from "react-icons/fa";

const ACTIVE = ["queued", "planning", "running", "building"];
const NEEDS_APPROVAL = ["waiting_for_approval", "paused"];

const STATUS = {
  completed: { label: "Completed", tone: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", Icon: FaCheckCircle },
  failed: { label: "Failed", tone: "text-rose-400 bg-rose-500/10 border-rose-500/20", Icon: FaExclamationTriangle },
  cancelled: { label: "Cancelled", tone: "text-text-secondary bg-surface-elevated border-border-dark", Icon: FaExclamationTriangle },
  approval: { label: "Needs approval", tone: "text-amber-400 bg-amber-500/10 border-amber-500/20", Icon: FaUserCheck },
  active: { label: "Running", tone: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20", Icon: FaHourglassHalf },
};

function statusOf(status) {
  if (NEEDS_APPROVAL.includes(status)) return STATUS.approval;
  if (ACTIVE.includes(status)) return STATUS.active;
  return STATUS[status] || STATUS.cancelled;
}

function timeAgo(iso) {
  if (!iso) return "";
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const units = [["d", 86400], ["h", 3600], ["m", 60]];
  for (const [unit, size] of units) {
    if (seconds >= size) return `${Math.floor(seconds / size)}${unit} ago`;
  }
  return "";
}

function StatCard({ label, value, hint, tone }) {
  return (
    <div className="rounded-2xl border border-border-dark bg-surface-card/80 p-4">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className={`mt-1 text-2xl font-semibold tabular-nums ${tone}`}>{value ?? "—"}</p>
      <p className="mt-0.5 text-[11px] text-text-muted">{hint}</p>
    </div>
  );
}

export default function RecentRuns({ onOpenRun }) {
  const [runs, setRuns] = useState(null);
  const [error, setError] = useState(null);

  const load = () => {
    setError(null);
    listGenerations()
      .then(({ generations = [] }) => {
        const sorted = [...generations].sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""));
        setRuns(sorted);
      })
      .catch((err) => setError(err?.message || "Could not load runs"));
  };

  useEffect(load, []);

  const count = (statuses) => runs?.filter((r) => statuses.includes(r.status)).length;
  const attention = (runs || []).filter((r) => NEEDS_APPROVAL.includes(r.status) || ACTIVE.includes(r.status));
  const recent = attention.length ? attention.slice(0, 5) : (runs || []).slice(0, 5);

  return (
    <section className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Completed" value={count(["completed"])} hint={runs ? `of ${runs.length} runs` : "Loading…"} tone="text-emerald-400" />
        <StatCard label="Needs your approval" value={count(NEEDS_APPROVAL)} hint="Paused at a review gate" tone="text-amber-400" />
        <StatCard label="Running" value={count(ACTIVE)} hint="In the pipeline now" tone="text-cyan-400" />
        <StatCard label="Failed" value={count(["failed", "cancelled"])} hint="Failed, interrupted or cancelled" tone="text-rose-400" />
      </div>

      <div className="rounded-2xl border border-border-dark bg-surface-card/80">
        <div className="flex items-center justify-between gap-3 border-b border-border-subtle px-5 py-3.5">
          <div>
            <h2 className="text-sm font-semibold text-text-primary">
              {attention.length ? "Runs that need you" : "Recent runs"}
            </h2>
            <p className="text-xs text-text-muted">
              {attention.length ? "Approve a paused run or follow one that is still running" : "Your latest generation runs"}
            </p>
          </div>
          <button onClick={load} className="rounded-lg p-2 text-text-muted transition hover:bg-surface-elevated hover:text-text-primary cursor-pointer" title="Refresh">
            <FaRedo size={11} />
          </button>
        </div>

        {error ? (
          <p className="px-5 py-6 text-sm text-rose-400">Could not reach the backend: {error}</p>
        ) : runs === null ? (
          <div className="space-y-2 p-5">
            {[0, 1, 2].map((i) => <div key={i} className="h-12 animate-pulse rounded-xl bg-surface-elevated/60" />)}
          </div>
        ) : recent.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-text-secondary">No runs yet. Describe an app above to start your first one.</p>
        ) : (
          <ul className="divide-y divide-border-subtle">
            {recent.map((run) => {
              const s = statusOf(run.status);
              const isActive = ACTIVE.includes(run.status);
              return (
                <li key={run.generation_id}>
                  <button
                    onClick={() => onOpenRun?.(run)}
                    className="group flex w-full items-center gap-4 px-5 py-3.5 text-left transition hover:bg-surface-elevated/60 cursor-pointer"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-sm font-medium text-text-primary">{run.project_id}</span>
                        <span className="shrink-0 text-[11px] text-text-muted">{timeAgo(run.created_at)}</span>
                      </div>
                      <p className="mt-0.5 truncate text-xs text-text-muted">
                        {run.status === "failed" && run.error ? run.error : run.prompt || run.generation_id}
                      </p>
                      {isActive && (
                        <div className="mt-2 h-1 w-full max-w-xs overflow-hidden rounded-full bg-surface-elevated">
                          <div className="h-full rounded-full bg-accent-cyan transition-all" style={{ width: `${run.progress || 0}%` }} />
                        </div>
                      )}
                    </div>
                    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${s.tone}`}>
                      <s.Icon size={10} />
                      {s.label}
                    </span>
                    <FaArrowRight size={11} className="shrink-0 text-text-muted transition group-hover:translate-x-0.5 group-hover:text-text-primary" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
