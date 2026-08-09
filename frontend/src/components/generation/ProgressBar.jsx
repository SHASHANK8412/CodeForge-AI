import React from 'react';

export default function ProgressBar({ completedCount = 6, totalCount = 8, progress = 78 }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 shadow-xl font-sans">
      <div className="flex justify-between items-center text-xs mb-2">
        <span className="font-bold text-white uppercase tracking-wider">AIForge Pipeline Progress</span>
        <span className="font-mono text-cyan-400 font-bold">{completedCount} / {totalCount} agents completed ({progress}%)</span>
      </div>

      <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden border border-slate-800">
        <div
          className="bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500 h-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
