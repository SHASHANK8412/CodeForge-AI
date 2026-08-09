import React from 'react';
import { FaBolt, FaSpinner, FaInfoCircle } from 'react-icons/fa';

export default function GenerateButton({
  projectName,
  setProjectName,
  submitting,
  onSubmit,
  nameError
}) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl backdrop-blur-md font-sans">
      {/* Project Name Field */}
      <div className="mb-6">
        <label className="text-xs font-bold text-white uppercase tracking-wider block mb-2">
          Project Name <span className="text-rose-400">*</span>
        </label>
        <input
          type="text"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="e.g. FoodDelivery AI"
          className={`w-full bg-slate-900 border rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none transition ${
            nameError ? 'border-rose-500' : 'border-slate-800 focus:border-cyan-500'
          }`}
        />
        {nameError && (
          <p className="mt-1 text-xs text-rose-400 flex items-center gap-1">
            <FaInfoCircle className="w-3 h-3" /> Project name cannot be empty.
          </p>
        )}
      </div>

      {/* Main Submit Action */}
      <div className="text-center">
        <button
          type="button"
          onClick={onSubmit}
          disabled={submitting}
          className="w-full sm:w-auto px-10 py-4 text-base font-extrabold text-white bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 disabled:bg-slate-800 rounded-xl shadow-xl shadow-cyan-500/20 border border-cyan-400/30 flex items-center justify-center gap-3 transition-all transform hover:-translate-y-0.5 active:translate-y-0 disabled:transform-none disabled:opacity-50 cursor-pointer mx-auto"
        >
          {submitting ? (
            <>
              <FaSpinner className="w-5 h-5 animate-spin text-white" />
              <span>Starting AIForge...</span>
            </>
          ) : (
            <>
              <FaBolt className="w-5 h-5 text-yellow-300" />
              <span>Generate Project</span>
            </>
          )}
        </button>

        <p className="text-xs text-slate-400 mt-3 font-sans max-w-lg mx-auto leading-relaxed">
          AIForge will use multiple specialized agents to plan, build, review, test and document your project.
        </p>
      </div>
    </div>
  );
}
