import React, { useState } from 'react';
import {
  FaCheckCircle,
  FaHourglassHalf,
  FaClock,
  FaTimesCircle,
  FaRobot,
  FaPlay,
  FaVial,
  FaFileCode,
  FaShieldAlt,
  FaLayerGroup,
  FaInfoCircle
} from 'react-icons/fa';

export default function AIMissionProgress({
  mission = null,
  elapsedSeconds = 18.4,
  currentTask = 'Testing authentication endpoints...',
  activeAgent = 'Testing Agent',
  affectedFiles = ['backend/routes/auth.py', 'tests/test_auth.py'],
  onViewDetails = null
}) {
  const [showModal, setShowModal] = useState(false);

  const defaultSteps = [
    { name: 'Analyze Requirements & User Prompt', status: 'COMPLETED', agent: 'Planner' },
    { name: 'Design Architecture & API Contracts', status: 'COMPLETED', agent: 'Architect' },
    { name: 'Human Architecture Approval', status: 'COMPLETED', agent: 'Human-in-the-Loop' },
    { name: 'Implement Backend APIs & Services', status: 'COMPLETED', agent: 'Backend' },
    { name: 'Implement Frontend React Components', status: 'COMPLETED', agent: 'Frontend' },
    { name: 'Database Schemas & Migrations', status: 'COMPLETED', agent: 'Database' },
    { name: 'Code Quality & Security Review', status: 'COMPLETED', agent: 'Reviewer' },
    { name: 'Automated Test Suite Execution', status: 'RUNNING', agent: 'Testing' },
    { name: 'Autonomous Debug & Fix Loop', status: 'PENDING', agent: 'Debug Agent' },
    { name: 'Documentation & Assembly Packaging', status: 'PENDING', agent: 'Documentation' }
  ];

  const steps = mission?.steps || defaultSteps;
  const completedCount = steps.filter((s) => s.status === 'COMPLETED').length;
  const totalCount = steps.length;
  const progressPct = Math.round((completedCount / totalCount) * 100);

  return (
    <div className="bg-[#090d16] border border-slate-800/90 rounded-2xl p-5 font-sans select-none shadow-2xl space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <FaRobot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-extrabold text-white">
                {mission?.title || 'Building Your Autonomous Application'}
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
                ● ACTIVE MISSION
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {completedCount} of {totalCount} engineering phases verified
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowModal(true)}
            className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-cyan-300 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer"
          >
            <FaInfoCircle className="w-3 h-3" /> Mission Details
          </button>
        </div>
      </div>

      {/* Real Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs font-mono">
          <span className="text-slate-400">Mission Progress</span>
          <span className="text-cyan-400 font-bold">{progressPct}% Complete</span>
        </div>
        <div className="w-full bg-slate-950 rounded-full h-2.5 border border-slate-800 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-500 via-indigo-500 to-emerald-400 transition-all duration-500 rounded-full"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* "Currently Working On" Card */}
      <div className="p-4 rounded-xl bg-[#060911] border border-cyan-500/30 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider">
              {activeAgent} Working
            </span>
          </div>
          <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
            <FaClock className="w-3 h-3 text-cyan-400" /> Elapsed: {elapsedSeconds}s
          </span>
        </div>

        <div className="text-xs font-bold text-white pl-4">
          {currentTask}
        </div>

        {affectedFiles.length > 0 && (
          <div className="pt-2 border-t border-slate-800/80 flex items-center gap-2 flex-wrap text-[11px] font-mono text-slate-400">
            <span className="text-[10px] uppercase font-bold text-slate-500">Target Files:</span>
            {affectedFiles.map((f, idx) => (
              <span key={idx} className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-800 flex items-center gap-1">
                <FaFileCode className="text-cyan-400 w-2.5 h-2.5" />
                {f}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Mission Execution Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2 pt-2">
        {steps.map((st, idx) => {
          const isDone = st.status === 'COMPLETED';
          const isRunning = st.status === 'RUNNING';

          return (
            <div
              key={idx}
              className={`p-2.5 rounded-xl border text-xs transition ${
                isRunning
                  ? 'bg-cyan-950/25 border-cyan-400 shadow-sm shadow-cyan-500/20'
                  : isDone
                  ? 'bg-slate-950/80 border-slate-800/80 text-slate-300'
                  : 'bg-slate-950/40 border-slate-900 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                {isDone ? (
                  <FaCheckCircle className="w-3 h-3 text-emerald-400" />
                ) : isRunning ? (
                  <FaHourglassHalf className="w-3 h-3 text-cyan-400 animate-spin" />
                ) : (
                  <FaClock className="w-3 h-3 text-slate-600" />
                )}
                <span className="text-[9px] font-mono text-slate-400 font-bold">{st.agent}</span>
              </div>
              <div className="font-semibold text-[11px] truncate text-slate-200 mt-1">{st.name}</div>
            </div>
          );
        })}
      </div>

      {/* Detailed Mission Execution Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4 font-sans">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white">{mission?.title || 'Autonomous Engineering Mission'}</h3>
                <p className="text-xs text-slate-400">Step-by-step lifecycle and chronological timeline</p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 max-h-80 overflow-y-auto custom-scrollbar">
              {steps.map((s, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs">
                  <div className="flex items-center gap-2.5">
                    {s.status === 'COMPLETED' ? (
                      <FaCheckCircle className="text-emerald-400 w-3.5 h-3.5" />
                    ) : s.status === 'RUNNING' ? (
                      <FaHourglassHalf className="text-cyan-400 w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <FaClock className="text-slate-600 w-3.5 h-3.5" />
                    )}
                    <span className="text-slate-200 font-medium">{s.name}</span>
                  </div>
                  <span className="text-[10px] font-mono text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    {s.agent}
                  </span>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
