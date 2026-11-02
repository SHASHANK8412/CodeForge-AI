import React, { useEffect, useRef, useState } from "react";
import { fetchInstalledModels } from "../../services/models";
import { FaArrowRight, FaUserCheck } from "react-icons/fa";

const EXAMPLES = [
  { label: "Task tracker", prompt: "Build a task tracker where users can create projects, add tasks with due dates and mark them done. FastAPI backend, React frontend, SQLite." },
  { label: "Recipe box", prompt: "Build a recipe box where users can add, search and delete recipes with ingredients and steps. FastAPI backend and React frontend." },
  { label: "Bookmark manager", prompt: "Build a bookmark manager where users can save links, tag them and filter by tag. FastAPI backend and React frontend." },
];

const PIPELINE = [
  { title: "Plan & architecture", note: "You approve the design", gate: true },
  { title: "Frontend · Backend · Database", note: "Written in parallel" },
  { title: "Review & security scan", note: "Static checks on every file" },
  { title: "Test → debug → patch", note: "Self-healing until tests pass" },
  { title: "Final review & export", note: "ZIP or GitHub", gate: true },
];

function EngineStatus({ engine }) {
  const loading = engine === null;
  const online = engine?.ollama_online;
  return (
    <div className="rounded-2xl border border-border-dark bg-bg-base/70 p-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Local AI engine</span>
        <span className={`flex items-center gap-1.5 text-[11px] font-medium ${loading ? "text-text-muted" : online ? "text-emerald-400" : "text-rose-400"}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${loading ? "bg-text-muted" : online ? "bg-emerald-400" : "bg-rose-400"}`} />
          {loading ? "Checking…" : online ? "Ollama online" : "Ollama offline"}
        </span>
      </div>
      {online ? (
        <dl className="mt-3 space-y-2 text-xs">
          <div className="flex items-center justify-between gap-3">
            <dt className="text-text-secondary">Planning</dt>
            <dd className="truncate font-mono text-text-primary">{engine.planning_model || "—"}</dd>
          </div>
          <div className="flex items-center justify-between gap-3">
            <dt className="text-text-secondary">Coding</dt>
            <dd className="truncate font-mono text-text-primary">{engine.coding_model || "—"}</dd>
          </div>
          <div className="flex items-center justify-between gap-3">
            <dt className="text-text-secondary">Installed</dt>
            <dd className="text-text-primary">{engine.models.length} model{engine.models.length === 1 ? "" : "s"}</dd>
          </div>
        </dl>
      ) : !loading && (
        <p className="mt-3 text-xs leading-relaxed text-text-secondary">
          Start Ollama and pull a model (for example <code className="font-mono text-text-primary">ollama pull qwen2.5-coder</code>) to generate projects.
        </p>
      )}
    </div>
  );
}

export default function AICommandCenter({ onLaunchPrompt }) {
  const [prompt, setPrompt] = useState("");
  const [engine, setEngine] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    fetchInstalledModels().then((res) => !cancelled && setEngine(res));
    return () => { cancelled = true; };
  }, []);

  const submit = (e) => {
    e?.preventDefault();
    const text = prompt.trim();
    if (text && onLaunchPrompt) onLaunchPrompt(text);
  };

  const applyExample = (text) => {
    setPrompt(text);
    inputRef.current?.focus();
  };

  return (
    <section className="relative overflow-hidden rounded-3xl border border-border-dark bg-gradient-to-br from-[#121522] via-surface-card to-bg-base">
      <div className="pointer-events-none absolute -right-32 -top-32 h-80 w-80 rounded-full bg-accent-violet/15 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 left-1/3 h-80 w-80 rounded-full bg-accent-cyan/10 blur-3xl" />

      <div className="relative grid gap-8 p-6 md:p-8 xl:grid-cols-[minmax(0,1fr)_300px]">
        {/* Prompt */}
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary md:text-[32px] md:leading-tight">
            What should we build today?
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-text-secondary">
            Describe an app in plain words. A team of local AI agents plans it, writes the frontend,
            backend and database, then reviews, tests and repairs the code before you approve it.
          </p>

          <form onSubmit={submit} className="mt-6">
            <div className="rounded-2xl border border-border-dark bg-bg-base/80 transition focus-within:border-accent-violet/70 focus-within:ring-4 focus-within:ring-accent-violet/10">
              <label htmlFor="dashboard-prompt" className="sr-only">Describe the app to build</label>
              <textarea
                id="dashboard-prompt"
                ref={inputRef}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) submit(e);
                }}
                rows={4}
                placeholder="e.g. A habit tracker where users log daily habits and see weekly streaks, with a FastAPI backend and React frontend"
                className="block w-full resize-none bg-transparent px-4 pt-4 text-sm leading-relaxed text-text-primary placeholder:text-text-muted outline-none"
              />
              <div className="flex flex-wrap items-center justify-between gap-3 px-4 pb-3 pt-2">
                <span className="text-[11px] text-text-muted">
                  <kbd className="rounded border border-border-dark bg-surface-elevated px-1.5 py-0.5 font-mono text-[10px]">Enter</kbd> to continue ·{" "}
                  <kbd className="rounded border border-border-dark bg-surface-elevated px-1.5 py-0.5 font-mono text-[10px]">Shift + Enter</kbd> new line
                </span>
                <button
                  type="submit"
                  disabled={!prompt.trim()}
                  className="inline-flex items-center gap-2 rounded-xl bg-accent-violet px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-accent-violet/25 transition hover:bg-[#7c4ee4] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none cursor-pointer"
                >
                  Generate project
                  <FaArrowRight size={11} />
                </button>
              </div>
            </div>
          </form>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs text-text-muted">Try an example:</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex.label}
                type="button"
                onClick={() => applyExample(ex.prompt)}
                className="rounded-full border border-border-dark bg-surface-elevated/70 px-3 py-1 text-xs text-text-secondary transition hover:border-accent-violet/50 hover:text-text-primary cursor-pointer"
              >
                {ex.label}
              </button>
            ))}
          </div>
        </div>

        {/* How a run works + engine */}
        <aside className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1 xl:content-start">
          <EngineStatus engine={engine} />
          <div className="rounded-2xl border border-border-dark bg-bg-base/70 p-4">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">How a run works</span>
            <ol className="mt-3 space-y-3">
              {PIPELINE.map((step, i) => (
                <li key={step.title} className="flex gap-3">
                  <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${step.gate ? "bg-amber-500/15 text-amber-400" : "bg-accent-violet/15 text-violet-300"}`}>
                    {step.gate ? <FaUserCheck size={9} /> : i + 1}
                  </span>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-text-primary">{step.title}</p>
                    <p className="text-[11px] text-text-muted">{step.note}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </aside>
      </div>
    </section>
  );
}
