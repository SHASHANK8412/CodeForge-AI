import React, { useState } from 'react';
import { FaCheckCircle, FaSpinner, FaRocket, FaExclamationTriangle, FaEllipsisV, FaCode, FaShieldAlt, FaCopy, FaEdit, FaArchive, FaTrash } from 'react-icons/fa';

export default function ProjectCard({
  project,
  onOpenProject,
  onOpenCode,
  onOpenQuality,
  onOpenDeploy,
  onRename,
  onDuplicate,
  onArchive,
  onDelete
}) {
  const [showMenu, setShowMenu] = useState(false);

  const getStatusBadge = (st) => {
    switch (st?.toUpperCase()) {
      case 'LIVE':
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase">
            <FaRocket className="w-2.5 h-2.5" /> Live
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase">
            <FaCheckCircle className="w-2.5 h-2.5" /> Completed
          </span>
        );
      case 'BUILDING':
      case 'QUEUED':
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase animate-pulse">
            <FaSpinner className="w-2.5 h-2.5 animate-spin" /> Building
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 uppercase">
            <FaExclamationTriangle className="w-2.5 h-2.5" /> Failed
          </span>
        );
    }
  };

  const stackText = project.stack ? project.stack.join(' · ') : 'React · FastAPI · PostgreSQL';

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 shadow-xl hover:border-slate-700 transition flex flex-col justify-between relative font-sans">
      {/* Top Card Bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">🍔</span>
            <h3 className="text-base font-extrabold text-white tracking-tight truncate max-w-[180px]">
              {project.project_name}
            </h3>
          </div>

          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-900 transition"
            >
              <FaEllipsisV className="w-3.5 h-3.5" />
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-1 w-44 bg-slate-950 border border-slate-800 rounded-xl p-1 shadow-2xl z-50 text-xs">
                <button
                  onClick={() => { setShowMenu(false); onOpenProject(project); }}
                  className="w-full text-left px-3 py-1.5 hover:bg-slate-900 rounded text-slate-200 flex items-center gap-2 transition"
                >
                  <FaCheckCircle className="text-cyan-400" /> Open Pipeline
                </button>
                <button
                  onClick={() => { setShowMenu(false); onOpenCode(project); }}
                  className="w-full text-left px-3 py-1.5 hover:bg-slate-900 rounded text-slate-200 flex items-center gap-2 transition"
                >
                  <FaCode className="text-emerald-400" /> Code Workspace
                </button>
                <button
                  onClick={() => { setShowMenu(false); onOpenQuality(project); }}
                  className="w-full text-left px-3 py-1.5 hover:bg-slate-900 rounded text-slate-200 flex items-center gap-2 transition"
                >
                  <FaShieldAlt className="text-amber-400" /> Quality Report
                </button>
                <button
                  onClick={() => { setShowMenu(false); onOpenDeploy(project); }}
                  className="w-full text-left px-3 py-1.5 hover:bg-slate-900 rounded text-slate-200 flex items-center gap-2 transition"
                >
                  <FaRocket className="text-purple-400" /> Deployment
                </button>

                <div className="border-t border-slate-800 my-1" />

                <button
                  onClick={() => { setShowMenu(false); onDuplicate(project); }}
                  className="w-full text-left px-3 py-1.5 hover:bg-slate-900 rounded text-slate-200 flex items-center gap-2 transition"
                >
                  <FaCopy className="text-slate-400" /> Duplicate
                </button>
                <button
                  onClick={() => { setShowMenu(false); onRename(project); }}
                  className="w-full text-left px-3 py-1.5 hover:bg-slate-900 rounded text-slate-200 flex items-center gap-2 transition"
                >
                  <FaEdit className="text-slate-400" /> Rename
                </button>
                <button
                  onClick={() => { setShowMenu(false); onArchive(project); }}
                  className="w-full text-left px-3 py-1.5 hover:bg-slate-900 rounded text-slate-200 flex items-center gap-2 transition"
                >
                  <FaArchive className="text-slate-400" /> Archive
                </button>
                <button
                  onClick={() => { setShowMenu(false); onDelete(project); }}
                  className="w-full text-left px-3 py-1.5 hover:bg-slate-900 rounded text-rose-400 flex items-center gap-2 transition border-t border-slate-800/80 mt-1"
                >
                  <FaTrash /> Delete
                </button>
              </div>
            )}
          </div>
        </div>

        <p className="text-[11px] font-mono text-cyan-400 mb-3 truncate">{stackText}</p>
        <p className="text-xs text-slate-400 line-clamp-2 mb-4 leading-relaxed">{project.description}</p>
      </div>

      {/* Metrics Row */}
      <div>
        <div className="flex items-center justify-between border-t border-slate-800/80 pt-3 mb-4 text-xs font-mono">
          <div>
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Quality</span>
            <span className="font-bold text-emerald-400">{project.quality_score} / 100</span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Tests</span>
            <span className="font-bold text-cyan-400">{project.tests_passed} / {project.tests_total}</span>
          </div>

          <div className="text-right">
            <span className="text-[10px] text-slate-500 uppercase block font-sans">Status</span>
            {getStatusBadge(project.status)}
          </div>
        </div>

        {/* Footer Bar */}
        <div className="flex items-center justify-between text-xs pt-1">
          <span className="text-[10px] font-mono text-slate-500">Updated {project.updated_at}</span>
          <button
            onClick={() => onOpenProject(project)}
            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg transition shadow-md shadow-indigo-600/20"
          >
            Open
          </button>
        </div>
      </div>
    </div>
  );
}
