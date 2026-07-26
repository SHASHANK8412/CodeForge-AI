import React, { useState } from 'react';
import { FaBrain, FaCheckCircle, FaClock, FaDatabase, FaFileCode, FaHistory, FaProjectDiagram } from 'react-icons/fa';

export default function MemoryPanel({ sessionMemory, currentStep }) {
  const [activeTab, setActiveTab] = useState('agents');

  if (!sessionMemory) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-400 text-xs text-center">
        No active memory context initialized. Start project generation to populate context store.
      </div>
    );
  }

  const {
    session_id = 'default',
    project_name = 'AIForge Application',
    context = {},
    generated_files = {},
    history = [],
    shared_stack = {}
  } = sessionMemory;

  const AGENT_LIST = [
    { key: 'planner', label: 'Planner Agent' },
    { key: 'architect', label: 'Architect Agent' },
    { key: 'frontend', label: 'Frontend Agent' },
    { key: 'backend', label: 'Backend Agent' },
    { key: 'database', label: 'Database Agent' },
    { key: 'reviewer', label: 'Reviewer Agent' },
    { key: 'testing', label: 'Testing Agent' },
    { key: 'documentation', label: 'Documentation Agent' }
  ];

  const fileKeys = Object.keys(generated_files);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <FaBrain className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold tracking-wide text-white uppercase">
            Multi-Agent Shared Memory & Context Store
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="bg-slate-800 text-indigo-300 px-2.5 py-1 rounded border border-slate-700">
            Project: <strong className="text-white">{project_name}</strong>
          </span>
          <span className="bg-indigo-950 text-emerald-300 px-2.5 py-1 rounded border border-indigo-800">
            Step: <strong className="text-emerald-400">{currentStep || 'active'}</strong>
          </span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab('agents')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
            activeTab === 'agents' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          <FaCheckCircle className="w-3.5 h-3.5" /> Agent Status
        </button>
        <button
          onClick={() => setActiveTab('context')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
            activeTab === 'context' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          <FaDatabase className="w-3.5 h-3.5" /> Shared Context
        </button>
        <button
          onClick={() => setActiveTab('files')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
            activeTab === 'files' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          <FaFileCode className="w-3.5 h-3.5" /> Generated Files ({fileKeys.length})
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer ${
            activeTab === 'history' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          <FaHistory className="w-3.5 h-3.5" /> Execution History
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === 'agents' && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {AGENT_LIST.map((agent) => {
            const hasData = context[agent.key] && (
              typeof context[agent.key] === 'string' ? context[agent.key].length > 0 : Object.keys(context[agent.key]).length > 0
            );
            return (
              <div
                key={agent.key}
                className={`p-3 rounded-lg border flex items-center justify-between text-xs transition-all ${
                  hasData
                    ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                    : 'bg-slate-950/40 border-slate-800 text-slate-500'
                }`}
              >
                <span className="font-medium truncate">{agent.label}</span>
                {hasData ? (
                  <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                    <FaCheckCircle className="w-3 h-3" /> Done
                  </span>
                ) : (
                  <span className="text-slate-600 text-[10px] italic">Pending</span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'context' && (
        <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3 font-mono text-xs text-slate-300">
          <div className="text-indigo-400 font-semibold text-xs mb-2">Propagated Stack Parameters:</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
            <div className="bg-slate-900 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px] block">AUTH</span>
              <span className="text-emerald-400 font-bold">{shared_stack.authentication || 'JWT'}</span>
            </div>
            <div className="bg-slate-900 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px] block">FRONTEND</span>
              <span className="text-indigo-400 font-bold">{shared_stack.frontend || 'React'}</span>
            </div>
            <div className="bg-slate-900 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px] block">BACKEND</span>
              <span className="text-purple-400 font-bold">{shared_stack.backend || 'FastAPI'}</span>
            </div>
            <div className="bg-slate-900 p-2 rounded border border-slate-800">
              <span className="text-slate-500 text-[10px] block">DATABASE</span>
              <span className="text-amber-400 font-bold">{shared_stack.database || 'PostgreSQL'}</span>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'files' && (
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 max-h-48 overflow-y-auto font-mono text-xs">
          {fileKeys.length === 0 ? (
            <span className="text-slate-500 italic">No files registered in memory.</span>
          ) : (
            <div className="space-y-1">
              {fileKeys.map((fname) => (
                <div key={fname} className="text-indigo-300 flex items-center gap-2 py-0.5">
                  <FaFileCode className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{fname}</span>
                  <span className="text-[10px] text-emerald-400 ml-auto bg-emerald-950 px-1.5 rounded">Cached in Memory</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 max-h-48 overflow-y-auto font-mono text-xs space-y-2">
          {history.length === 0 ? (
            <span className="text-slate-500 italic">No execution history logged.</span>
          ) : (
            history.map((h, idx) => (
              <div key={idx} className="p-2 rounded bg-slate-900 border border-slate-800 flex items-start justify-between">
                <div>
                  <span className="text-indigo-400 font-bold">{h.agent}</span>: <span className="text-slate-300">{h.user_prompt}</span>
                </div>
                <span className="text-[10px] text-slate-500 flex items-center gap-1">
                  <FaClock className="w-2.5 h-2.5" /> {h.execution_time?.toFixed(2)}s
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
