import React from 'react';
import { FaPlus, FaLayerGroup } from 'react-icons/fa';

export default function EmptyProjects({ onNewProject }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-12 shadow-xl text-center font-sans max-w-lg mx-auto">
      <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center text-2xl mx-auto mb-4">
        <FaLayerGroup />
      </div>

      <h3 className="text-lg font-bold text-white mb-2">You haven't created a project yet</h3>
      <p className="text-xs text-slate-400 mb-6 leading-relaxed">
        Turn your idea into a complete software project with AIForge's autonomous multi-agent engineering workflow.
      </p>

      <button
        onClick={onNewProject}
        className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-extrabold transition shadow-lg shadow-cyan-500/20 inline-flex items-center gap-2"
      >
        <FaPlus /> Create Your First Project
      </button>
    </div>
  );
}
