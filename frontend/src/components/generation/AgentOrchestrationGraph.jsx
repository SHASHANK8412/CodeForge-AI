import React, { useState } from 'react';
import {
  FaPlay,
  FaCheckCircle,
  FaHourglassHalf,
  FaExclamationTriangle,
  FaTimesCircle,
  FaClock,
  FaRobot,
  FaCode,
  FaDatabase,
  FaShieldAlt,
  FaVial,
  FaBook,
  FaWrench,
  FaUserCheck,
  FaRedo
} from 'react-icons/fa';

const NODES = [
  { id: 'planner', label: 'Planner Agent', icon: FaRobot, x: 260, y: 30, type: 'agent', role: 'Deconstructs prompts into executable specs' },
  { id: 'architect', label: 'Architect Agent', icon: FaCode, x: 260, y: 110, type: 'agent', role: 'Defines schemas, contracts & models' },
  { id: 'hitl_arch', label: 'Human Architecture Approval', icon: FaUserCheck, x: 260, y: 190, type: 'checkpoint', role: 'User review & gatekeeping' },
  { id: 'frontend', label: 'Frontend Agent', icon: FaCode, x: 80, y: 280, type: 'parallel', role: 'React + Vite UI components' },
  { id: 'backend', label: 'Backend Agent', icon: FaCode, x: 260, y: 280, type: 'parallel', role: 'FastAPI routes & business logic' },
  { id: 'database', label: 'Database Agent', icon: FaDatabase, x: 440, y: 280, type: 'parallel', role: 'PostgreSQL schemas & migrations' },
  { id: 'reviewer', label: 'Reviewer Agent', icon: FaShieldAlt, x: 260, y: 370, type: 'agent', role: 'Validates code quality & security' },
  { id: 'testing', label: 'Testing Agent', icon: FaVial, x: 260, y: 450, type: 'agent', role: 'Executes automated test suites' },
  { id: 'document', label: 'Documentation Agent', icon: FaBook, x: 100, y: 550, type: 'success', role: 'Generates API docs & README' },
  { id: 'debug_loop', label: 'Debug → Fix → Retest Loop', icon: FaWrench, x: 420, y: 550, type: 'loop', role: 'Targeted root cause diagnosis & repair' },
];

export default function AgentOrchestrationGraph({
  generationStatus = null,
  activeAgentName = null,
  onSelectNode = null
}) {
  const [selectedNode, setSelectedNode] = useState(null);

  const getNodeStatus = (nodeId) => {
    if (!generationStatus?.agents) return 'waiting';
    const agent = generationStatus.agents.find((a) => a.name === nodeId);
    if (!agent) return 'completed';
    return (agent.status || 'waiting').toLowerCase();
  };

  const getNodeBadge = (status) => {
    if (status === 'running') {
      return (
        <span className="flex items-center gap-1 text-[9px] font-mono font-bold text-cyan-400 bg-cyan-500/20 px-1.5 py-0.5 rounded border border-cyan-500/40 animate-pulse">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
          RUNNING
        </span>
      );
    }
    if (status === 'completed' || status === 'success') {
      return (
        <span className="flex items-center gap-1 text-[9px] font-mono font-bold text-emerald-400 bg-emerald-500/20 px-1.5 py-0.5 rounded border border-emerald-500/30">
          <FaCheckCircle className="w-2 h-2" />
          PASSED
        </span>
      );
    }
    if (status === 'failed') {
      return (
        <span className="flex items-center gap-1 text-[9px] font-mono font-bold text-rose-400 bg-rose-500/20 px-1.5 py-0.5 rounded border border-rose-500/30">
          <FaTimesCircle className="w-2 h-2" />
          FAILED
        </span>
      );
    }
    return (
      <span className="text-[9px] font-mono font-semibold text-slate-500 bg-slate-900 px-1.5 py-0.5 rounded">
        WAITING
      </span>
    );
  };

  return (
    <div className="bg-[#090d16] border border-slate-800/90 rounded-2xl p-4 font-sans select-none relative overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <FaRobot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-white">LangGraph Autonomous Multi-Agent Workflow</h3>
            <p className="text-[11px] text-slate-400">Real-time state graph with checkpointing, parallel execution & repair loops</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="flex items-center gap-1 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Done</span>
          <span className="flex items-center gap-1 text-cyan-400"><span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" /> Active</span>
          <span className="flex items-center gap-1 text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-400" /> Loop</span>
        </div>
      </div>

      {/* Visual Workflow Graph */}
      <div className="relative w-full h-[630px] bg-[#060911] border border-slate-800/60 rounded-xl p-4 overflow-x-auto custom-scrollbar flex items-center justify-center">
        <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-slate-700/60 stroke-[1.5] fill-none">
          {/* Planner -> Architect */}
          <path d="M 330 75 L 330 110" markerEnd="url(#arrow)" />
          {/* Architect -> Human Approval */}
          <path d="M 330 155 L 330 190" markerEnd="url(#arrow)" />
          {/* Human Approval -> Parallel Agents */}
          <path d="M 330 235 L 150 280" markerEnd="url(#arrow)" />
          <path d="M 330 235 L 330 280" markerEnd="url(#arrow)" />
          <path d="M 330 235 L 510 280" markerEnd="url(#arrow)" />
          {/* Parallel Agents -> Reviewer */}
          <path d="M 150 325 L 330 370" markerEnd="url(#arrow)" />
          <path d="M 330 325 L 330 370" markerEnd="url(#arrow)" />
          <path d="M 510 325 L 330 370" markerEnd="url(#arrow)" />
          {/* Reviewer -> Testing */}
          <path d="M 330 415 L 330 450" markerEnd="url(#arrow)" />
          {/* Testing -> Documentation (Pass) & Debug Loop (Fail) */}
          <path d="M 310 495 L 170 550" markerEnd="url(#arrow)" />
          <path d="M 350 495 L 490 550" markerEnd="url(#arrow)" />
          {/* Debug Loop -> Testing (Retest) */}
          <path d="M 530 550 C 580 500, 560 460, 400 465" strokeDasharray="4" stroke="#f59e0b" markerEnd="url(#arrow-loop)" />

          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
            </marker>
            <marker id="arrow-loop" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
            </marker>
          </defs>
        </svg>

        {/* Interactive Node Cards */}
        {NODES.map((node) => {
          const Icon = node.icon;
          const status = getNodeStatus(node.id);
          const isSelected = selectedNode?.id === node.id;

          return (
            <div
              key={node.id}
              onClick={() => {
                setSelectedNode(node);
                onSelectNode?.(node);
              }}
              style={{ left: `${node.x}px`, top: `${node.y}px` }}
              className={`absolute w-36 sm:w-40 p-2.5 rounded-xl border transition-all duration-200 cursor-pointer shadow-lg z-10 ${
                isSelected
                  ? 'bg-indigo-600/25 border-cyan-400 ring-2 ring-cyan-500/30'
                  : status === 'running'
                  ? 'bg-slate-900/90 border-cyan-500/60 shadow-cyan-500/10'
                  : 'bg-slate-950/90 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="p-1 rounded bg-slate-900 text-cyan-400">
                  <Icon className="w-3 h-3" />
                </div>
                {getNodeBadge(status)}
              </div>
              <div className="font-bold text-[11px] text-white truncate">{node.label}</div>
              <div className="text-[9px] text-slate-400 truncate mt-0.5">{node.role}</div>
            </div>
          );
        })}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="mt-3 p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs flex items-center justify-between animate-fade-in">
          <div>
            <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-wider">Agent Node Selected:</span>
            <div className="text-sm font-bold text-white mt-0.5">{selectedNode.label}</div>
            <div className="text-[11px] text-slate-400 mt-0.5">{selectedNode.role}</div>
          </div>
          <button
            onClick={() => setSelectedNode(null)}
            className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded text-[11px] cursor-pointer"
          >
            Close Details
          </button>
        </div>
      )}
    </div>
  );
}
