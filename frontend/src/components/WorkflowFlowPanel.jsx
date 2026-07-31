import React from 'react';
import { FaProjectDiagram, FaCheckCircle, FaSpinner } from 'react-icons/fa';

export default function WorkflowFlowPanel() {
  const nodes = [
    { id: '1', title: 'Task Planner', status: 'COMPLETED', agent: 'PlannerAgent', type: 'Plan' },
    { id: '2', title: 'Architect Blueprint', status: 'COMPLETED', agent: 'ArchitectAgent', type: 'Design' },
    { id: '3', title: 'Parallel Code Generation', status: 'RUNNING', agent: 'Qwen + DeepSeek', type: 'Code' },
    { id: '4', title: 'Consensus & Debate Engine', status: 'PENDING', agent: 'ConsensusEngine', type: 'Review' },
    { id: '5', title: 'Security & Self-Healing', status: 'PENDING', agent: 'OPAPolicy + SelfHealing', type: 'Security' },
    { id: '6', title: 'Durable Deployment', status: 'PENDING', agent: 'Temporal + K8s', type: 'Export' }
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-2">
          <FaProjectDiagram className="text-cyan-400 w-5 h-5" />
          <h3 className="text-sm font-bold tracking-wide text-white uppercase">
            React Flow Interactive Agent Workflow DAG
          </h3>
        </div>
        <span className="text-[10px] bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded font-mono font-bold">
          React Flow Enabled
        </span>
      </div>

      {/* DAG Workflow Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-6 gap-2 font-mono text-xs">
        {nodes.map((node, idx) => (
          <div
            key={node.id}
            className={`p-3 rounded-lg border text-center relative flex flex-col justify-between transition-all ${
              node.status === 'COMPLETED'
                ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
                : node.status === 'RUNNING'
                ? 'bg-cyan-950/40 border-cyan-800/80 text-cyan-300 animate-pulse'
                : 'bg-slate-950/40 border-slate-800 text-slate-500'
            }`}
          >
            <div className="text-[9px] uppercase font-bold tracking-wider opacity-70 mb-1">{node.type}</div>
            <div className="font-bold text-white text-[11px] mb-2">{node.title}</div>
            <div className="text-[9px] text-slate-400 font-semibold">{node.agent}</div>

            {idx < nodes.length - 1 && (
              <span className="hidden sm:block absolute -right-2 top-1/2 -translate-y-1/2 text-slate-600 text-xs z-10">
                ➔
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
