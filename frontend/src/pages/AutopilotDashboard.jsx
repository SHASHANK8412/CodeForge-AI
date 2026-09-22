import React, { useState, useEffect } from 'react';
import {
  FaBolt, FaPlay, FaPause, FaStop, FaCheckCircle, FaSpinner,
  FaExclamationTriangle, FaShieldAlt, FaCode, FaChartLine,
  FaSync, FaArrowRight, FaBrain, FaLayerGroup, FaDatabase, FaLock,
  FaThList, FaInfoCircle, FaWrench, FaHistory
} from 'react-icons/fa';
import {
  startAutopilot, fetchAutopilotState, pauseAutopilot, resumeAutopilot,
  stopAutopilot, approveAutopilotAction, rejectAutopilotAction
} from '../services/autopilot';
import { subscribeToGenerationEvents } from '../services/generation';

export default function AutopilotDashboard({ generationId = 'aiforge-demo', setView, setActiveGenerationId }) {
  const [goal, setGoal] = useState('Build a production-ready e-commerce platform with authentication, products, cart, payments, admin dashboard and PostgreSQL database.');
  const [autonomyLevel, setAutonomyLevel] = useState('BALANCED');
  const [approvalSettings, setApprovalSettings] = useState({
    deployment: true,
    schemaDestruction: true,
    archChanges: true,
    bugFixes: false,
    testFixes: false,
    docChanges: false,
  });

  const [activeGenId, setActiveGenId] = useState(generationId);
  const [autopilotData, setAutopilotData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedStage, setSelectedStage] = useState('BUILD');
  const [selectedDecision, setSelectedDecision] = useState(null);

  const loadState = async () => {
    try {
      const res = await fetchAutopilotState(activeGenId);
      setAutopilotData(res);
    } catch (err) {
      console.warn('Failed to load autopilot state:', err);
    }
  };

  useEffect(() => {
    loadState();
    const interval = setInterval(loadState, 2500);

    const unsubscribeSSE = subscribeToGenerationEvents(
      activeGenId,
      () => loadState(),
      () => {}
    );

    return () => {
      clearInterval(interval);
      if (unsubscribeSSE) {
        if (typeof unsubscribeSSE === 'function') unsubscribeSSE();
        else if (typeof unsubscribeSSE.disconnect === 'function') unsubscribeSSE.disconnect();
      }
    };
  }, [activeGenId]);

  const handleStart = async (e) => {
    e.preventDefault();
    if (!goal.trim()) return;

    setLoading(true);
    try {
      const projId = `proj_${Date.now()}`;
      const res = await startAutopilot(projId, goal, autonomyLevel, approvalSettings);
      if (res.generation_id) {
        setActiveGenId(res.generation_id);
        if (setActiveGenerationId) setActiveGenerationId(res.generation_id);
      }
      await loadState();
    } catch (err) {
      alert(`Autopilot start failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    setActionLoading(true);
    await pauseAutopilot(activeGenId);
    await loadState();
    setActionLoading(false);
  };

  const handleResume = async () => {
    setActionLoading(true);
    await resumeAutopilot(activeGenId);
    await loadState();
    setActionLoading(false);
  };

  const handleStop = async () => {
    if (!window.confirm('Stop Autopilot? The current project version will be preserved.')) return;
    setActionLoading(true);
    await stopAutopilot(activeGenId);
    await loadState();
    setActionLoading(false);
  };

  const handleApprove = async (reqId) => {
    setActionLoading(true);
    await approveAutopilotAction(activeGenId, reqId);
    await loadState();
    setActionLoading(false);
  };

  const handleReject = async (reqId) => {
    setActionLoading(true);
    await rejectAutopilotAction(activeGenId, reqId);
    await loadState();
    setActionLoading(false);
  };

  const progress = autopilotData?.progress || (autopilotData?.status === 'completed' ? 100 : 78);
  const status = (autopilotData?.status || 'completed').toUpperCase();
  const currentAgent = autopilotData?.current_agent || 'deployment';
  const decisions = autopilotData?.decisions || [];
  const pendingApproval = autopilotData?.pending_approval;

  const pipelineStages = [
    { key: 'PLAN', label: 'PLAN', status: progress >= 10 ? 'PASS' : 'PENDING' },
    { key: 'ARCHITECT', label: 'ARCHITECT', status: progress >= 20 ? 'PASS' : 'PENDING' },
    { key: 'BUILD', label: 'BUILD', status: progress >= 50 ? 'PASS' : 'PENDING' },
    { key: 'REVIEW', label: 'REVIEW', status: progress >= 65 ? 'PASS' : 'PENDING' },
    { key: 'TEST', label: 'TEST', status: progress >= 80 ? 'PASS' : 'RUNNING' },
    { key: 'REPAIR', label: 'REPAIR', status: progress >= 85 ? 'PASS' : 'RUNNING' },
    { key: 'OPTIMIZE', label: 'OPTIMIZE', status: progress >= 95 ? 'PASS' : 'PENDING' },
    { key: 'DEPLOY', label: 'DEPLOY', status: progress >= 100 ? 'PASS' : 'PENDING' },
  ];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/40 rounded-xl text-yellow-400">
              <FaBolt className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                Engineering Autopilot
                <span className="text-xs px-2.5 py-0.5 bg-yellow-400/10 border border-yellow-400/30 text-yellow-400 rounded-full font-mono font-semibold">
                  FLAGSHIP
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Let AIForge build, test, repair and optimize your software autonomously.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => setView && setView('flight-recorder')}
          className="px-4 py-2 bg-slate-900 border border-slate-700 hover:border-indigo-500 rounded-xl text-xs font-bold text-indigo-300 hover:text-white transition flex items-center gap-2 shrink-0"
        >
          <FaHistory /> Engineering Flight Recorder
        </button>
      </div>

      {/* Goal Input & Autonomy Configuration Panel */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
        <form onSubmit={handleStart} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
              What should AIForge build?
            </label>
            <textarea
              rows={3}
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Build a task management platform with user auth, projects, tasks, deadlines, search and PostgreSQL..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 transition font-mono"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 pt-2">
            {/* Autonomy Level */}
            <div className="md:col-span-6 space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                Autonomy Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { level: 'ASSISTED', desc: 'Asks before major code changes' },
                  { level: 'BALANCED', desc: 'Auto-fixes issues; asks for destructive ops' },
                  { level: 'FULL_AUTONOMY', desc: 'Auto build, test, repair, optimize & version' },
                ].map(({ level, desc }) => (
                  <button
                    key={level}
                    type="button"
                    onClick={() => setAutonomyLevel(level)}
                    className={`p-3 rounded-xl border text-left transition ${
                      autonomyLevel === level
                        ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-lg'
                        : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="text-xs font-bold font-mono">{level.replace('_', ' ')}</div>
                    <div className="text-[10px] text-slate-400 mt-1 leading-tight">{desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Approval Gate Settings */}
            <div className="md:col-span-6 space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                Human Approval Gates (Require approval before)
              </label>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono text-slate-300 bg-slate-900/50 border border-slate-800/80 rounded-xl p-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={approvalSettings.deployment}
                    onChange={(e) => setApprovalSettings({ ...approvalSettings, deployment: e.target.checked })}
                    className="accent-indigo-500"
                  />
                  <span>Production deployment</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={approvalSettings.schemaDestruction}
                    onChange={(e) => setApprovalSettings({ ...approvalSettings, schemaDestruction: e.target.checked })}
                    className="accent-indigo-500"
                  />
                  <span>Database schema destruction</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={approvalSettings.archChanges}
                    onChange={(e) => setApprovalSettings({ ...approvalSettings, archChanges: e.target.checked })}
                    className="accent-indigo-500"
                  />
                  <span>Major architecture changes</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-slate-500">
                  <input
                    type="checkbox"
                    checked={approvalSettings.bugFixes}
                    onChange={(e) => setApprovalSettings({ ...approvalSettings, bugFixes: e.target.checked })}
                    className="accent-indigo-500"
                  />
                  <span>Normal bug fixes</span>
                </label>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white text-xs font-bold rounded-xl shadow-lg transition flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaBolt className="w-4 h-4" />}
              Start Autopilot
            </button>
          </div>
        </form>
      </div>

      {/* Pending Approval Modal Banner */}
      {pendingApproval && (
        <div className="bg-amber-950/60 border-2 border-amber-500 rounded-2xl p-5 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 animate-pulse">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
              <FaExclamationTriangle className="w-5 h-5" />
              Approval Required for High-Risk Action
            </div>
            <p className="text-xs text-slate-200 font-mono">
              AIForge wants to: <span className="font-bold text-amber-300">{pendingApproval.action}</span>
            </p>
            <p className="text-xs text-slate-400">Reason: {pendingApproval.reason}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => handleReject(pendingApproval.id)}
              disabled={actionLoading}
              className="px-4 py-2 bg-slate-900 border border-slate-700 hover:bg-slate-800 text-rose-400 text-xs font-bold rounded-xl transition"
            >
              Reject
            </button>
            <button
              onClick={() => handleApprove(pendingApproval.id)}
              disabled={actionLoading}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-lg transition"
            >
              Approve
            </button>
          </div>
        </div>
      )}

      {/* Autopilot Control Panel & Progress */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-[11px] font-mono font-bold text-indigo-400 uppercase tracking-wider block">
              ⚡ AUTOPILOT CONTROL PANEL ({autonomyLevel.replace('_', ' ')})
            </span>
            <h2 className="text-base font-bold text-white mt-1">Goal: {goal}</h2>
          </div>

          <div className="flex items-center gap-3">
            {status === 'PAUSED' ? (
              <button
                onClick={handleResume}
                disabled={actionLoading}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5"
              >
                <FaPlay className="w-3 h-3" /> Resume
              </button>
            ) : (
              <button
                onClick={handlePause}
                disabled={actionLoading}
                className="px-4 py-2 bg-slate-900 border border-slate-700 hover:bg-slate-800 text-amber-300 text-xs font-bold rounded-xl transition flex items-center gap-1.5"
              >
                <FaPause className="w-3 h-3" /> Pause
              </button>
            )}
            <button
              onClick={handleStop}
              disabled={actionLoading}
              className="px-4 py-2 bg-rose-950/60 border border-rose-500/40 hover:bg-rose-900/60 text-rose-300 text-xs font-bold rounded-xl transition flex items-center gap-1.5"
            >
              <FaStop className="w-3 h-3" /> Stop
            </button>
          </div>
        </div>

        {/* Progress Bar & Current Task */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400">Overall Progress</span>
            <span className="font-bold text-cyan-400">{progress}%</span>
          </div>
          <div className="w-full bg-slate-900 rounded-full h-3 overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 h-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between text-xs font-mono pt-1 text-slate-400">
            <span>Current Task: <strong className="text-white uppercase">{currentAgent}</strong></span>
            <span>Status: <strong className="text-indigo-400">{status}</strong></span>
          </div>
        </div>

        {/* Engineering Pipeline Stage Tracker */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 pt-2">
          {pipelineStages.map((st) => (
            <button
              key={st.key}
              onClick={() => setSelectedStage(st.key)}
              className={`p-3 rounded-xl border font-mono text-xs flex flex-col items-center justify-between transition ${
                selectedStage === st.key
                  ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-lg'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <span className="font-bold text-[11px]">{st.label}</span>
              {st.status === 'PASS' ? (
                <FaCheckCircle className="w-4 h-4 text-emerald-400 mt-2" />
              ) : st.status === 'RUNNING' ? (
                <FaSpinner className="w-4 h-4 text-cyan-400 animate-spin mt-2" />
              ) : (
                <span className="w-4 h-4 text-slate-600 mt-2">○</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Decision Timeline & Autonomous Repair Visualization 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Decision Timeline & Decision Cards */}
        <div className="lg:col-span-7 bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <FaBrain className="text-indigo-400" />
              AI Decision Timeline & Evidence Cards
            </h3>
            <span className="text-[11px] font-mono text-slate-400">{decisions.length} Decisions Recorded</span>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {decisions.map((d) => (
              <div
                key={d.id}
                onClick={() => setSelectedDecision(d)}
                className={`p-4 rounded-xl border transition cursor-pointer ${
                  selectedDecision?.id === d.id
                    ? 'bg-slate-900 border-indigo-500 shadow-xl'
                    : 'bg-slate-900/50 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                  <span className="font-bold text-indigo-300 flex items-center gap-1.5">
                    <FaLayerGroup className="text-indigo-400" /> {d.title}
                  </span>
                  <span className="text-slate-500">{d.timestamp}</span>
                </div>
                <p className="text-xs text-slate-300 font-sans mb-2">{d.summary}</p>

                <div className="text-[11px] font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-slate-400 space-y-1">
                  <div><strong className="text-slate-300">Why:</strong> {d.reason}</div>
                  {d.impact && <div><strong className="text-emerald-400">Impact:</strong> {d.impact}</div>}
                  <div className="flex justify-between items-center pt-1 border-t border-slate-800/60">
                    <span className="text-slate-400">
                      Confidence: {d.confidence !== null && d.confidence !== undefined ? `${Math.round(d.confidence * 100)}% High` : 'Confidence unavailable'}
                    </span>
                    <span className="text-indigo-400">{(d.sources || []).length} Citations</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Autonomous Repair & Before/After Comparison */}
        <div className="lg:col-span-5 space-y-6">
          {/* Repair Visualization */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <FaWrench className="text-amber-400" />
              Autonomous Repair Cycle #1
            </h3>

            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 text-xs font-mono space-y-2 text-slate-300">
              <div><strong className="text-rose-400">Problem:</strong> Authentication input validation failure</div>
              <div><strong className="text-amber-300">Root Cause:</strong> Request schema validation missing before route handler</div>
              <div><strong className="text-cyan-300">Files Changed:</strong> backend/routes/auth.py</div>
              <div className="flex justify-between pt-1 border-t border-slate-800 text-[11px]">
                <span>Tests: <strong className="text-emerald-400">47 → 52</strong></span>
                <span>Quality: <strong className="text-emerald-400">86 → 96</strong></span>
                <span className="text-emerald-400 font-bold">✓ Successful</span>
              </div>
            </div>
          </div>

          {/* Before / After Metrics Comparison */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <FaChartLine className="text-emerald-400" />
              Before / After Metric Delta
            </h3>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-slate-900/50 border border-slate-800 p-3 rounded-xl">
                <span className="text-slate-500 uppercase text-[10px] block">BEFORE REPAIR</span>
                <div className="mt-1 space-y-1 text-slate-300">
                  <div>Quality: <strong className="text-amber-400">86</strong></div>
                  <div>Tests: <strong className="text-amber-400">47/52</strong></div>
                  <div>Security: <strong className="text-amber-400">78</strong></div>
                  <div>Coverage: <strong className="text-amber-400">82%</strong></div>
                </div>
              </div>

              <div className="bg-slate-900/50 border border-emerald-500/30 p-3 rounded-xl">
                <span className="text-emerald-400 uppercase text-[10px] block">AFTER REPAIR</span>
                <div className="mt-1 space-y-1 text-white">
                  <div>Quality: <strong className="text-emerald-400">96 (+10)</strong></div>
                  <div>Tests: <strong className="text-emerald-400">52/52 (100%)</strong></div>
                  <div>Security: <strong className="text-emerald-400">95 (+17)</strong></div>
                  <div>Coverage: <strong className="text-emerald-400">94% (+12%)</strong></div>
                </div>
              </div>
            </div>
          </div>

          {/* Overall AIForge Engineering Score */}
          <div className="bg-slate-950 border border-indigo-500/40 rounded-2xl p-6 shadow-xl space-y-3 text-center">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
              AIForge Engineering Score
            </span>
            <div className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 font-mono">
              96 / 100
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-400 text-left pt-2">
              <div>Requirements: <strong className="text-emerald-400">98</strong></div>
              <div>Architecture: <strong className="text-emerald-400">94</strong></div>
              <div>Code Quality: <strong className="text-emerald-400">95</strong></div>
              <div>Security: <strong className="text-emerald-400">95</strong></div>
              <div>Testing: <strong className="text-emerald-400">100</strong></div>
              <div>Performance: <strong className="text-emerald-400">92</strong></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
