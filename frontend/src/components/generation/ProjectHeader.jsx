import React, { useState } from 'react';
import { FaLayerGroup, FaBan, FaCircle, FaCheckCircle, FaExclamationTriangle, FaWrench } from 'react-icons/fa';

export default function ProjectHeader({
  projectName,
  stack,
  generationId,
  status,
  onCancel
}) {
  const [showCancelModal, setShowCancelModal] = useState(false);

  const getStatusBadge = () => {
    switch (status?.toUpperCase()) {
      case 'COMPLETED':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 text-xs font-bold uppercase tracking-wider">
            <FaCheckCircle className="w-3 h-3" /> COMPLETED
          </span>
        );
      case 'REPAIRING':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-full text-amber-400 text-xs font-bold uppercase tracking-wider animate-pulse">
            <FaWrench className="w-3 h-3" /> REPAIRING
          </span>
        );
      case 'FAILED':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-rose-500/10 border border-rose-500/30 rounded-full text-rose-400 text-xs font-bold uppercase tracking-wider">
            <FaExclamationTriangle className="w-3 h-3" /> FAILED
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 border border-slate-700 rounded-full text-slate-400 text-xs font-bold uppercase tracking-wider">
            <FaBan className="w-3 h-3" /> CANCELLED
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 bg-cyan-500/10 border border-cyan-500/30 rounded-full text-cyan-400 text-xs font-bold uppercase tracking-wider animate-pulse">
            <FaCircle className="w-2.5 h-2.5" /> BUILDING
          </span>
        );
    }
  };

  const stackText = stack
    ? `${stack.frontend || 'React'} + ${stack.backend || 'FastAPI'} + ${stack.database || 'PostgreSQL'}`
    : 'React + FastAPI + PostgreSQL';

  return (
    <header className="border-b border-slate-800/80 bg-[#090d16]/90 backdrop-blur-md sticky top-0 z-40 font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Project Info */}
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <FaLayerGroup className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-extrabold text-white tracking-tight">{projectName}</h2>
              {getStatusBadge()}
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
              <span>{stackText}</span>
              <span>•</span>
              <span className="text-cyan-400">ID: {generationId}</span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {status !== 'COMPLETED' && status !== 'CANCELLED' && status !== 'FAILED' && (
            <button
              onClick={() => setShowCancelModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-rose-300 hover:text-white bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/60 rounded-lg transition"
            >
              <FaBan className="w-3 h-3" /> Cancel Generation
            </button>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 max-w-md w-full text-center shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2">Are you sure?</h3>
            <p className="text-xs text-slate-300 mb-6">
              Stopping generation will terminate the current AIForge workflow execution.
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => {
                  setShowCancelModal(false);
                  onCancel();
                }}
                className="px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 rounded-xl shadow-lg transition"
              >
                Cancel Generation
              </button>
              <button
                onClick={() => setShowCancelModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white bg-slate-900 border border-slate-800 rounded-xl transition"
              >
                Continue Building
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
