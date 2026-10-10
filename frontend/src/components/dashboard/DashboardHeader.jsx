import React, { useState } from 'react';
import { FaPlus, FaBell, FaUserCircle, FaCog, FaKey, FaSignOutAlt } from 'react-icons/fa';

export default function DashboardHeader({ onNewProject, onNotify }) {
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6 font-sans">
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
          Good afternoon 👋
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Welcome back to AIForge. Describe an idea or manage your autonomous software projects.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => onNotify && onNotify('No new system notifications', 'info')}
          className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white rounded-xl transition relative"
        >
          <FaBell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-cyan-400 rounded-full" />
        </button>

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 px-3 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition"
          >
            <FaUserCircle className="w-4 h-4 text-cyan-400" />
            <span>Developer</span>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-slate-950 border border-slate-800 rounded-xl p-1.5 shadow-2xl z-50 text-xs font-sans">
              <div className="px-3 py-2 border-b border-slate-800 text-slate-400">
                Signed in as <strong className="text-white block font-mono">dev@aiforge.io</strong>
              </div>
              <button className="w-full text-left px-3 py-2 hover:bg-slate-900 rounded-lg text-slate-200 flex items-center gap-2 transition">
                <FaUserCircle className="text-slate-400" /> Profile
              </button>
              <button className="w-full text-left px-3 py-2 hover:bg-slate-900 rounded-lg text-slate-200 flex items-center gap-2 transition">
                <FaCog className="text-slate-400" /> Settings
              </button>
              <button className="w-full text-left px-3 py-2 hover:bg-slate-900 rounded-lg text-slate-200 flex items-center gap-2 transition">
                <FaKey className="text-slate-400" /> API Keys
              </button>
              <button className="w-full text-left px-3 py-2 hover:bg-slate-900 rounded-lg text-rose-400 flex items-center gap-2 transition border-t border-slate-800 mt-1">
                <FaSignOutAlt /> Logout
              </button>
            </div>
          )}
        </div>

        <button
          onClick={onNewProject}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20"
        >
          <FaPlus className="w-3 h-3" /> New Project
        </button>
      </div>
    </div>
  );
}
