import React, { useMemo, useState } from 'react';
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

const EDGES = [
  ['planner', 'architect'],
  ['architect', 'hitl_arch'],
  ['hitl_arch', 'frontend'], ['hitl_arch', 'backend'], ['hitl_arch', 'database'],
  ['frontend', 'assembly'], ['backend', 'assembly'], ['database', 'assembly'],
  ['assembly', 'reviewer'],
  ['reviewer', 'build_validation'], ['reviewer', 'dependency_manager'], ['reviewer', 'security_scan'], ['reviewer', 'performance'],
  ['build_validation', 'execution_validation'], ['dependency_manager', 'execution_validation'], ['security_scan', 'execution_validation'], ['performance', 'execution_validation'],
  ['execution_validation', 'testing'],
  ['testing', 'documentation'], ['testing', 'debug_loop'],
  ['documentation', 'packaging'], ['debug_loop', 'packaging'],
  ['packaging', 'deployment'],
];

const NODE_W = 150;
const NODE_H = 74;
const nodeById = Object.fromEntries(NODES.map((n) => [n.id, n]));
const centerX = (n) => n.x + NODE_W / 2;

function curvePath(from, to) {
  const x1 = centerX(from);
  const y1 = from.y + NODE_H;
  const x2 = centerX(to);
  const y2 = to.y;
  const midY = (y1 + y2) / 2;
  return `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
}

const STATUS_COLOR = {
  running: '#22d3ee',
  completed: '#10b981',
  failed: '#f43f5e',
  idle: '#334155',
  waiting: '#334155',
};

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

  // Precompute once per render pass so both the SVG edges and the node cards agree.
  const statusById = useMemo(() => {
    const map = {};
    NODES.forEach((n) => { map[n.id] = getNodeStatus(n.id); });
    return map;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [generationStatus]);

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

  const passedCount = Object.values(statusById).filter((s) => s === 'completed').length;

  return (
    <div className="bg-[#090d16] border border-slate-800/90 rounded-2xl p-4 font-sans select-none relative overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500/20 to-indigo-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(34,211,238,0.25)]">
            <FaRobot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-white tracking-tight">Autonomous Software Factory — Agent Org Chart</h3>
            <p className="text-[11px] text-slate-400">Live LangGraph pipeline: plan → build → review → secure → test → self-heal → ship</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {generationStatus?.agents && (
            <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-1 rounded-lg">
              {passedCount}/{NODES.length} PASSED
            </span>
          )}
          <div className="flex items-center gap-2.5 text-[10px] font-mono">
            <span className="flex items-center gap-1 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Passed</span>
            <span className="flex items-center gap-1 text-cyan-400"><span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" /> Running</span>
            <span className="flex items-center gap-1 text-rose-400"><span className="w-2 h-2 rounded-full bg-rose-400" /> Failed</span>
            <span className="flex items-center gap-1 text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-400" /> Retry Loop</span>
          </div>
        </div>
      </div>

      {/* Visual Workflow Graph */}
      <div
        className="relative w-full h-[1050px] bg-[#060911] border border-slate-800/60 rounded-xl p-4 overflow-auto custom-scrollbar"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(100,116,139,0.16) 1px, transparent 1px)',
          backgroundSize: '22px 22px',
        }}
      >
        <div className="relative" style={{ width: '900px', height: '1030px' }}>
          <svg className="absolute inset-0 w-full h-full pointer-events-none fill-none">
            {EDGES.map(([fromId, toId]) => {
              const from = nodeById[fromId];
              const to = nodeById[toId];
              const fromStatus = statusById[fromId];
              const toStatus = statusById[toId];
              const active = fromStatus === 'completed' || fromStatus === 'success';
              const isRunning = toStatus === 'running';
              const isFailed = toStatus === 'failed';
              const color = isFailed ? STATUS_COLOR.failed : isRunning ? STATUS_COLOR.running : active ? STATUS_COLOR.completed : STATUS_COLOR.idle;

              return (
                <path
                  key={`${fromId}-${toId}`}
                  d={curvePath(from, to)}
                  stroke={color}
                  strokeWidth={active || isRunning ? 2 : 1.5}
                  strokeOpacity={active || isRunning || isFailed ? 0.9 : 0.45}
                  strokeDasharray={isRunning ? '6 6' : undefined}
                  className={isRunning ? 'animate-dash-flow' : ''}
                  markerEnd={isFailed ? 'url(#arrow-failed)' : isRunning ? 'url(#arrow-running)' : active ? 'url(#arrow-passed)' : 'url(#arrow-idle)'}
                />
              );
            })}

            {/* Retry loop: debug_loop back to testing */}
            <path
              d="M 825 837 C 900 780, 880 700, 525 747"
              strokeDasharray="4 5"
              stroke="#f59e0b"
              strokeWidth={2}
              className={statusById.debug_loop === 'running' ? 'animate-dash-flow' : ''}
              markerEnd="url(#arrow-loop)"
            />

            <defs>
              {[
                ['arrow-idle', STATUS_COLOR.idle],
                ['arrow-passed', STATUS_COLOR.completed],
                ['arrow-running', STATUS_COLOR.running],
                ['arrow-failed', STATUS_COLOR.failed],
                ['arrow-loop', '#f59e0b'],
              ].map(([id, color]) => (
                <marker key={id} id={id} viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 0 L 10 5 L 0 10 z" fill={color} />
                </marker>
              ))}
            </defs>
          </svg>

          {/* Interactive Node Cards */}
          {NODES.map((node) => {
            const Icon = node.icon;
            const status = statusById[node.id];
            const isSelected = selectedNode?.id === node.id;
            // Status is the authoritative live signal; activeAgentName can lag behind it
            // once a run finishes, so it only ever adds emphasis, never overrides status.
            const isActive = status === 'running' || (activeAgentName === node.id && status !== 'completed' && status !== 'failed');

            const cardTone =
              status === 'failed'
                ? 'bg-gradient-to-br from-rose-950/50 to-slate-950/95 border-rose-600/60'
                : isActive
                ? 'bg-gradient-to-br from-cyan-950/50 to-slate-950/95 border-cyan-400/70 animate-node-glow'
                : status === 'completed'
                ? 'bg-gradient-to-br from-emerald-950/20 to-slate-950/95 border-emerald-700/40 hover:border-emerald-500/60'
                : 'bg-slate-950/90 border-slate-800 hover:border-slate-600';

            const iconTone =
              status === 'failed'
                ? 'bg-rose-500/15 text-rose-400 ring-1 ring-rose-500/40'
                : isActive
                ? 'bg-cyan-500/15 text-cyan-300 ring-1 ring-cyan-400/50'
                : status === 'completed'
                ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-600/30'
                : 'bg-slate-900 text-slate-500 ring-1 ring-slate-800';

            return (
              <div
                key={node.id}
                onClick={() => {
                  setSelectedNode(node);
                  onSelectNode?.(node);
                }}
                style={{ left: `${node.x}px`, top: `${node.y}px`, width: `${NODE_W}px` }}
                className={`absolute p-2.5 rounded-xl border transition-all duration-200 cursor-pointer shadow-lg z-10 hover:scale-[1.03] hover:shadow-xl ${
                  isSelected ? 'ring-2 ring-cyan-400/60 border-cyan-400' : cardTone
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center ${iconTone}`}>
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
