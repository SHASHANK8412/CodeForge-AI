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
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 selection:bg-cyan-500 selection:text-white">
      {/* Top Header */}
      <DashboardHeader onNewProject={handleNewProject} onNotify={notify} />

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
            <div key={i} className="bg-slate-950 border border-slate-800 rounded-2xl p-6 h-48 animate-pulse flex flex-col justify-between">
              <div className="space-y-3">
                <div className="w-1/2 h-4 bg-slate-900 rounded" />
                <div className="w-1/3 h-3 bg-slate-900 rounded" />
                <div className="w-full h-3 bg-slate-900 rounded" />
              </div>
              <div className="w-1/4 h-3 bg-slate-900 rounded self-end" />
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
