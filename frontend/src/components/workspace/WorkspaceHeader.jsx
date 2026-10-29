import { BACKEND_URL } from '../../config/backend';
import React from 'react';
import {
  FaLayerGroup,
  FaArrowLeft,
  FaPlay,
  FaCheckCircle,
  FaSearch,
  FaDownload,
  FaRocket,
  FaShieldAlt,
  FaClipboardList,
  FaHeartbeat,
  FaSave,
  FaKeyboard,
  FaBrain,
  FaBug
} from 'react-icons/fa';

export default function WorkspaceHeader({
  projectName = 'AIForge Project',
  generationId = 'aiforge-demo',
  status = 'READY',
  hasUnsavedChanges = false,
  onBackToGeneration,
  onRun,
  onPreview,
  onSpec,
  onHealth,
  onTest,
  onReview,
  onQualityReport,
  onDeploy,
  onDownload,
  onOpenCommandPalette,
  onOpenMemory,
  onAutoRepair
}) {
  const handleDownloadZip = () => {
    window.location.href = `${BACKEND_URL}/api/export/zip/${encodeURIComponent(generationId)}`;
  };

  const getStatusBadge = () => {
    const s = (status || 'READY').toUpperCase();
    if (s.includes('RUNNING') || s.includes('GENERATING')) {
      return (
        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
          Running
        </span>
      );
    }
    if (s.includes('APPROVAL') || s.includes('WAITING')) {
      return (
        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 animate-pulse">
          ● Approval Required
        </span>
      );
    }
    if (s.includes('TESTING')) {
      return (
        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
          ● Testing
        </span>
      );
    }
    if (s.includes('DEBUG')) {
      return (
        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
          ● Debugging
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
        <FaCheckCircle className="w-2.5 h-2.5" />
        Ready
      </span>
    );
  };

  return (
    <header className="bg-[#090d16] border-b border-slate-800/80 px-3 h-14 flex items-center justify-between font-sans shrink-0 select-none overflow-x-auto custom-scrollbar">
      {/* Left: Brand & Navigation */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={onBackToGeneration}
          className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-md transition cursor-pointer"
        >
          <FaArrowLeft className="w-2.5 h-2.5" /> <span className="hidden sm:inline">Back</span>
        </button>

        <div className="flex items-center gap-2 border-l border-slate-800 pl-2.5">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-sm shrink-0">
            <FaLayerGroup className="w-3 h-3" />
          </div>
          <div className="flex flex-col">
            <span className="text-xs sm:text-sm font-extrabold text-white truncate max-w-[150px] sm:max-w-[220px]">
              {projectName}
            </span>
          </div>
          {getStatusBadge()}
          {hasUnsavedChanges ? (
            <span className="hidden lg:flex items-center gap-1 text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              ● Unsaved Changes
            </span>
          ) : (
            <span className="hidden lg:flex items-center gap-1 text-[10px] font-mono text-slate-500 bg-slate-900/50 px-2 py-0.5 rounded">
              Saved
            </span>
          )}
        </div>
      </div>

      {/* Middle & Right Action Controls */}
      <div className="flex items-center gap-1.5 shrink-0">
        {/* Command Palette Button */}
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white rounded-md text-[11px] font-mono transition cursor-pointer"
          title="Command Palette (Ctrl/Cmd + K)"
        >
          <FaKeyboard className="w-3 h-3 text-cyan-400" />
          <span className="hidden md:inline font-semibold">⌘K</span>
        </button>

        {/* Project Memory */}
        <button
          onClick={onOpenMemory}
          className="flex items-center gap-1 px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-violet-300 hover:text-white rounded-md text-[11px] font-bold transition font-mono cursor-pointer"
          title="Inspect Project Memory & Codebase Intelligence"
        >
          <FaBrain className="w-3 h-3 text-violet-400" />
          <span className="hidden lg:inline">Memory</span>
        </button>

        {/* Live Preview / Run */}
        <button
          onClick={onPreview || onRun}
          className="flex items-center gap-1 px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded-md text-[11px] font-bold transition shadow-sm font-mono cursor-pointer"
        >
          <FaPlay className="w-2.5 h-2.5" /> Live Preview
        </button>

        {/* Test */}
        <button
          onClick={onTest}
          className="flex items-center gap-1 px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-[11px] font-bold transition shadow-sm cursor-pointer"
        >
          <FaCheckCircle className="w-2.5 h-2.5" /> Test
        </button>

        {/* Auto Repair */}
        <button
          onClick={onAutoRepair}
          className="flex items-center gap-1 px-2 py-1 bg-slate-900 hover:bg-slate-800 text-amber-300 hover:text-white border border-slate-800 rounded-md text-[11px] font-semibold transition cursor-pointer"
          title="Autonomous Debug & Repair Loop"
        >
          <FaBug className="w-2.5 h-2.5 text-amber-400" /> <span className="hidden xl:inline">Auto Fix</span>
        </button>

        {/* Review */}
        <button
          onClick={onReview}
          className="flex items-center gap-1 px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 rounded-md text-[11px] font-semibold transition cursor-pointer"
        >
          <FaSearch className="w-2.5 h-2.5 text-cyan-400" /> <span className="hidden sm:inline">Review</span>
        </button>

        {/* Download ZIP */}
        <button
          onClick={onDownload || handleDownloadZip}
          className="flex items-center gap-1 px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-cyan-300 hover:text-white rounded-md text-[11px] font-bold transition cursor-pointer"
        >
          <FaDownload className="w-2.5 h-2.5 text-cyan-400" /> <span className="hidden sm:inline">Export ZIP</span>
        </button>
      </div>
    </header>
  );
}
