import React from 'react';
import { FaCheckCircle, FaDownload, FaCode, FaShieldAlt, FaRocket } from 'react-icons/fa';

export default function CompletionActions({
  generationId,
  qualityScore = 96.0,
  testsPassed = 48,
  totalTests = 48,
  onOpenWorkspace,
  onViewQualityReport
}) {
  const handleDownloadZip = () => {
    window.location.href = `http://127.0.0.1:8000/export/zip/${generationId}`;
  };

  return (
    <div className="bg-gradient-to-tr from-slate-950 via-indigo-950/40 to-slate-950 border border-emerald-500/30 rounded-2xl p-6 shadow-2xl font-sans mb-6">
      <div className="flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center text-2xl shrink-0">
            <FaCheckCircle />
          </div>
          <div>
            <h3 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
              🎉 Project Generation Complete
            </h3>
            <p className="text-xs text-slate-300 mt-1">
              Your project has been successfully generated, reviewed, and tested.
            </p>
          </div>
        </div>

        {/* Metrics Pill Cards */}
        <div className="flex items-center gap-4">
          <div className="bg-slate-900/90 border border-slate-800 p-3 rounded-xl text-center min-w-[110px]">
            <div className="text-[11px] text-slate-400 font-medium">Quality Score</div>
            <div className="text-lg font-black text-emerald-400 font-mono">{qualityScore} <span className="text-xs text-slate-500 font-normal">/ 100</span></div>
          </div>

          <div className="bg-slate-900/90 border border-slate-800 p-3 rounded-xl text-center min-w-[110px]">
            <div className="text-[11px] text-slate-400 font-medium">Tests</div>
            <div className="text-lg font-black text-cyan-400 font-mono">{testsPassed} / {totalTests} <span className="text-xs text-emerald-400">Passed</span></div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-6 pt-5 border-t border-slate-800/80">
        <button
          onClick={onOpenWorkspace}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-cyan-500/20"
        >
          <FaCode className="w-4 h-4" /> Open Code Workspace
        </button>

        <button
          onClick={handleDownloadZip}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-bold transition"
        >
          <FaDownload className="w-4 h-4 text-emerald-400" /> Download ZIP
        </button>

        <button
          onClick={onViewQualityReport}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-bold transition"
        >
          <FaShieldAlt className="w-4 h-4 text-amber-400" /> Quality Report
        </button>

        <button
          onClick={onOpenWorkspace}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-bold transition"
        >
          <FaRocket className="w-4 h-4 text-purple-400" /> Deployment
        </button>
      </div>
    </div>
  );
}
