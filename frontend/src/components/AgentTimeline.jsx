import React from 'react';
import { FaCheckCircle, FaClock, FaExclamationTriangle, FaSync, FaSpinner } from 'react-icons/fa';

const STAGES = [
  { id: 'planner', label: 'Planner Agent' },
  { id: 'architect', label: 'Architect Agent' },
  { id: 'frontend', label: 'Frontend Agent' },
  { id: 'backend', label: 'Backend Agent' },
  { id: 'database', label: 'Database Agent' },
  { id: 'reviewer', label: 'Reviewer Agent' },
  { id: 'testing', label: 'Testing Agent' },
  { id: 'documentation', label: 'Documentation Agent' },
  { id: 'build_validation', label: 'Build Validation' },
  { id: 'dependency_manager', label: 'Dependency Manager' },
  { id: 'security_scan', label: 'Security Scan' },
  { id: 'performance', label: 'Performance Agent' },
  { id: 'execution_validation', label: 'Execution Validation' },
  { id: 'self_healing', label: 'Self-Healing Loop' },
  { id: 'packaging', label: 'Packaging Agent' },
  { id: 'deployment', label: 'Deployment Agent' },
];

export default function AgentTimeline({ currentStep, isGenerating, streamEvents = [] }) {
  const getStepIndex = (stepId) => STAGES.findIndex((s) => s.id === stepId);
  const currentIndex = getStepIndex(currentStep);
  const progressPercent = isGenerating
    ? Math.min(95, Math.round(((currentIndex + 1) / STAGES.length) * 100))
    : currentStep === 'deployment' || currentStep === 'complete' ? 100 : 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold tracking-wide text-indigo-400 uppercase flex items-center gap-2">
          {isGenerating ? (
            <FaSpinner className="w-4 h-4 animate-spin text-indigo-400" />
          ) : (
            <FaCheckCircle className="w-4 h-4 text-emerald-400" />
          )}
          Autonomous Agent Execution Pipeline
        </h3>
        <span className="text-xs font-mono bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-1 rounded-full">
          {progressPercent}% Complete
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-2 mb-5 overflow-hidden">
        <div
          className="bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 h-2 rounded-full transition-all duration-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Agent Timeline Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2 mb-4">
        {STAGES.map((stage, idx) => {
          let status = 'idle';
          if (idx < currentIndex) status = 'completed';
          else if (idx === currentIndex && isGenerating) status = 'running';
          else if (currentStep === 'self_healing' && stage.id === 'self_healing') status = 'healing';
          else if (progressPercent === 100) status = 'completed';

          return (
            <div
              key={stage.id}
              className={`flex flex-col items-center justify-center p-2.5 rounded-lg border text-center text-xs transition-all ${
                status === 'completed'
                  ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                  : status === 'running'
                  ? 'bg-indigo-950/80 border-indigo-500 text-indigo-200 animate-pulse'
                  : status === 'healing'
                  ? 'bg-amber-950/60 border-amber-500 text-amber-300'
                  : 'bg-slate-950/40 border-slate-800/60 text-slate-500'
              }`}
            >
              <div className="mb-1">
                {status === 'completed' && <FaCheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
                {status === 'running' && <FaSpinner className="w-3.5 h-3.5 text-indigo-400 animate-spin" />}
                {status === 'healing' && <FaSync className="w-3.5 h-3.5 text-amber-400 animate-spin" />}
                {status === 'idle' && <FaClock className="w-3.5 h-3.5 text-slate-600" />}
              </div>
              <span className="font-medium text-[10px] leading-tight truncate w-full">{stage.label}</span>
            </div>
          );
        })}
      </div>

      {/* Live Event Log Terminal */}
      {streamEvents.length > 0 && (
        <div className="bg-slate-950 rounded-lg p-3 border border-slate-800 font-mono text-[11px] max-h-32 overflow-y-auto space-y-1">
          <div className="text-slate-500 text-[10px] uppercase font-sans font-semibold mb-1">Live Execution Stream Log:</div>
          {streamEvents.map((evt, index) => (
            <div key={index} className="text-emerald-400 flex items-start gap-1.5">
              <span className="text-slate-600">›</span>
              <span>{evt}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
