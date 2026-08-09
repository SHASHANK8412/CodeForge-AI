/**
 * AgentPipeline.jsx
 * ==================
 * Visualizes the real parallel LangGraph workflow structure.
 * Matches the actual graph edges in parallel_workflow.py:
 *   Planner → Architect → [Frontend | Backend | Database] → Assembly
 *   → Reviewer → Documentation → Build Validation → Dependency Manager
 *   → Security → Performance → Execution Validation → Testing
 *   ↳ (on fail) Debug → Patch → back to Execution Validation
 *   → Packaging → Deployment
 *
 * All statuses come from real backend data — no hardcoded labels.
 */

import React from 'react';
import {
  FaCheckCircle, FaSpinner, FaClock, FaTimesCircle,
  FaArrowDown, FaWrench, FaRedo,
} from 'react-icons/fa';

const STATUS_CONFIG = {
  completed: {
    icon: <FaCheckCircle className="w-3 h-3 text-emerald-400" />,
    label: 'Completed',
    labelClass: 'text-emerald-400',
    boxClass: 'bg-slate-900 border-emerald-800/40',
  },
  running: {
    icon: <FaSpinner className="w-3 h-3 animate-spin text-cyan-400" />,
    label: 'Running',
    labelClass: 'text-cyan-400',
    boxClass: 'bg-indigo-950/60 border-cyan-400/50 shadow-cyan-500/10 shadow-md',
  },
  failed: {
    icon: <FaTimesCircle className="w-3 h-3 text-rose-400" />,
    label: 'Failed',
    labelClass: 'text-rose-400',
    boxClass: 'bg-rose-950/30 border-rose-800/40',
  },
  retrying: {
    icon: <FaRedo className="w-3 h-3 animate-spin text-amber-400" />,
    label: 'Retrying',
    labelClass: 'text-amber-400',
    boxClass: 'bg-amber-950/30 border-amber-700/40',
  },
  repairing: {
    icon: <FaWrench className="w-3 h-3 animate-bounce text-amber-400" />,
    label: 'Repairing',
    labelClass: 'text-amber-400',
    boxClass: 'bg-amber-950/30 border-amber-700/40',
  },
  waiting: {
    icon: <FaClock className="w-3 h-3 text-slate-600" />,
    label: 'Waiting',
    labelClass: 'text-slate-500',
    boxClass: 'bg-slate-950/60 border-slate-800/80 opacity-60',
  },
  skipped: {
    icon: <FaClock className="w-3 h-3 text-slate-500" />,
    label: 'Skipped',
    labelClass: 'text-slate-500',
    boxClass: 'bg-slate-950/60 border-slate-800/80 opacity-40',
  },
};

function AgentBox({ name, label, agentsMap }) {
  const info = agentsMap[name] || {};
  const status = info.status || 'waiting';
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.waiting;
  const duration = info.duration ? `${info.duration.toFixed(1)}s` : null;
  const retries = info.retry_count > 0 ? `${info.retry_count} retry` : null;

  return (
    <div className={`p-3 rounded-xl border text-xs transition-all ${cfg.boxClass}`}>
      <div className="flex items-center justify-between mb-0.5">
        <span className="font-bold text-white text-[11px]">{label}</span>
        <span className={`font-mono text-[10px] flex items-center gap-1 ${cfg.labelClass}`}>
          {cfg.icon} {cfg.label}
        </span>
      </div>
      {(duration || retries) && (
        <div className="flex gap-3 mt-1">
          {duration && <span className="text-[10px] text-slate-500 font-mono">{duration}</span>}
          {retries && <span className="text-[10px] text-amber-500 font-mono">{retries}</span>}
        </div>
      )}
      {!duration && !retries && (
        <p className="text-[10px] text-slate-600 italic mt-0.5">
          {status === 'waiting' ? 'Waiting in queue…' : ''}
        </p>
      )}
    </div>
  );
}

function Arrow() {
  return (
    <div className="flex justify-center text-slate-700 my-0.5">
      <FaArrowDown className="w-3 h-3" />
    </div>
  );
}

export default function AgentPipeline({ agentsMap = {} }) {
  const box = (name, label) => (
    <AgentBox name={name} label={label} agentsMap={agentsMap} />
  );

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 shadow-xl font-sans space-y-1.5">
      <h3 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-3 border-b border-slate-800 pb-2">
        Multi-Agent Workflow Pipeline
      </h3>

      {/* Sequential: Planner */}
      {box('planner', 'Planner Agent')}
      <Arrow />

      {/* Sequential: Architect */}
      {box('architect', 'Architect Agent')}
      <Arrow />

      {/* Parallel fan-out: Frontend | Backend | Database */}
      <div className="p-3 bg-slate-900/40 border border-indigo-500/20 rounded-xl">
        <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400 mb-2 text-center">
          ⚡ Parallel Code Generation
        </div>
        <div className="grid grid-cols-3 gap-2">
          {box('frontend', 'Frontend')}
          {box('backend', 'Backend')}
          {box('database', 'Database')}
        </div>
      </div>
      <Arrow />

      {/* Fan-in: Assembly */}
      {box('assembly', 'Project Assembly')}
      <Arrow />

      {/* Sequential: Reviewer */}
      {box('reviewer', 'Reviewer Agent')}
      <Arrow />

      {/* Sequential: Documentation */}
      {box('documentation', 'Documentation')}
      <Arrow />

      {/* Platform checks */}
      <div className="p-3 bg-slate-900/40 border border-slate-700/30 rounded-xl">
        <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 mb-2 text-center">
          Quality & Validation
        </div>
        <div className="grid grid-cols-2 gap-2">
          {box('build_validation', 'Build Check')}
          {box('dependency_manager', 'Dependencies')}
          {box('security_scan', 'Security')}
          {box('performance', 'Performance')}
        </div>
      </div>
      <Arrow />

      {/* Execution Validation */}
      {box('execution_validation', 'Execution Check')}
      <Arrow />

      {/* Testing */}
      {box('testing', 'Testing Agent')}

      {/* Debug/Patch loop (only shown when relevant) */}
      {(agentsMap['debug']?.status === 'running' ||
        agentsMap['debug']?.status === 'completed' ||
        agentsMap['patch']?.status === 'running' ||
        agentsMap['patch']?.status === 'completed') && (
        <div className="pl-4 border-l-2 border-amber-700/40 ml-2 space-y-1.5">
          <div className="text-[10px] text-amber-500 font-mono ml-1">↳ Self-Repair Loop</div>
          {box('debug', 'Debug Agent')}
          {box('patch', 'Patch Agent')}
        </div>
      )}
      <Arrow />

      {/* Packaging */}
      {box('packaging', 'Packaging')}
      <Arrow />

      {/* Deployment */}
      {box('deployment', 'Deployment')}
    </div>
  );
}
