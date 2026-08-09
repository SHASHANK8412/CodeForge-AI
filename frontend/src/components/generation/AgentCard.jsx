import React from 'react';
import { FaSpinner, FaClock, FaCheckCircle, FaCode, FaFileCode } from 'react-icons/fa';

export default function AgentCard({ currentAgent = 'frontend', progress = 72 }) {
  const agentDisplayNames = {
    planner: 'Planner Agent',
    architect: 'Architect Agent',
    frontend: 'Frontend Agent',
    backend: 'Backend Agent',
    database: 'Database Agent',
    reviewer: 'Reviewer Agent',
    testing: 'Testing Agent',
    documentation: 'Documentation Agent',
    completed: 'Pipeline Completed'
  };

  const agentDescriptions = {
    planner: 'Analyzing project prompt requirements and structuring execution task graph...',
    architect: 'Designing component architecture, OpenAPI route definitions, and schema models...',
    frontend: 'Generating responsive React application components and state containers...',
    backend: 'Creating FastAPI REST API endpoints, services, and validation schemas...',
    database: 'Designing PostgreSQL schema models, tables, relationships, and seed data...',
    reviewer: 'Inspecting generated code quality, static analysis AST, and SAST security policies...',
    testing: 'Executing automated pytest suite and verifying empirical test assertions...',
    documentation: 'Generating technical OpenAPI specification, setup guides, and project README...',
    completed: 'All specialized agents completed execution successfully. Project ready for export.'
  };

  const activeName = agentDisplayNames[currentAgent?.toLowerCase()] || 'Active Agent';
  const activeDesc = agentDescriptions[currentAgent?.toLowerCase()] || 'Processing pipeline stage...';

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans relative overflow-hidden">
      {/* Background Accent Glow */}
      <div className="absolute -top-10 -right-10 w-40 h-40 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
            <FaSpinner className="w-4 h-4 animate-spin text-cyan-400" />
          </div>
          <h3 className="text-base font-extrabold text-white">{activeName}</h3>
        </div>

        <span className="text-xs font-mono font-bold text-cyan-400 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-lg">
          {progress}%
        </span>
      </div>

      <p className="text-xs text-slate-300 mb-6 leading-relaxed">
        {activeDesc}
      </p>

      {/* Progress Indicator */}
      <div className="space-y-1.5 mb-6">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Agent Task Progress</span>
          <span className="font-mono text-cyan-400 font-bold">{progress}%</span>
        </div>
        <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Agent Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex items-center gap-3">
          <FaCode className="w-4 h-4 text-cyan-400 shrink-0" />
          <div>
            <div className="text-[11px] text-slate-400">Components</div>
            <div className="font-mono font-bold text-white text-sm">12</div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex items-center gap-3">
          <FaFileCode className="w-4 h-4 text-indigo-400 shrink-0" />
          <div>
            <div className="text-[11px] text-slate-400">Files Generated</div>
            <div className="font-mono font-bold text-white text-sm">28</div>
          </div>
        </div>
      </div>
    </div>
  );
}
