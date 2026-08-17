import React, { useState, useEffect } from 'react';
import DashboardHeader from '../components/dashboard/DashboardHeader';
import StatsCards from '../components/dashboard/StatsCards';
import ProjectToolbar from '../components/dashboard/ProjectToolbar';
import ProjectGrid from '../components/dashboard/ProjectGrid';
import ProjectPagination from '../components/dashboard/ProjectPagination';
import ToastNotifications from '../components/dashboard/ToastNotifications';
import { RenameModal, ArchiveModal, DeleteModal } from '../components/dashboard/ProjectActions';
import {
  fetchProjects,
  renameProject,
  duplicateProject,
  archiveProject,
  deleteProject
} from '../services/projects';

export default function Dashboard({ setView, setActiveProjectName, setActiveGenerationId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [promptInput, setPromptInput] = useState('');

  // Filters & Controls
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('recently_updated');

  // Modals & Notifications
  const [renameTarget, setRenameTarget] = useState(null);
  const [archiveTarget, setArchiveTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [notification, setNotification] = useState(null);

  const loadProjects = async () => {
    setLoading(true);
    const res = await fetchProjects({
      page,
      pageSize: 12,
      search: searchQuery,
      status: statusFilter,
      sort: sortBy
    });
    setData(res);
    setLoading(false);
  };

  useEffect(() => {
    loadProjects();
  }, [page, searchQuery, statusFilter, sortBy]);

  const notify = (text, type = 'success') => {
    setNotification({ text, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleNewProject = () => {
    if (setView) setView('create');
    else window.location.href = '/create';
  };

  const handleLaunchPrompt = () => {
    if (!promptInput.trim()) return;
    sessionStorage.setItem("aiforge_pending_prompt", promptInput.trim());
    if (setView) setView('create');
    else window.location.href = '/create';
  };

  const handleOpenProject = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView('build');
    else window.location.href = `/projects/${proj.generation_id}/build`;
  };

  const handleOpenCode = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView('code');
    else window.location.href = `/projects/${proj.generation_id}/code`;
  };

  const handleOpenQuality = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView('metrics');
    else window.location.href = `/projects/${proj.generation_id}/quality`;
  };

  const handleOpenDeploy = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView('plugins');
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
    notify(`Duplicated ${proj.project_name} to ${res.new_name || 'new copy'}`);
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
    notify(`Deleted project permanently`, 'error');
    loadProjects();
  };

  const projects = data?.projects || [];
  const total = data?.total || 0;
  const stats = data?.stats || {};

  return (
    <div className="min-h-screen bg-[#08090D] text-[#F5F7FA] font-sans p-6 space-y-8">
      {/* Top Header */}
      <DashboardHeader onNewProject={handleNewProject} onNotify={notify} />

      {/* Central Focus Prompt Hero */}
      <div className="bg-[#0F1117] border border-[#242833] rounded-2xl p-6 md:p-8 space-y-6 max-w-4xl mx-auto shadow-2xl relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-violet-600/5 rounded-full blur-[100px] pointer-events-none" />
        
        <div className="text-center space-y-2 max-w-xl mx-auto">
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-[#F5F7FA]">Build something amazing.</h2>
          <p className="text-xs text-[#9AA1B2]">Describe your software idea below. AIForge will architect, generate, test, and deploy it for you.</p>
        </div>

        <div className="space-y-4">
          <div className="relative bg-[#08090D] border border-[#242833] rounded-xl p-2 focus-within:border-[#8D5CF6] transition flex flex-col sm:flex-row items-center gap-3">
            <textarea
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              placeholder="e.g. Build a task manager dashboard with drag and drop columns..."
              rows={2}
              className="w-full sm:flex-1 bg-transparent text-xs text-[#F5F7FA] placeholder-[#9AA1B2]/40 outline-none resize-none px-2 py-1 leading-relaxed font-mono"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleLaunchPrompt();
                }
              }}
            />
            <button
              onClick={handleLaunchPrompt}
              className="w-full sm:w-auto shrink-0 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white px-4 py-2.5 rounded-lg text-xs font-bold transition shadow-md shadow-violet-500/25 hover:scale-[1.02] active:scale-95 cursor-pointer"
            >
              Generate Project →
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2 text-xs">
            <span className="text-[10px] uppercase font-bold text-[#9AA1B2]/50 mr-1">Suggested Ideas:</span>
            {[
              { label: "SaaS Dashboard", text: "Build a SaaS analytics dashboard with React, FastAPI, charts, and auth." },
              { label: "AI Chat Room", text: "Build a real-time AI assistant chat room with document upload support." },
              { label: "E-Commerce System", text: "Build a full e-commerce backend and frontend with Stripe checkout integrations." }
            ].map((item, idx) => (
              <button
                key={idx}
                onClick={() => setPromptInput(item.text)}
                className="bg-[#151821] hover:bg-[#1f2330] border border-[#242833] rounded-md px-2.5 py-1 text-[11px] text-[#9AA1B2] hover:text-[#F5F7FA] transition cursor-pointer"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* AI Command Center Live Activity Banner */}
      <div className="bg-[#0b101d] border border-cyan-500/30 rounded-2xl p-5 shadow-2xl max-w-4xl mx-auto space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
            <div>
              <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">AI Software Engineering Team Active</span>
              <div className="text-sm font-bold text-white">Full-Stack Platform Generation & Verification</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setView?.('code')}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition shadow cursor-pointer"
            >
              Open AI Workspace →
            </button>
            <button
              onClick={() => setView?.('xray')}
              className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-cyan-300 rounded-lg text-xs font-bold transition cursor-pointer"
            >
              Project X-Ray
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl">
            <div className="text-[10px] font-mono text-slate-400">PROJECT HEALTH</div>
            <div className="text-xl font-bold text-emerald-400 mt-0.5">94%</div>
            <div className="text-[10px] text-slate-500">6 Pillars Verified</div>
          </div>
          <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl">
            <div className="text-[10px] font-mono text-slate-400">TEST PASS RATE</div>
            <div className="text-xl font-bold text-cyan-400 mt-0.5">48 / 48</div>
            <div className="text-[10px] text-slate-500">0 Failures Detected</div>
          </div>
          <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl">
            <div className="text-[10px] font-mono text-slate-400">PROJECT MEMORY</div>
            <div className="text-xl font-bold text-violet-400 mt-0.5">12 Decisions</div>
            <div className="text-[10px] text-slate-500">Active & Versioned</div>
          </div>
          <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl">
            <div className="text-[10px] font-mono text-slate-400">ACTIVE AGENTS</div>
            <div className="text-xl font-bold text-white mt-0.5">8 Agents</div>
            <div className="text-[10px] text-emerald-400 font-semibold">Orchestrated</div>
          </div>
        </div>
      </div>

      {/* Summary Statistics */}
      <StatsCards stats={stats} />

      {/* Search & Filter Toolbar */}
      <ProjectToolbar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        sortBy={sortBy}
        setSortBy={setSortBy}
      />

      {/* Project Grid / Skeleton Loading */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-[#0F1117] border border-[#242833] rounded-2xl p-6 h-48 animate-pulse flex flex-col justify-between">
              <div className="space-y-3">
                <div className="w-1/2 h-4 bg-[#151821] rounded" />
                <div className="w-1/3 h-3 bg-[#151821] rounded" />
                <div className="w-full h-3 bg-[#151821] rounded" />
              </div>
              <div className="w-1/4 h-3 bg-[#151821] rounded self-end" />
            </div>
          ))}
        </div>
      ) : (
        <ProjectGrid
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
        />
      )}

      {/* Pagination */}
      <ProjectPagination
        page={page}
        total={total}
        pageSize={12}
        onPageChange={(newPage) => setPage(newPage)}
      />

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

      {/* Toast Notification Popups */}
      <ToastNotifications
        notification={notification}
        onClose={() => setNotification(null)}
      />
    </div>
  );
}
