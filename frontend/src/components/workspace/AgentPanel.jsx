import React, { useMemo, useState } from 'react';
import { FaRobot, FaCheckCircle, FaClock, FaTimesCircle, FaHourglassHalf, FaChevronDown, FaChevronRight, FaBars } from 'react-icons/fa';

const STATUS_META = {
  completed: { label: 'COMPLETED', color: 'text-emerald-400', icon: FaCheckCircle },
  running: { label: 'RUNNING', color: 'text-cyan-400', icon: FaHourglassHalf },
  waiting: { label: 'WAITING', color: 'text-slate-400', icon: FaClock },
  failed: { label: 'FAILED', color: 'text-rose-400', icon: FaTimesCircle },
  blocked: { label: 'BLOCKED', color: 'text-amber-400', icon: FaTimesCircle },
  unknown: { label: 'UNKNOWN', color: 'text-slate-500', icon: FaBars },
};

const AGENT_LABELS = {
  planner: 'Planner Agent',
  architect: 'Architect Agent',
  frontend: 'Frontend Agent',
  backend: 'Backend Agent',
  database: 'Database Agent',
  assembly: 'Assembly Agent',
  reviewer: 'Reviewer Agent',
  documentation: 'Documentation Agent',
  testing: 'Testing Agent',
  deployment: 'Deployment Agent',
  build_validation: 'Build Agent',
  dependency_manager: 'Dependency Agent',
  security_scan: 'Security Agent',
  performance: 'Performance Agent',
  execution_validation: 'Execution Agent',
  patch: 'Repair Agent',
  packaging: 'Packaging Agent',
};

export default function AgentPanel({ generation = null, onAgentSelect }) {
  const [expanded, setExpanded] = useState(true);

  const agents = useMemo(() => {
    if (!generation?.agents?.length) return [];
    const ordered = generation.agents.slice();
    return ordered.map((agent) => ({
      ...agent,
      displayName: AGENT_LABELS[agent.name] || agent.name || 'Agent',
      normalizedStatus: (agent.status || 'unknown').toLowerCase(),
    }));
  }, [generation]);

  const latestAgent = agents.find((agent) => agent.status?.toLowerCase() === 'running') || agents[agents.length - 1] || null;

  return (
    <div className="bg-[#090d16] border-l border-slate-800/80 w-72 xl:w-80 flex flex-col shrink-0 min-h-0 overflow-hidden select-none">
      <div className="flex items-center justify-between px-3 py-3 border-b border-slate-800/80 bg-slate-950">
        <div className="flex items-center gap-2">
          <FaRobot className="text-cyan-400 w-4 h-4" />
          <div>
            <div className="text-[11px] uppercase tracking-[0.22em] text-slate-400 font-semibold">AI Agents</div>
            <div className="text-sm font-semibold text-white">Specialized Team</div>
          </div>
        </div>
        <button
          className="text-slate-400 hover:text-white"
          onClick={() => setExpanded((prev) => !prev)}
          title={expanded ? 'Collapse Agent Panel' : 'Expand Agent Panel'}
        >
          {expanded ? <FaChevronDown className="w-4 h-4" /> : <FaChevronRight className="w-4 h-4" />}
        </button>
      </div>

      {expanded ? (
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="px-3 py-3 border-b border-slate-800/80 bg-slate-950 text-[11px] font-mono text-slate-400">
            {generation ? (
              <div className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span>Status</span>
                  <span className="text-cyan-300 font-semibold uppercase">{generation.status || 'Not available'}</span>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span>Progress</span>
                  <span className="font-semibold text-emerald-400">{generation.progress ?? 0}%</span>
                </div>
              </div>
            ) : (
              <span>Agent status unavailable</span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-2">
            {agents.length === 0 ? (
              <div className="text-slate-500 text-xs italic">No agent data available.</div>
            ) : (
              agents.map((agent) => {
                const meta = STATUS_META[agent.normalizedStatus] || STATUS_META.unknown;
                const Icon = meta.icon;
                return (
                  <button
                    key={agent.name}
                    onClick={() => onAgentSelect?.(agent)}
                    className="w-full text-left p-3 bg-slate-950/80 border border-slate-800 rounded-xl transition hover:border-cyan-500/50 hover:bg-slate-900 flex items-start gap-3"
                  >
                    <span className={`mt-1 ${meta.color}`}><Icon className="w-4 h-4" /></span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-slate-100 font-semibold text-[12px]">{agent.displayName}</span>
                        <span className={`text-[10px] uppercase tracking-[0.25em] font-bold ${meta.color}`}>{meta.label}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1 leading-snug">
                        {agent.error ? agent.error : agent.name ? `Last run: ${agent.started_at || 'unknown'}` : 'No details available'}
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>

          <div className="px-3 pb-3 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
            <div className="font-semibold text-slate-200 text-xs">Agent Activity</div>
            <div className="mt-2 text-[10px] text-slate-500">AIForge synchronizes agent states with your backend generation workflow and preserves latest status across sessions.</div>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-center flex-1 text-slate-500 text-xs italic">Collapsed</div>
      )}
    </div>
  );
}
