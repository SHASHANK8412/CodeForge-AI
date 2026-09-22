import React, { useState } from 'react';
import {
  FaCheckCircle,
  FaTimesCircle,
  FaRobot,
  FaCode,
  FaDatabase,
  FaShieldAlt,
  FaVial,
  FaBook,
  FaWrench,
  FaUserCheck,
  FaSearch,
  FaHammer,
  FaBoxes,
  FaTachometerAlt,
  FaTerminal,
  FaCubes,
  FaBoxOpen,
  FaCloudUploadAlt,
} from 'react-icons/fa';

// Node ids match the backend LangGraph node names 1:1 (see backend/graph/parallel_workflow.py
// and the AGENT_ORDER list in GenerationDashboard.jsx) so live status lookups need no mapping.
// 'hitl_arch' is a UI-only checkpoint (the graph pauses here for human approval, it isn't a
// tracked agent) and 'debug_loop' represents the combined debug+patch self-healing pair.
const NODES = [
  { id: 'planner', label: 'Planner Agent', icon: FaRobot, x: 375, y: 30, role: 'Deconstructs the prompt into executable specs' },
  { id: 'architect', label: 'Architect Agent', icon: FaCode, x: 375, y: 110, role: 'Defines schemas, contracts & data models' },
  { id: 'hitl_arch', label: 'Human Architecture Approval', icon: FaUserCheck, x: 375, y: 190, type: 'checkpoint', role: 'User reviews & gates the architecture' },

  { id: 'frontend', label: 'Frontend Agent', icon: FaCode, x: 75, y: 280, role: 'React + Vite UI components' },
  { id: 'backend', label: 'Backend Agent', icon: FaCode, x: 375, y: 280, role: 'FastAPI routes & business logic' },
  { id: 'database', label: 'Database Agent', icon: FaDatabase, x: 675, y: 280, role: 'PostgreSQL schemas & migrations' },

  { id: 'assembly', label: 'Assembly Agent', icon: FaCubes, x: 375, y: 370, role: 'Merges parallel outputs into one project tree' },
  { id: 'reviewer', label: 'Reviewer Agent', icon: FaSearch, x: 375, y: 450, role: 'Validates code quality & consistency' },

  { id: 'build_validation', label: 'Build Validation', icon: FaHammer, x: 35, y: 540, role: 'Confirms the project actually compiles/builds' },
  { id: 'dependency_manager', label: 'Dependency Manager', icon: FaBoxes, x: 255, y: 540, role: 'Resolves & pins package dependencies' },
  { id: 'security_scan', label: 'Security Agent', icon: FaShieldAlt, x: 495, y: 540, role: 'Scans for secrets, CVEs & unsafe patterns' },
  { id: 'performance', label: 'Performance Agent', icon: FaTachometerAlt, x: 715, y: 540, role: 'Flags slow queries & render bottlenecks' },

  { id: 'execution_validation', label: 'Execution Validation', icon: FaTerminal, x: 375, y: 630, role: 'Actually runs the generated app end-to-end' },
  { id: 'testing', label: 'Testing Agent', icon: FaVial, x: 375, y: 710, role: 'Executes the automated test suite' },

  { id: 'documentation', label: 'Documentation Agent', icon: FaBook, x: 75, y: 800, role: 'Generates API docs & README' },
  { id: 'debug_loop', label: 'Debug → Fix → Retest Loop', icon: FaWrench, x: 675, y: 800, type: 'loop', role: 'Root-cause diagnosis & targeted repair' },

  { id: 'packaging', label: 'Packaging Agent', icon: FaBoxOpen, x: 375, y: 890, role: 'Bundles the project into a deployable artifact' },
  { id: 'deployment', label: 'Deployment Agent', icon: FaCloudUploadAlt, x: 375, y: 970, role: 'Ships the build to the target environment' },
];

const NODE_W = 150; // px, matches the box width below

export default function AgentOrchestrationGraph({
  generationStatus = null,
  activeAgentName = null,
  onSelectNode = null,
}) {
  const [selectedNode, setSelectedNode] = useState(null);

  const findAgent = (name) => generationStatus?.agents?.find((a) => a.name === name);

  const getNodeStatus = (nodeId) => {
    if (!generationStatus?.agents) return 'idle';

    if (nodeId === 'hitl_arch') {
      // Not a tracked backend agent - infer from whether downstream work has started.
      const started = generationStatus.agents.some((a) => a.name !== 'planner' && a.name !== 'architect' && a.status && a.status !== 'waiting');
      return started ? 'completed' : (findAgent('architect')?.status === 'completed' ? 'running' : 'waiting');
    }

    if (nodeId === 'debug_loop') {
      const debug = findAgent('debug');
      const patch = findAgent('patch');
      const statuses = [debug?.status, patch?.status].filter(Boolean);
      if (statuses.includes('running')) return 'running';
      if (statuses.includes('failed')) return 'failed';
      if (statuses.length && statuses.every((s) => s === 'completed')) return 'completed';
      return statuses.length ? 'waiting' : 'idle';
    }

    const agent = findAgent(nodeId);
    if (!agent) return 'idle';
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
    if (status === 'idle') {
      // No generation is running at all - distinct from "queued behind a live run".
      return (
        <span className="text-[9px] font-mono font-semibold text-slate-600 bg-slate-900/60 px-1.5 py-0.5 rounded">
          IDLE
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
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <FaRobot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-white">Autonomous Software Factory — Agent Org Chart</h3>
            <p className="text-[11px] text-slate-400">Live LangGraph pipeline: plan → build → review → secure → test → self-heal → ship</p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 text-[10px] font-mono">
          <span className="flex items-center gap-1 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Passed</span>
          <span className="flex items-center gap-1 text-cyan-400"><span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" /> Running</span>
          <span className="flex items-center gap-1 text-rose-400"><span className="w-2 h-2 rounded-full bg-rose-400" /> Failed</span>
          <span className="flex items-center gap-1 text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-400" /> Retry Loop</span>
        </div>
      </div>

      {/* Visual Workflow Graph */}
      <div className="relative w-full h-[1050px] bg-[#060911] border border-slate-800/60 rounded-xl p-4 overflow-auto custom-scrollbar">
        <div className="relative" style={{ width: '900px', height: '1030px' }}>
          <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-slate-700/60 stroke-[1.5] fill-none">
            <path d="M 450 75 L 450 110" markerEnd="url(#arrow)" />
            <path d="M 450 155 L 450 190" markerEnd="url(#arrow)" />

            <path d="M 450 235 L 150 280" markerEnd="url(#arrow)" />
            <path d="M 450 235 L 450 280" markerEnd="url(#arrow)" />
            <path d="M 450 235 L 750 280" markerEnd="url(#arrow)" />

            <path d="M 150 325 L 450 370" markerEnd="url(#arrow)" />
            <path d="M 450 325 L 450 370" markerEnd="url(#arrow)" />
            <path d="M 750 325 L 450 370" markerEnd="url(#arrow)" />

            <path d="M 450 415 L 450 450" markerEnd="url(#arrow)" />

            <path d="M 450 495 L 110 540" markerEnd="url(#arrow)" />
            <path d="M 450 495 L 330 540" markerEnd="url(#arrow)" />
            <path d="M 450 495 L 570 540" markerEnd="url(#arrow)" />
            <path d="M 450 495 L 790 540" markerEnd="url(#arrow)" />

            <path d="M 110 585 L 450 630" markerEnd="url(#arrow)" />
            <path d="M 330 585 L 450 630" markerEnd="url(#arrow)" />
            <path d="M 570 585 L 450 630" markerEnd="url(#arrow)" />
            <path d="M 790 585 L 450 630" markerEnd="url(#arrow)" />

            <path d="M 450 675 L 450 710" markerEnd="url(#arrow)" />

            <path d="M 430 755 L 150 800" markerEnd="url(#arrow)" />
            <path d="M 470 755 L 750 800" markerEnd="url(#arrow)" />

            <path d="M 150 845 L 450 890" markerEnd="url(#arrow)" />
            <path d="M 750 845 L 450 890" markerEnd="url(#arrow)" />

            <path d="M 450 935 L 450 970" markerEnd="url(#arrow)" />

            {/* Retry loop: debug_loop back to testing */}
            <path d="M 800 800 C 870 730, 850 630, 525 705" strokeDasharray="4" stroke="#f59e0b" markerEnd="url(#arrow-loop)" />

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
            const isActive = activeAgentName === node.id;

            return (
              <div
                key={node.id}
                onClick={() => {
                  setSelectedNode(node);
                  onSelectNode?.(node);
                }}
                style={{ left: `${node.x}px`, top: `${node.y}px`, width: `${NODE_W}px` }}
                className={`absolute p-2.5 rounded-xl border transition-all duration-200 cursor-pointer shadow-lg z-10 ${
                  isSelected
                    ? 'bg-indigo-600/25 border-cyan-400 ring-2 ring-cyan-500/30'
                    : isActive || status === 'running'
                    ? 'bg-slate-900/90 border-cyan-500/60 shadow-cyan-500/10'
                    : status === 'failed'
                    ? 'bg-rose-950/40 border-rose-700/60'
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
