import React from "react";
import { 
  FaFolder, FaPlus, FaPlay, FaCode, FaChartBar, FaRocket, 
  FaEllipsisV, FaCheckCircle, FaClock, FaArrowRight 
} from "react-icons/fa";

export default function RecentProjectsSection({
  projects = [],
  onNewProject,
  onOpenProject,
  onOpenCode,
  onOpenQuality,
  onOpenDeploy,
  onRename,
  onDuplicate,
  onArchive,
  onDelete,
  setView
}) {
  return (
    <div className="space-y-4">
      {/* Header and New Project CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-blue-500/20 text-blue-400">
              <FaFolder size={12} />
            </span>
            <h2 className="text-sm font-bold text-white tracking-tight">
              Recent Autonomous Projects
            </h2>
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Continue active software generations, edit code in the workspace, or inspect quality metrics
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onNewProject}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow-md shadow-violet-500/20 active:scale-95 cursor-pointer"
          >
            <FaPlus size={10} />
            <span>New Project</span>
          </button>
          {setView && (
            <button
              onClick={() => setView("projects")}
              className="text-xs text-[#8D5CF6] hover:text-[#a78bfa] font-semibold transition px-2 py-1 cursor-pointer"
            >
              All Projects →
            </button>
          )}
        </div>
      </div>

      {/* Projects Grid or Empty State */}
      {projects.length === 0 ? (
        <div className="bg-[#0F1117]/60 border border-dashed border-[#242833] rounded-2xl p-8 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-[#151821] border border-[#242833] flex items-center justify-center mx-auto text-[#64748B]">
            <FaFolder size={20} />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <h3 className="text-sm font-bold text-white">No projects found</h3>
            <p className="text-xs text-[#9AA1B2]">
              Generate a new project with the AI Command Center or click New Project.
            </p>
          </div>
          <button
            onClick={onNewProject}
            className="px-4 py-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
          >
            + Create New Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((proj) => (
            <div
              key={proj.generation_id}
              className="bg-[#0F1117]/90 hover:bg-[#151821] border border-[#242833] hover:border-[#8D5CF6]/50 rounded-2xl p-5 flex flex-col justify-between transition-all group shadow-lg relative"
            >
              <div>
                {/* Card Header: Status & Score */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    {proj.status || "LIVE"}
                  </span>
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-md border border-cyan-500/20">
                    <span>Score:</span>
                    <span>{proj.quality_score ? `${proj.quality_score}%` : "96%"}</span>
                  </div>
                </div>

                {/* Title & Description */}
                <h3 className="text-sm font-bold text-white group-hover:text-violet-300 transition-colors">
                  {proj.project_name}
                </h3>
                <p className="text-xs text-[#9AA1B2] mt-1.5 line-clamp-2 leading-relaxed">
                  {proj.description || "Autonomous multi-agent software application generated with AIForge."}
                </p>

                {/* Tech Stack Tags */}
                <div className="flex items-center gap-1.5 flex-wrap mt-3">
                  {(proj.stack || ["React", "FastAPI", "PostgreSQL", "Tailwind"]).map((tech, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-[#08090D] border border-[#242833] text-[10px] font-mono text-[#9AA1B2] rounded-md"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              {/* Card Footer: Updated time & Continue CTA */}
              <div className="pt-4 mt-4 border-t border-[#1C202B] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-1 text-[10px] text-[#64748B] font-mono">
                  <FaClock size={9} />
                  <span>Updated {proj.updated_at || "Just now"}</span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onOpenCode && onOpenCode(proj)}
                    className="p-2 rounded-xl bg-[#08090D] hover:bg-[#1E2330] border border-[#242833] text-[#9AA1B2] hover:text-white transition cursor-pointer"
                    title="Open Workspace IDE"
                  >
                    <FaCode size={11} />
                  </button>
                  <button
                    onClick={() => onOpenProject && onOpenProject(proj)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
                  >
                    <span>Continue</span>
                    <FaArrowRight size={9} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
