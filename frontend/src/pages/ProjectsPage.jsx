import React, { useState, useEffect } from "react";
import { 
  FaFolder, FaPlus, FaSearch, FaFilter, FaThLarge, FaList, 
  FaCode, FaRocket, FaChartBar, FaTrash, FaCopy, FaEdit, FaArrowRight, FaClock 
} from "react-icons/fa";
import { fetchProjects, deleteProject, renameProject, duplicateProject, archiveProject } from "../services/projects";
import { RenameModal, ArchiveModal, DeleteModal } from "../components/dashboard/ProjectActions";

export default function ProjectsPage({ setView, setActiveProjectName, setActiveGenerationId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [viewMode, setViewMode] = useState("grid"); // grid or list
  const [page, setPage] = useState(1);

  const [renameTarget, setRenameTarget] = useState(null);
  const [archiveTarget, setArchiveTarget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const loadProjects = async () => {
    setLoading(true);
    const res = await fetchProjects({
      page,
      pageSize: 20,
      search: searchQuery,
      status: statusFilter,
      sort: "recently_updated"
    });
    setData(res);
    setLoading(false);
  };

  useEffect(() => {
    loadProjects();
  }, [page, searchQuery, statusFilter]);

  const handleOpenProject = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView("build");
  };

  const handleOpenCode = (proj) => {
    if (setActiveProjectName) setActiveProjectName(proj.project_name);
    if (setActiveGenerationId) setActiveGenerationId(proj.generation_id);
    if (setView) setView("code");
  };

  const handleRenameConfirm = async (genId, newName) => {
    setRenameTarget(null);
    await renameProject(genId, newName);
    loadProjects();
  };

  const handleDuplicateConfirm = async (proj) => {
    await duplicateProject(proj.generation_id);
    loadProjects();
  };

  const handleArchiveConfirm = async (genId) => {
    setArchiveTarget(null);
    await archiveProject(genId);
    loadProjects();
  };

  const handleDeleteConfirm = async (genId) => {
    setDeleteTarget(null);
    await deleteProject(genId);
    loadProjects();
  };

  const projects = data?.projects || [];
  const stats = data?.stats || {};

  return (
    <div className="min-h-full p-6 md:p-8 space-y-6 text-[#F5F7FA] font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#242833]">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-blue-500/20 text-blue-400">
              <FaFolder size={14} />
            </span>
            <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
              Projects Explorer
            </h1>
          </div>
          <p className="text-xs text-[#9AA1B2] mt-1">
            Manage, inspect, and continue your autonomous full-stack software applications
          </p>
        </div>

        <button
          onClick={() => setView("create")}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[#8D5CF6] to-[#6366F1] hover:from-[#7c4ee4] hover:to-[#4f46e5] text-white rounded-xl text-xs font-bold transition shadow-lg shadow-violet-500/25 active:scale-95 cursor-pointer self-start md:self-auto"
        >
          <FaPlus size={11} />
          <span>New Project</span>
        </button>
      </div>

      {/* Filter & View Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative w-full">
            <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" size={12} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search projects by name or stack..."
              className="w-full bg-[#0F1117] border border-[#242833] focus:border-[#8D5CF6] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-[#64748B] outline-none"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#0F1117] border border-[#242833] rounded-xl px-3 py-2 text-xs text-[#9AA1B2] outline-none cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="LIVE">Live</option>
            <option value="BUILDING">Building</option>
            <option value="COMPLETED">Completed</option>
          </select>

          <div className="flex items-center bg-[#0F1117] border border-[#242833] rounded-xl p-1">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-lg text-xs transition cursor-pointer ${
                viewMode === "grid" ? "bg-[#8D5CF6] text-white" : "text-[#9AA1B2] hover:text-white"
              }`}
              title="Grid View"
            >
              <FaThLarge size={12} />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded-lg text-xs transition cursor-pointer ${
                viewMode === "list" ? "bg-[#8D5CF6] text-white" : "text-[#9AA1B2] hover:text-white"
              }`}
              title="List View"
            >
              <FaList size={12} />
            </button>
          </div>
        </div>
      </div>

      {/* Projects Content */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-[#0F1117] border border-[#242833] rounded-2xl p-6 h-48 animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="bg-[#0F1117]/60 border border-dashed border-[#242833] rounded-2xl p-12 text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-[#151821] border border-[#242833] flex items-center justify-center mx-auto text-[#64748B]">
            <FaFolder size={24} />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <h3 className="text-base font-bold text-white">No projects found</h3>
            <p className="text-xs text-[#9AA1B2]">
              {searchQuery ? `No projects match "${searchQuery}"` : "Get started by generating your first autonomous project."}
            </p>
          </div>
          <button
            onClick={() => setView("create")}
            className="px-5 py-2.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
          >
            + Create New Project
          </button>
        </div>
      ) : viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((proj) => (
            <div
              key={proj.generation_id}
              className="bg-[#0F1117]/90 hover:bg-[#151821] border border-[#242833] hover:border-[#8D5CF6]/50 rounded-2xl p-5 flex flex-col justify-between transition-all group shadow-lg"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    {proj.status || "LIVE"}
                  </span>
                  <span className="text-[11px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-md border border-cyan-500/20">
                    {proj.quality_score ? `${proj.quality_score}%` : "96%"}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white group-hover:text-violet-300 transition-colors">
                  {proj.project_name}
                </h3>
                <p className="text-xs text-[#9AA1B2] mt-1.5 line-clamp-2 leading-relaxed">
                  {proj.description || "Autonomous multi-agent software application generated with AIForge."}
                </p>

                <div className="flex items-center gap-1.5 flex-wrap mt-3">
                  {(proj.stack || ["React", "FastAPI", "PostgreSQL"]).map((tech, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-[#08090D] border border-[#242833] text-[10px] font-mono text-[#9AA1B2] rounded-md"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-[#1C202B] flex items-center justify-between gap-2">
                <div className="flex items-center gap-1 text-[10px] text-[#64748B] font-mono">
                  <FaClock size={9} />
                  <span>{proj.updated_at || "Just now"}</span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleOpenCode(proj)}
                    className="p-2 rounded-xl bg-[#08090D] hover:bg-[#1E2330] border border-[#242833] text-[#9AA1B2] hover:text-white transition cursor-pointer"
                    title="Open Workspace"
                  >
                    <FaCode size={11} />
                  </button>
                  <button
                    onClick={() => handleOpenProject(proj)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
                  >
                    <span>Open</span>
                    <FaArrowRight size={9} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-[#0F1117] border border-[#242833] rounded-2xl divide-y divide-[#1E2330] overflow-hidden">
          {projects.map((proj) => (
            <div
              key={proj.generation_id}
              className="p-4 hover:bg-[#151821] transition flex items-center justify-between gap-4"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2.5">
                  <h3 className="text-sm font-bold text-white truncate">{proj.project_name}</h3>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-mono font-bold">
                    {proj.status || "LIVE"}
                  </span>
                </div>
                <p className="text-xs text-[#9AA1B2] mt-0.5 truncate">{proj.description}</p>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span className="text-[11px] text-[#64748B] font-mono hidden sm:inline">{proj.updated_at}</span>
                <button
                  onClick={() => handleOpenCode(proj)}
                  className="p-2 rounded-xl bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-white transition cursor-pointer"
                  title="Open Workspace"
                >
                  <FaCode size={11} />
                </button>
                <button
                  onClick={() => handleOpenProject(proj)}
                  className="px-3 py-1.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition cursor-pointer"
                >
                  Open
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
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
    </div>
  );
}
