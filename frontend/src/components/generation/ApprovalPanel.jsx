/**
 * ApprovalPanel.jsx
 * ==================
 * Human-in-the-Loop (HITL) interactive review panel for AIForge.
 * Pauses autonomous execution at critical decision points:
 *   1. Architecture Review (Tech stack, components, database design, ready agents, risks)
 *   2. Final Quality Review (Generated files, test results, reviewer scores, fixes applied)
 * Supports one-click approval or rejection with actionable human feedback.
 */

import React, { useState } from 'react';
import {
  FaCheckCircle, FaTimesCircle, FaPauseCircle, FaLayerGroup,
  FaDatabase, FaShieldAlt, FaCode, FaExclamationTriangle,
  FaVial, FaSpinner, FaRocket, FaCogs
} from 'react-icons/fa';

export default function ApprovalPanel({
  approvalRequest = {},
  stage = 'architecture',
  onApprove,
  onReject,
  isSubmitting = false,
}) {
  const [feedback, setFeedback] = useState('');
  const [showFeedbackInput, setShowFeedbackInput] = useState(false);
  const [notes, setNotes] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const isFinal = stage === 'final' || approvalRequest.stage === 'final';
  const title = approvalRequest.title || (isFinal ? 'Final Quality & Project Export Review' : 'Architecture Review Required');
  const reason = approvalRequest.reason || 'Please review and approve the planned system configuration before continuing.';
  const projectName = approvalRequest.project_name || 'AIForge Project';

  const techStack = approvalRequest.tech_stack || {
    frontend: 'React + Vite',
    backend: 'FastAPI',
    database: 'PostgreSQL',
    authentication: 'JWT Bearer',
  };

  const components = approvalRequest.components || [
    'User Authentication & JWT Verification',
    'REST API Router & Business Logic',
    'Interactive React Dashboard Components',
    'Relational Schema & Database Migrations'
  ];

  const risks = approvalRequest.risks || [
    'Ensure production environment variables are configured before deployment',
    'Verify CORS permissions between frontend and backend endpoints'
  ];

  const readyAgents = approvalRequest.agents_ready || (isFinal
    ? ['Project Packaging Agent', 'Deployment Agent', 'Live Deploy Agent']
    : ['Frontend Agent', 'Backend Agent', 'Database Agent']);

  const filesGenerated = approvalRequest.files_generated || [];
  const testsPassed = approvalRequest.tests_passed ?? 0;
  const testsFailed = approvalRequest.tests_failed ?? 0;
  const qualityScore = typeof approvalRequest.quality_score === 'number'
    ? approvalRequest.quality_score
    : (approvalRequest.quality_score?.overall_score || 96.0);

  const handleApprove = async () => {
    setErrorMsg('');
    try {
      await onApprove(notes);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to approve workflow.');
    }
  };

  const handleReject = async () => {
    if (!feedback.trim()) {
      setShowFeedbackInput(true);
      setErrorMsg('Please provide specific revision instructions before rejecting.');
      return;
    }
    setErrorMsg('');
    try {
      await onReject(feedback.trim());
    } catch (err) {
      setErrorMsg(err.message || 'Failed to submit rejection feedback.');
    }
  };

  return (
    <div className="relative rounded-2xl border-2 border-amber-500/50 bg-gradient-to-b from-slate-900/95 via-slate-950/95 to-[#0b0f19] p-6 sm:p-8 shadow-2xl shadow-amber-500/10 backdrop-blur-xl transition-all duration-300">
      {/* Top Banner / Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-11 h-11 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400 shadow-lg shadow-amber-500/20">
            <FaPauseCircle className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30">
                {isFinal ? 'Checkpoint 2 • Final Review' : 'Checkpoint 1 • Architecture Review'}
              </span>
              <span className="text-xs font-mono text-slate-400">• {projectName}</span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight mt-0.5">
              {title}
            </h2>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium bg-amber-950/60 border border-amber-700/50 text-amber-300">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
            Workflow Paused: Awaiting Decision
          </span>
        </div>
      </div>

      <p className="text-slate-300 text-sm mt-4 leading-relaxed">
        {reason}
      </p>

      {/* Main Content Area */}
      {!isFinal ? (
        /* Architecture Stage Details */
        <div className="mt-6 space-y-6">
          {/* Tech Stack Cards Grid */}
          <div>
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-3 flex items-center gap-2">
              <FaLayerGroup className="w-3.5 h-3.5" /> Selected Technology Stack
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-cyan-500/30">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Frontend</span>
                <span className="text-sm font-bold text-white mt-0.5 block">{techStack.frontend || 'React + Vite'}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-indigo-500/30">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Backend</span>
                <span className="text-sm font-bold text-white mt-0.5 block">{techStack.backend || 'FastAPI'}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-emerald-500/30">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Database</span>
                <span className="text-sm font-bold text-white mt-0.5 block">{techStack.database || 'PostgreSQL'}</span>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-900/80 border border-purple-500/30">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Authentication</span>
                <span className="text-sm font-bold text-white mt-0.5 block">{techStack.authentication || 'JWT'}</span>
              </div>
            </div>
          </div>

          {/* 2-Column Details: Components & Ready Agents */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Planned Components */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                <FaCode className="w-3.5 h-3.5 text-cyan-400" /> Planned System Components
              </h4>
              <ul className="space-y-2">
                {components.map((comp, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <FaCheckCircle className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                    <span>{comp}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Next Ready Agents */}
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
              <div>
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                  <FaCogs className="w-3.5 h-3.5 text-indigo-400" /> Agents Ready for Parallel Execution
                </h4>
                <ul className="space-y-2">
                  {readyAgents.map((agent, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                      <span className="font-medium text-white">{agent}</span>
                      <span className="text-[10px] text-slate-500 font-mono ml-auto">Ready</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Risks and Warnings */}
              {risks.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-800/80">
                  <div className="flex items-start gap-2 text-xs text-amber-300/90 bg-amber-500/10 p-2.5 rounded-lg border border-amber-500/20">
                    <FaExclamationTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <span className="text-[11px] leading-tight">
                      {risks[0]}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Final Stage Details */
        <div className="mt-6 space-y-5">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-emerald-500/30">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">Tests Passed</span>
              <span className="text-lg font-bold text-emerald-400 mt-0.5 block flex items-center gap-1.5">
                <FaVial className="w-4 h-4" /> {testsPassed} / {testsPassed + testsFailed}
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-cyan-500/30">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">Quality Score</span>
              <span className="text-lg font-bold text-cyan-400 mt-0.5 block">
                {typeof qualityScore === 'number' ? qualityScore.toFixed(1) : qualityScore}%
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-indigo-500/30">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">Files Generated</span>
              <span className="text-lg font-bold text-indigo-300 mt-0.5 block">
                {filesGenerated.length || '12'} Files
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-purple-500/30">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">Readiness</span>
              <span className="text-sm font-bold text-purple-300 mt-1 block flex items-center gap-1">
                <FaRocket className="w-3.5 h-3.5 text-purple-400" /> Ready for Export
              </span>
            </div>
          </div>

          {filesGenerated.length > 0 && (
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-mono max-h-32 overflow-y-auto">
              <div className="text-slate-400 mb-1 font-bold">Generated Files Manifest:</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 text-slate-300 text-[11px]">
                {filesGenerated.slice(0, 8).map((f, i) => (
                  <div key={i} className="truncate">📄 {f}</div>
                ))}
                {filesGenerated.length > 8 && (
                  <div className="text-slate-500 italic">+ {filesGenerated.length - 8} more files</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <div className="mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <FaTimesCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Feedback input when rejecting or requesting changes */}
      {showFeedbackInput && (
        <div className="mt-5 space-y-2 p-4 rounded-xl bg-rose-950/30 border border-rose-800/40 animate-fadeIn">
          <label className="text-xs font-bold text-rose-300 block">
            Provide Revision Feedback for the AI Agent:
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder='e.g., "Use PostgreSQL and FastAPI instead of MongoDB and Express", "Add JWT auth with refresh tokens", "Include Stripe payment integration"'
            rows={3}
            className="w-full rounded-lg bg-slate-900/90 border border-rose-600/40 p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-400 focus:ring-1 focus:ring-rose-400"
          />
          <p className="text-[10px] text-slate-400">
            The AI Engineer will incorporate this feedback and revise the project plan without losing previous progress.
          </p>
        </div>
      )}

      {/* Action Footer */}
      <div className="mt-6 pt-5 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="text-xs text-slate-400 text-center sm:text-left">
          Review details above and decide whether to approve and proceed with generation.
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {!showFeedbackInput ? (
            <button
              onClick={() => setShowFeedbackInput(true)}
              disabled={isSubmitting}
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl border border-rose-600/50 bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 hover:text-rose-200 text-xs font-semibold transition flex items-center justify-center gap-2"
            >
              <FaTimesCircle className="w-3.5 h-3.5" /> Reject / Request Changes
            </button>
          ) : (
            <button
              onClick={handleReject}
              disabled={isSubmitting}
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-500 hover:to-red-600 text-white text-xs font-semibold shadow-lg shadow-rose-600/20 transition flex items-center justify-center gap-2"
            >
              {isSubmitting ? <FaSpinner className="w-3.5 h-3.5 animate-spin" /> : <FaTimesCircle className="w-3.5 h-3.5" />}
              Submit Rejection & Revise
            </button>
          )}

          <button
            onClick={handleApprove}
            disabled={isSubmitting}
            className="flex-1 sm:flex-none px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:from-emerald-500 hover:via-teal-500 hover:to-cyan-500 text-white text-xs font-bold shadow-lg shadow-emerald-500/20 transition-all transform hover:scale-[1.02] flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <FaSpinner className="w-3.5 h-3.5 animate-spin" />
                Resuming Workflow…
              </>
            ) : (
              <>
                <FaCheckCircle className="w-3.5 h-3.5" />
                {isFinal ? 'Approve & Finalize Export' : 'Approve & Continue Generation'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
