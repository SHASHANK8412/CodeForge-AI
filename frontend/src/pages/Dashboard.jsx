import React, { useState, useEffect } from "react";
import AICommandCenter from "../components/dashboard/AICommandCenter";
import RecentRuns from "../components/dashboard/RecentRuns";
import RecentProjectsSection from "../components/dashboard/RecentProjectsSection";
import AIToolsSection from "../components/dashboard/AIToolsSection";
import SavedOutputsSection from "../components/dashboard/SavedOutputsSection";
import ActivityTimeline from "../components/dashboard/ActivityTimeline";
import { fetchProjects } from "../services/projects";

const EXPLORE_TABS = [
  { id: "tools", label: "AI tools" },
  { id: "saved", label: "Saved outputs" },
  { id: "history", label: "Activity" },
];

export default function Dashboard({ setView, setActiveProjectName, setActiveGenerationId }) {
  const [projects, setProjects] = useState(null);
  const [projectsError, setProjectsError] = useState(null);
  const [exploreTab, setExploreTab] = useState("tools");

  useEffect(() => {
    let cancelled = false;
    fetchProjects({ page: 1, pageSize: 6, sort: "recently_updated" }).then((res) => {
      if (cancelled) return;
      setProjects(res.projects || []);
      setProjectsError(res.error || null);
    });
    return () => { cancelled = true; };
  }, []);

  const go = (view, fallbackPath) => {
    if (setView) setView(view);
    else window.location.href = fallbackPath;
  };

  const handleLaunchPrompt = (prompt) => {
    sessionStorage.setItem("aiforge_pending_prompt", prompt);
    go("create", "/create");
  };

  const selectProject = (proj) => {
    setActiveProjectName?.(proj.project_name);
    setActiveGenerationId?.(proj.generation_id);
  };

  const handleOpenRun = (run) => {
    setActiveProjectName?.(run.project_id);
    setActiveGenerationId?.(run.generation_id);
    go("build", `/generations/${run.generation_id}`);
  };

  return (
    <div className="mx-auto min-h-full max-w-7xl space-y-10 bg-bg-base p-4 font-sans text-text-primary sm:p-6 lg:p-8">
      <AICommandCenter onLaunchPrompt={handleLaunchPrompt} />

      <RecentRuns onOpenRun={handleOpenRun} />

      <div>
        {projectsError && (
          <p className="mb-3 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-2.5 text-xs text-rose-300">
            Could not load projects: {projectsError}
          </p>
        )}
        <RecentProjectsSection
          projects={projects || []}
          loading={projects === null}
          onNewProject={() => go("create", "/create")}
          onOpenProject={(proj) => { selectProject(proj); go("project-details", `/projects/${proj.generation_id}`); }}
          onOpenCode={(proj) => { selectProject(proj); go("code", `/projects/${proj.generation_id}/code`); }}
          setView={setView}
        />
      </div>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-text-primary">Explore</h2>
          <div role="tablist" aria-label="Explore" className="flex gap-1 rounded-xl border border-border-dark bg-surface-card p-1">
            {EXPLORE_TABS.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={exploreTab === tab.id}
                onClick={() => setExploreTab(tab.id)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition cursor-pointer ${
                  exploreTab === tab.id ? "bg-surface-hover text-text-primary" : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        {exploreTab === "tools" && <AIToolsSection setView={setView} />}
        {exploreTab === "saved" && <SavedOutputsSection setView={setView} />}
        {exploreTab === "history" && <ActivityTimeline setView={setView} />}
      </section>
    </div>
  );
}
