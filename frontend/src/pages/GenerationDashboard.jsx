/**
 * GenerationDashboard.jsx
 * ========================
 * Real-time generation build dashboard.
 * Consumes real backend events via SSE + polling fallback.
 * All data is sourced from the live API — no fake fallback data.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import ProjectHeader from '../components/generation/ProjectHeader';
import AgentPipeline from '../components/generation/AgentPipeline';
import AgentCard from '../components/generation/AgentCard';
import AgentLogs from '../components/generation/AgentLogs';
import ProgressBar from '../components/generation/ProgressBar';
import CompletionActions from '../components/generation/CompletionActions';
import RepairLoop from '../components/generation/RepairLoop';
import ApprovalPanel from '../components/generation/ApprovalPanel';
import DebugActivityPanel from '../components/generation/DebugActivityPanel';
import {

  connectGenerationStream,
  cancelGeneration,
  approveGeneration,
  rejectGeneration,
  isTerminalStatus,
} from '../services/generation';


// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const AGENT_ORDER = [
  'planner', 'architect', 'frontend', 'backend', 'database',
  'assembly', 'reviewer', 'documentation', 'build_validation',
  'dependency_manager', 'security_scan', 'performance',
  'execution_validation', 'testing', 'debug', 'patch', 'packaging', 'deployment',
];

function formatTime(isoStr) {
  if (!isoStr) return '';
  try {
    return new Date(isoStr).toLocaleTimeString();
  } catch (_) {
    return isoStr;
  }
}

function agentLabel(name) {
  return (name || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function buildAgentsMap(agents = []) {
  const map = {};
  agents.forEach((a) => { map[a.name] = a; });
  return map;
}

function buildLogsFromEvents(events = []) {
  return events
    .filter((e) => e.type !== 'snapshot' && e.type !== 'heartbeat')
    .map((e) => {
      const time = formatTime(e.timestamp);
      const icon = e.type?.includes('completed') ? '✓' : e.type?.includes('failed') ? '✗' : '⟳';
      const agent = e.agent ? `[${agentLabel(e.agent)}] ` : '';
      return `${time}  ${icon} ${agent}${e.message || e.type}`;
    });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function GenerationDashboard({
  generationId,
  setView,
  setActiveProjectName,
}) {

  const [generation, setGeneration] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connectionMode, setConnectionMode] = useState('connecting'); // 'sse' | 'polling' | 'connecting'
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [showFailModal, setShowFailModal] = useState(false);
  const streamRef = useRef(null);
  const completedFiredRef = useRef(false);

  // Derive ID: from props or URL
  const genId = generationId
    || window.location.pathname.split('/').find((p) => p.startsWith('gen_'))
    || 'unknown';

  // ----- Apply snapshot (full status) -----
  const applySnapshot = useCallback((snap) => {
    setGeneration((prev) => ({ ...(prev || {}), ...snap }));
    setLoading(false);
    if (snap.project_id && setActiveProjectName) {
      setActiveProjectName(snap.project_id);
    }

    if (!completedFiredRef.current) {
      if (snap.status === 'completed') {
        completedFiredRef.current = true;
        setShowCompleteModal(true);
      } else if (snap.status === 'failed') {
        completedFiredRef.current = true;
        setShowFailModal(true);
      }
    }
  }, [setActiveProjectName]);

  // ----- Apply a single live event -----
  const applyEvent = useCallback((evt) => {
    setEvents((prev) => {
      // De-duplicate by event id if present
      if (evt.id && prev.find((e) => e.id === evt.id)) return prev;
      return [...prev, evt];
    });

    // Update agent status in generation state
    const { type, agent, progress, metadata } = evt;

    if (type === 'approval_required') {
      setGeneration((prev) => prev ? {
        ...prev,
        status: 'waiting_for_approval',
        approval_required: true,
        approval_stage: metadata?.approval_stage || 'architecture',
        approval_request: metadata?.approval_request || prev.approval_request || {},
        progress: progress ?? prev.progress,
      } : prev);
      return;
    }

    if (type === 'approval_approved' || type === 'approval_rejected') {
      setGeneration((prev) => prev ? {
        ...prev,
        status: 'running',
        approval_required: false,
        approval_status: type === 'approval_approved' ? 'approved' : 'rejected',
      } : prev);
      return;
    }

    if (!agent) return;

    setGeneration((prev) => {
      if (!prev) return prev;
      const agents = [...(prev.agents || [])];
      const idx = agents.findIndex((a) => a.name === agent);
      if (idx >= 0) {
        agents[idx] = { ...agents[idx] };
        if (type === 'agent_started') agents[idx].status = 'running';
        if (type === 'agent_completed') agents[idx].status = 'completed';
        if (type === 'agent_failed') agents[idx].status = 'failed';
        if (type === 'agent_retrying') agents[idx].status = 'retrying';
      }
      return {
        ...prev,
        agents,
        current_agent: type === 'agent_started' ? agent : prev.current_agent,
        progress: progress ?? prev.progress,
      };
    });

  }, []);

  // ----- Connect stream -----
  useEffect(() => {
    if (!genId || genId === 'unknown') return;

    const stream = connectGenerationStream(genId, {
      onSnapshot: (snap) => {
        applySnapshot(snap);
        setConnectionMode((m) => m === 'sse' ? 'sse' : 'polling');
      },
      onEvent: (evt) => {
        if (evt.type !== 'snapshot') applyEvent(evt);
      },
      onAgentStarted: (_, evt) => applyEvent({ ...evt, type: 'agent_started' }),
      onAgentCompleted: (_, evt) => applyEvent({ ...evt, type: 'agent_completed' }),
      onAgentFailed: (_, evt) => applyEvent({ ...evt, type: 'agent_failed' }),
      onGenerationCompleted: (evt) => {
        applyEvent({ ...evt, type: 'generation_completed' });
        if (!completedFiredRef.current) {
          completedFiredRef.current = true;
          setShowCompleteModal(true);
        }
        setGeneration((prev) => prev ? { ...prev, status: 'completed', progress: 100 } : prev);
      },
      onGenerationFailed: (evt) => {
        applyEvent({ ...evt, type: 'generation_failed' });
        if (!completedFiredRef.current) {
          completedFiredRef.current = true;
          setShowFailModal(true);
        }
        setGeneration((prev) => prev ? { ...prev, status: 'failed' } : prev);
      },
      onError: (err) => {
        console.warn('[Generation] stream error:', err.message);
        setConnectionMode('polling');
      },
    });

    // Detect if SSE came alive
    const sseCheck = setInterval(() => {
      setConnectionMode((m) => m === 'connecting' ? 'polling' : m);
    }, 3500);

    streamRef.current = stream;
    return () => {
      stream.disconnect();
      clearInterval(sseCheck);
    };
  }, [genId, applySnapshot, applyEvent]);

  // ----- Cancel -----
  const handleCancel = useCallback(async () => {
    await cancelGeneration(genId);
    setGeneration((prev) => prev ? { ...prev, status: 'cancelled' } : prev);
  }, [genId]);

  // ----- HITL Approval & Rejection Handlers -----
  const [isApproving, setIsApproving] = useState(false);

  const handleApproveWorkflow = useCallback(async (notes) => {
    setIsApproving(true);
    try {
      await approveGeneration(genId, notes);
      setGeneration((prev) => prev ? {
        ...prev,
        status: 'running',
        approval_required: false,
        approval_status: 'approved'
      } : prev);
    } catch (err) {
      console.error('Approval failed:', err);
      throw err;
    } finally {
      setIsApproving(false);
    }
  }, [genId]);

  const handleRejectWorkflow = useCallback(async (feedback) => {
    setIsApproving(true);
    try {
      await rejectGeneration(genId, feedback);
      setGeneration((prev) => prev ? {
        ...prev,
        status: 'running',
        approval_required: false,
        approval_status: 'rejected'
      } : prev);
    } catch (err) {
      console.error('Rejection failed:', err);
      throw err;
    } finally {
      setIsApproving(false);
    }
  }, [genId]);

  // ----- Navigation -----
  const handleOpenWorkspace = useCallback(() => {
    if (setView) setView('code');
    else window.location.href = `/projects/${genId}/code`;
  }, [genId, setView]);

  const handleViewQuality = useCallback(() => {
    if (setView) setView('metrics');
    else window.location.href = `/projects/${genId}/quality`;
  }, [genId, setView]);

  // ----- Derived state -----
  const status = generation?.status || 'queued';
  const progress = generation?.progress ?? 0;
  const currentAgent = generation?.current_agent || null;
  const agentsMap = buildAgentsMap(generation?.agents || []);
  const completedCount = Object.values(agentsMap).filter((a) => a.status === 'completed').length;
  const totalCount = (generation?.agents || []).length || AGENT_ORDER.length;
  const logs = buildLogsFromEvents(events);
  const projectName = generation?.project_id || genId;
  const isWaitingApproval = status === 'waiting_for_approval' || generation?.approval_required === true;
  const approvalRequest = generation?.approval_request || {};
  const approvalStage = generation?.approval_stage || (approvalRequest.stage || 'architecture');

  if (loading) {
    return (
      <div className="min-h-screen bg-[#08090D] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">Connecting to generation engine…</p>
          <p className="text-slate-600 text-xs font-mono">{genId}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#08090D] text-slate-100 font-sans selection:bg-cyan-500 selection:text-white">
      <ProjectHeader
        projectName={projectName}
        generationId={genId}
        status={status}
        onCancel={handleCancel}
      />


      {/* SSE / Polling indicator */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-2 flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${connectionMode === 'sse' ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`} />
        <span className="text-xs text-slate-500">
          {connectionMode === 'sse' ? 'Live (SSE)' : connectionMode === 'polling' ? 'Live (polling)' : 'Connecting…'}
        </span>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

        {/* Human-in-the-Loop Approval Panel */}
        {isWaitingApproval && (
          <ApprovalPanel
            approvalRequest={approvalRequest}
            stage={approvalStage}
            onApprove={handleApproveWorkflow}
            onReject={handleRejectWorkflow}
            isSubmitting={isApproving}
          />
        )}

        {/* Completion modal */}
        {showCompleteModal && (
          <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-6 text-center space-y-4">
            <div className="text-4xl">🎉</div>
            <h2 className="text-xl font-bold text-emerald-300">Project Generation Complete</h2>
            <p className="text-slate-400 text-sm">
              Your project has been fully generated and is ready to explore.
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              <button
                onClick={handleOpenWorkspace}
                className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-sm font-medium transition"
              >
                Open Code Workspace
              </button>
              <button
                onClick={handleViewQuality}
                className="px-5 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition"
              >
                Quality Report
              </button>
            </div>
          </div>
        )}

        {/* Failure display */}
        {showFailModal && (
          <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-6 text-center space-y-4">
            <div className="text-4xl">⚠️</div>
            <h2 className="text-xl font-bold text-red-300">Generation Failed</h2>
            <p className="text-slate-400 text-sm">
              {generation?.error || 'An error occurred during generation. Please try again.'}
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              <button
                onClick={() => window.location.href = '/create'}
                className="px-5 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition"
              >
                Retry Generation
              </button>
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="px-5 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        )}

        {/* Autonomous Debug -> Fix -> Retest Activity Panel */}
        {(status === 'repairing' || isWaitingApproval && approvalStage === 'debug_escalation' || generation?.human_intervention_required) && (
          <DebugActivityPanel
            active={status === 'repairing' || isWaitingApproval && approvalStage === 'debug_escalation'}
            debugState={generation?.state || generation || {}}
            testResults={generation?.test_results || {}}
            currentCycle={generation?.retry_count || (generation?.agents?.find(a => a.name === 'debug')?.retry_count || 0) + 1}
            maxCycles={3}
            humanInterventionRequired={Boolean(generation?.human_intervention_required || approvalStage === 'debug_escalation')}
            onProvideGuidance={(text) => handleRejectWorkflow(text)}
            onRetry={() => handleRejectWorkflow('Retry autonomous debug cycle')}
            onProceedAnyway={() => handleApproveWorkflow()}
          />
        )}


        {/* Completion actions (non-modal variant) */}
        {status === 'completed' && !showCompleteModal && (
          <CompletionActions
            generationId={genId}
            onOpenWorkspace={handleOpenWorkspace}
            onViewQualityReport={handleViewQuality}
          />
        )}

        {/* Overall Progress Bar */}
        <ProgressBar
          completedCount={completedCount}
          totalCount={totalCount}
          progress={progress}
        />

        {/* Main 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left: Agent Pipeline */}
          <div className="lg:col-span-5">
            <AgentPipeline agentsMap={agentsMap} />
          </div>

          {/* Right: Active Agent + Live Logs */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            <AgentCard currentAgent={currentAgent} progress={progress} />
            <AgentLogs logs={logs} />
          </div>
        </div>
      </main>
    </div>
  );
}
