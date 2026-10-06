import React from "react";
import { FaFolder, FaPlus, FaCode, FaClock, FaArrowRight } from "react-icons/fa";

const STATUS_TONE = {
  LIVE: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  COMPLETED: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  FAILED: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  WAITING_FOR_APPROVAL: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  RUNNING: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
};

const prettyStatus = (s) => (s || "UNKNOWN").replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

export default function RecentProjectsSection({
  projects = [],
  loading = false,
  onNewProject,
  onOpenProject,
  onOpenCode,
  setView
}) {
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">Projects</h2>
          <p className="text-xs text-text-muted">Generated code on disk. Open one to browse files, run tests or export it.</p>
        </div>
        <div className="flex items-center gap-2">
          {setView && (
            <button
              onClick={() => setView("projects")}
              className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-text-secondary transition hover:bg-surface-elevated hover:text-text-primary cursor-pointer"
            >
              View all
            </button>
          )}
          <button
            onClick={onNewProject}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border-dark bg-surface-elevated px-3 py-1.5 text-xs font-medium text-text-primary transition hover:border-accent-violet/50 cursor-pointer"
          >
            <FaPlus size={9} />
            New project
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => <div key={i} className="h-44 animate-pulse rounded-2xl border border-border-dark bg-surface-card/60" />)}
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border-dark bg-surface-card/40 p-10 text-center">
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl border border-border-dark bg-surface-elevated text-text-muted">
            <FaFolder size={18} />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-text-primary">No projects yet</h3>
          <p className="mt-1 text-xs text-text-secondary">Finished generations show up here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((proj) => (
            <article
              key={proj.generation_id}
              className="group flex flex-col rounded-2xl border border-border-dark bg-surface-card/80 p-5 transition hover:border-accent-violet/40 hover:bg-surface-elevated/50"
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="min-w-0 truncate text-sm font-semibold text-text-primary" title={proj.project_name}>
                  {proj.project_name}
                </h3>
                <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium ${STATUS_TONE[proj.status] || "text-text-secondary bg-surface-elevated border-border-dark"}`}>
                  {prettyStatus(proj.status)}
                </span>
              </div>

              <p className="mt-2 line-clamp-2 min-h-[2.5rem] text-xs leading-relaxed text-text-secondary">
                {proj.description || <span className="text-text-muted">No prompt recorded for this folder.</span>}
              </p>

              <div className="mt-3 flex flex-wrap gap-1.5">
                {(proj.stack || []).map((tech) => (
                  <span key={tech} className="rounded-md border border-border-dark bg-bg-base px-2 py-0.5 font-mono text-[10px] text-text-secondary">
                    {tech}
                  </span>
                ))}
              </div>

              <dl className="mt-4 grid grid-cols-2 gap-3 rounded-xl bg-bg-base/60 px-3 py-2.5 text-xs">
                <div>
                  <dt className="text-[10px] uppercase tracking-wide text-text-muted">Quality</dt>
                  <dd className="mt-0.5 font-medium text-text-primary">{proj.quality_score != null ? `${proj.quality_score}%` : "Not measured"}</dd>
                </div>
                <div>
                  <dt className="text-[10px] uppercase tracking-wide text-text-muted">Tests</dt>
                  <dd className="mt-0.5 font-medium text-text-primary">
                    {proj.tests_total != null ? `${proj.tests_passed ?? 0} / ${proj.tests_total} passed` : "Not run"}
                  </dd>
                </div>
              </dl>

              <div className="mt-4 flex items-center justify-between gap-3 border-t border-border-subtle pt-4">
                <span className="flex items-center gap-1.5 text-[11px] text-text-muted">
                  <FaClock size={9} />
                  {proj.updated_at ? `Updated ${proj.updated_at}` : "—"}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onOpenCode?.(proj)}
                    className="rounded-lg border border-border-dark p-2 text-text-secondary transition hover:bg-surface-hover hover:text-text-primary cursor-pointer"
                    title="Open in code workspace"
                    aria-label={`Open ${proj.project_name} in the code workspace`}
                  >
                    <FaCode size={11} />
                  </button>
                  <button
                    onClick={() => onOpenProject?.(proj)}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-accent-violet px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-[#7c4ee4] cursor-pointer"
                  >
                    Open
                    <FaArrowRight size={9} />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
