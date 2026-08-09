import React from 'react';
import { FaCheckCircle, FaSpinner, FaClock, FaTimesCircle, FaArrowDown, FaWrench } from 'react-icons/fa';

export default function AgentPipeline({ agentsMap = {} }) {
  const getAgentState = (name) => {
    const info = agentsMap[name.toLowerCase()] || {};
    return {
      status: info.status || 'waiting',
      summary: info.summary || '',
      timestamp: info.timestamp || ''
    };
  };

  const renderStatusBadge = (state) => {
    switch (state.status?.toLowerCase()) {
      case 'completed':
        return (
          <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1">
            <FaCheckCircle className="w-3 h-3 text-emerald-400" /> Completed
          </span>
        );
      case 'running':
        return (
          <span className="text-cyan-400 font-mono text-[11px] flex items-center gap-1">
            <FaSpinner className="w-3 h-3 animate-spin text-cyan-400" /> Running
          </span>
        );
      case 'failed':
        return (
          <span className="text-rose-400 font-mono text-[11px] flex items-center gap-1">
            <FaTimesCircle className="w-3 h-3 text-rose-400" /> Failed
          </span>
        );
      case 'repairing':
        return (
          <span className="text-amber-400 font-mono text-[11px] flex items-center gap-1">
            <FaWrench className="w-3 h-3 animate-bounce text-amber-400" /> Repairing
          </span>
        );
      default:
        return (
          <span className="text-slate-500 font-mono text-[11px] flex items-center gap-1">
            <FaClock className="w-3 h-3 text-slate-600" /> Waiting
          </span>
        );
    }
  };

  const renderAgentBox = (name, title) => {
    const st = getAgentState(name);
    const isRunning = st.status?.toLowerCase() === 'running';
    const isCompleted = st.status?.toLowerCase() === 'completed';

    return (
      <div
        className={`p-3.5 rounded-xl border transition-all text-xs font-sans shadow-md ${
          isRunning
            ? 'bg-indigo-950/60 border-cyan-400/50 shadow-cyan-500/10'
            : isCompleted
            ? 'bg-slate-900 border-slate-800'
            : 'bg-slate-950/60 border-slate-800/80 opacity-60'
        }`}
      >
        <div className="flex items-center justify-between mb-1">
          <span className="font-bold text-white text-xs">{title}</span>
          {renderStatusBadge(st)}
        </div>
        {st.summary ? (
          <p className="text-[11px] text-slate-400 line-clamp-1">{st.summary}</p>
        ) : (
          <p className="text-[11px] text-slate-600 italic">Waiting in pipeline queue...</p>
        )}
      </div>
    );
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 shadow-xl font-sans">
      <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">
        Multi-Agent Workflow Pipeline
      </h3>

      <div className="space-y-3">
        {/* Step 1: Planner */}
        {renderAgentBox('planner', 'Planner Agent')}

        <div className="flex justify-center text-slate-600">
          <FaArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 2: Architect */}
        {renderAgentBox('architect', 'Architect Agent')}

        <div className="flex justify-center text-slate-600">
          <FaArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 3: Parallel Coders (Frontend, Backend, Database) */}
        <div className="p-3.5 bg-slate-900/40 border border-indigo-500/20 rounded-2xl">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400 mb-2.5 text-center">
            ⚡ Parallel Autonomous Coders
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {renderAgentBox('frontend', 'Frontend Agent')}
            {renderAgentBox('backend', 'Backend Agent')}
            {renderAgentBox('database', 'Database Agent')}
          </div>
        </div>

        <div className="flex justify-center text-slate-600">
          <FaArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 4: Reviewer */}
        {renderAgentBox('reviewer', 'Reviewer Agent')}

        <div className="flex justify-center text-slate-600">
          <FaArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 5: Testing */}
        {renderAgentBox('testing', 'Testing Agent')}

        <div className="flex justify-center text-slate-600">
          <FaArrowDown className="w-3.5 h-3.5" />
        </div>

        {/* Step 6: Documentation */}
        {renderAgentBox('documentation', 'Documentation Agent')}
      </div>
    </div>
  );
}
