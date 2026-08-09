import React, { useState } from 'react';
import { FaLayerGroup, FaArrowLeft, FaCode, FaShieldAlt, FaRocket, FaCheckCircle, FaDownload } from 'react-icons/fa';
import { exportQualityReport } from '../../services/quality';

export default function QualityHeader({
  projectName = 'FoodDelivery AI',
  generationId = 'aiforge-demo',
  onNavigate
}) {
  const [showExportMenu, setShowExportMenu] = useState(false);

  const handleExport = (format) => {
    setShowExportMenu(false);
    exportQualityReport(generationId, format);
  };

  return (
    <header className="bg-[#090d16] border-b border-slate-800/80 px-4 sm:px-6 h-16 flex items-center justify-between font-sans shrink-0 sticky top-0 z-40">
      {/* Brand & Project Info */}
      <div className="flex items-center gap-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
          <FaLayerGroup className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-extrabold text-white tracking-tight">{projectName}</h2>
            <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">
              <FaCheckCircle className="w-2.5 h-2.5" /> ANALYSIS COMPLETE
            </span>
          </div>
          <div className="text-[11px] font-mono text-slate-400">ID: {generationId}</div>
        </div>
      </div>

      {/* Center Navigation Links & Export Action */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => onNavigate && onNavigate('build')}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition"
        >
          <FaArrowLeft className="w-3 h-3 text-cyan-400" /> Build
        </button>

        <button
          onClick={() => onNavigate && onNavigate('code')}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition"
        >
          <FaCode className="w-3 h-3 text-emerald-400" /> Code Workspace
        </button>

        <button
          onClick={() => onNavigate && onNavigate('metrics')}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-indigo-600/20"
        >
          <FaShieldAlt className="w-3 h-3" /> Quality Center
        </button>

        <button
          onClick={() => onNavigate && onNavigate('plugins')}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition"
        >
          <FaRocket className="w-3 h-3 text-purple-400" /> Deploy →
        </button>

        {/* Export Dropdown Menu */}
        <div className="relative ml-2">
          <button
            onClick={() => setShowExportMenu(!showExportMenu)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-bold transition shadow-md shadow-cyan-600/20"
          >
            <FaDownload className="w-3 h-3" /> Export Report
          </button>

          {showExportMenu && (
            <div className="absolute right-0 mt-2 w-40 bg-slate-950 border border-slate-800 rounded-xl p-1.5 shadow-2xl z-50 text-xs font-sans">
              <button
                onClick={() => handleExport('pdf')}
                className="w-full text-left px-3 py-2 hover:bg-slate-900 rounded-lg text-slate-200 transition"
              >
                Export as PDF
              </button>
              <button
                onClick={() => handleExport('json')}
                className="w-full text-left px-3 py-2 hover:bg-slate-900 rounded-lg text-slate-200 transition"
              >
                Export as JSON
              </button>
              <button
                onClick={() => handleExport('markdown')}
                className="w-full text-left px-3 py-2 hover:bg-slate-900 rounded-lg text-slate-200 transition"
              >
                Export as Markdown
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
