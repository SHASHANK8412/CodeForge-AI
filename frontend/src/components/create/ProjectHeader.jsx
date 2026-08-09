import React from 'react';
import { FaLayerGroup, FaArrowLeft } from 'react-icons/fa';

export default function ProjectHeader({ onBack }) {
  return (
    <header className="border-b border-slate-800/80 bg-[#090d16]/80 backdrop-blur-md sticky top-0 z-40 font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 text-slate-400 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg transition"
            title="Back to Landing Page"
          >
            <FaArrowLeft className="w-3.5 h-3.5" />
          </button>
          <div className="flex items-center gap-2 cursor-pointer" onClick={onBack}>
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
              <FaLayerGroup className="w-4 h-4" />
            </div>
            <span className="text-lg font-extrabold text-white">AIForge</span>
          </div>
        </div>

        <div className="flex items-center gap-6 text-xs font-semibold text-slate-300">
          <button onClick={onBack} className="hover:text-cyan-400 transition">Dashboard</button>
          <button onClick={onBack} className="hover:text-cyan-400 transition">Projects</button>
          <a href="https://github.com/SHASHANK8412/CodeForge-AI" target="_blank" rel="noreferrer" className="hover:text-cyan-400 transition">Docs</a>
        </div>
      </div>
    </header>
  );
}
