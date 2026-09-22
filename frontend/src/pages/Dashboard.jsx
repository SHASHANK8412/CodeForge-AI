import React, { useState, useEffect } from "react";
import AICommandCenter from "../components/dashboard/AICommandCenter";
import SmartRecommendations from "../components/dashboard/SmartRecommendations";
import RecentProjectsSection from "../components/dashboard/RecentProjectsSection";
import AIToolsSection from "../components/dashboard/AIToolsSection";
import SavedOutputsSection from "../components/dashboard/SavedOutputsSection";
import ActivityTimeline from "../components/dashboard/ActivityTimeline";
import ToastNotifications from "../components/dashboard/ToastNotifications";
import { RenameModal, ArchiveModal, DeleteModal } from "../components/dashboard/ProjectActions";
import {
  fetchProjects,
  renameProject,
  duplicateProject,
  archiveProject,
  deleteProject
} from "../services/projects";
import { FaSearch, FaBolt, FaFolder, FaBrain, FaBookmark, FaHistory } from "react-icons/fa";

export default function Dashboard({ setView, setActiveProjectName, setActiveGenerationId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all"); // all, projects, tools, saved, history
  const [globalSearch, setGlobalSearch] = useState("");

  // Modals & Notifications
  const [renameTarget, setRenameTarget] = useState(null);
  const [archiveTarget, setArchiveTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [notification, setNotification] = useState(null);

  const loadProjects = async () => {
    setLoading(true);
    const res = await fetchProjects({
      page: 1,
      pageSize: 6,
      search: globalSearch,
      status: "all",
      sort: "recently_updated"
    });
    setData(res);
    setLoading(false);
  };

  useEffect(() => {
    loadProjects();
  }, [globalSearch]);

  const notify = (text, type = "success") => {
    setNotification({ text, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleLaunchPrompt = (prompt, mode, model) => {
    sessionStorage.setItem("aiforge_pending_prompt", prompt);
    sessionStorage.setItem("aiforge_prompt_mode", mode);
    sessionStorage.setItem("aiforge_prompt_model", model);
    if (setView) setView("create");
    else window.location.href = "/create";
  };

  const handleNewProject = () => {
    if (setView) setView("create");
    else window.location.href = "/create";
  };

  const handleOpenProject = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView("build");
    else window.location.href = `/projects/${proj.generation_id}/build`;
  };

  const handleOpenCode = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView("code");
    else window.location.href = `/projects/${proj.generation_id}/code`;
  };

  const handleOpenQuality = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView("metrics");
    else window.location.href = `/projects/${proj.generation_id}/quality`;
  };

  const handleOpenDeploy = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView("plugins");
    else window.location.href = `/projects/${proj.generation_id}/deploy`;
  };

  const handleRenameConfirm = async (genId, newName) => {
    setRenameTarget(null);
    await renameProject(genId, newName);
    notify(`Renamed project to "${newName}"`);
    loadProjects();
  };

  const handleDuplicateConfirm = async (proj) => {
    const res = await duplicateProject(proj.generation_id);
    notify(`Duplicated ${proj.project_name} to ${res.new_name || "new copy"}`);
    loadProjects();
  };

  const handleArchiveConfirm = async (genId) => {
    setArchiveTarget(null);
    await archiveProject(genId);
    notify(`Archived project successfully`);
    loadProjects();
  };

  const handleDeleteConfirm = async (genId) => {
    setDeleteTarget(null);
    await deleteProject(genId);
    notify(`Deleted project permanently`, "error");
    loadProjects();
  };

  const projects = data?.projects || [];

  return (
    <div className="min-h-full bg-[#08090D] text-[#F5F7FA] font-sans p-4 sm:p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* 1. PRIMARY SECTION: AI COMMAND CENTER */}
      <AICommandCenter
        onLaunchPrompt={handleLaunchPrompt}
        setView={setView}
        onOpenCode={handleOpenCode}
        activeProjectName={projects[0]?.project_name}
      />

      {/* 2. SMART AI RECOMMENDATIONS */}
      <SmartRecommendations setView={setView} onOpenCode={handleOpenCode} />

      {/* 3. UNIFIED SECTION FILTER & SEARCH BAR */}
      <div className="bg-[#0F1117]/80 border border-[#242833] rounded-2xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 custom-scrollbar">
          {[
            { id: "all", label: "Overview", icon: <FaBolt size={10} /> },
            { id: "projects", label: "Projects", icon: <FaFolder size={10} /> },
            { id: "tools", label: "AI Tools", icon: <FaBrain size={10} /> },
            { id: "saved", label: "Saved Outputs", icon: <FaBookmark size={10} /> },
            { id: "history", label: "Activity", icon: <FaHistory size={10} /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all shrink-0 cursor-pointer ${
                activeTab === tab.id
                  ? "bg-[#8D5CF6] text-white shadow-md shadow-violet-500/20"
                  : "text-[#9AA1B2] hover:text-white hover:bg-[#151821]"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Search within dashboard */}
        <div className="relative w-full sm:w-72">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" size={11} />
          <input
            type="text"
            value={globalSearch}
            onChange={(e) => setGlobalSearch(e.target.value)}
            placeholder="Search projects & tools..."
            className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-[#64748B] outline-none"
          />
        </div>
      </div>

      {/* 4. DYNAMIC DASHBOARD SECTIONS BASED ON TAB */}
      {(activeTab === "all" || activeTab === "projects") && (
        <RecentProjectsSection
          projects={projects}
          onNewProject={handleNewProject}
          onOpenProject={handleOpenProject}
          onOpenCode={handleOpenCode}
          onOpenQuality={handleOpenQuality}
          onOpenDeploy={handleOpenDeploy}
          onRename={(p) => setRenameTarget(p)}
          onDuplicate={handleDuplicateConfirm}
          onArchive={(p) => setArchiveTarget(p)}
          onDelete={(p) => setDeleteTarget(p)}
          setView={setView}
        />
      )}

      {(activeTab === "all" || activeTab === "tools") && (
        <div className="pt-2">
          <AIToolsSection setView={setView} />
        </div>
      )}

      {(activeTab === "all" || activeTab === "saved") && (
        <div className="pt-2">
          <SavedOutputsSection setView={setView} />
        </div>
      )}

      {(activeTab === "all" || activeTab === "history") && (
        <div className="pt-2">
          <ActivityTimeline setView={setView} />
        </div>
      )}

      {/* Action Modals */}
      <RenameModal
        project={renameTarget}
        onSave={handleRenameConfirm}
        onClose={() => setRenameTarget(null)}
      />
      <ArchiveModal
        project={archiveTarget}
        onConfirm={handleArchiveConfirm}
        onClose={() => setArchiveTarget(null)}
      />
      <DeleteModal
        project={deleteTarget}
        onConfirm={handleDeleteConfirm}
        onClose={() => setDeleteTarget(null)}
      />

      {/* Toast Notifications */}
      <ToastNotifications
        notification={notification}
        onClose={() => setNotification(null)}
      />
    </div>
  );
}
