import React, { useState, useEffect } from 'react';
import { FaBug, FaWrench, FaCheckCircle, FaExclamationTriangle, FaRedo, FaServer, FaHistory, FaPercentage, FaSync, FaShieldAlt } from 'react-icons/fa';

export default function DebugDashboard({ projectId = 'debug_proj' }) {
  const [metrics, setMetrics] = useState({
    errors_found: 0,
    errors_fixed: 0,
    retries_used: 0,
    average_confidence: 100,
    build_success_pct: 100,
    recent_history: []
  });

  const [timeline, setTimeline] = useState({
    stages: [
      { name: 'Planning', status: 'COMPLETED', icon: '✔' },
      { name: 'Architecture', status: 'COMPLETED', icon: '✔' },
      { name: 'Frontend', status: 'COMPLETED', icon: '✔' },
      { name: 'Backend', status: 'COMPLETED', icon: '✔' },
      { name: 'Testing', status: 'FAILED', icon: '❌' },
      { name: 'Debugging', status: 'RUNNING', icon: '⏳' }
    ],
    current_error: 'ModuleNotFoundError: No module named fastapi',
    current_fix: 'pip install fastapi',
    retry_count: 1,
    confidence: 94
  });

  const [loading, setLoading] = useState(false);

  const fetchSelfHealingData = async () => {
    setLoading(true);
    try {
      const resMet = await fetch('http://127.0.0.1:8000/api/v1/self-healing/metrics');
      if (resMet.ok) {
        const dataMet = await resMet.json();
        if (dataMet.metrics) setMetrics(dataMet.metrics);
      }

      const resTime = await fetch(`http://127.0.0.1:8000/api/v1/self-healing/timeline/${projectId}`);
      if (resTime.ok) {
        const dataTime = await resTime.json();
        if (dataTime.timeline_data?.timeline) setTimeline(dataTime.timeline_data.timeline);
      }
    } catch (err) {
      console.log('Using default self-healing dashboard state:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSelfHealingData();
  }, [projectId]);

  const handleTriggerPipeline = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/self-healing/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error_log: "ModuleNotFoundError: No module named 'fastapi'",
          project_id: projectId
        })
      });
      if (res.ok) {
        fetchSelfHealingData();
      }
    } catch (err) {
      console.error('Failed to trigger pipeline:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FaBug className="w-5 h-5 text-rose-400" />
          <div>
            <h3 className="text-sm font-bold tracking-wide text-white uppercase">
              Intelligent Error Detection & Self-Healing Pipeline (Day 42)
            </h3>
            <p className="text-[11px] text-slate-400">Autonomous debugging, root cause analysis & auto-retry engine</p>
          </div>
        </div>

        <button
          onClick={handleTriggerPipeline}
          disabled={loading}
          className="bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-semibold text-xs px-3.5 py-2 rounded-lg transition cursor-pointer flex items-center gap-1.5 shadow w-fit"
        >
          <FaRedo className={loading ? 'animate-spin' : ''} />
          {loading ? 'Running Self-Healing Pipeline...' : 'Run Self-Healing Pipeline'}
        </button>
      </div>

      {/* Error Timeline Component */}
      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 mb-5 font-mono text-xs">
        <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wide mb-3 flex items-center gap-2">
          <FaSync className="text-indigo-400" /> Error Pipeline Timeline
        </h4>

        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
          {timeline.stages.map((stg, idx) => (
            <div
              key={idx}
              className={`p-2.5 rounded-lg border text-center flex flex-col items-center justify-center transition-all ${
                stg.status === 'COMPLETED'
                  ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
                  : stg.status === 'FAILED'
                  ? 'bg-rose-950/40 border-rose-800/80 text-rose-300'
                  : 'bg-amber-950/40 border-amber-800/80 text-amber-300 animate-pulse'
              }`}
            >
              <span className="text-base mb-1">{stg.icon}</span>
              <span className="text-[11px] font-bold block">{stg.name}</span>
              <span className="text-[9px] uppercase tracking-wider opacity-80">{stg.status}</span>
            </div>
          ))}
        </div>

        {/* Live Status Row */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-slate-800/80 text-[11px]">
          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Current Error</span>
            <span className="text-rose-300 font-semibold truncate block">{timeline.current_error}</span>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Current Fix</span>
            <span className="text-emerald-300 font-semibold truncate block">{timeline.current_fix}</span>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Retry Count</span>
            <span className="text-amber-300 font-bold block">{timeline.retry_count} / 3 Attempts</span>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Confidence</span>
            <span className={`font-bold block ${timeline.confidence >= 60 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {timeline.confidence}% {timeline.confidence < 60 ? '(Aborted)' : ''}
            </span>
          </div>
        </div>
      </div>

      {/* Dashboard Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-5 font-mono text-xs">
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Errors Found</span>
          <span className="text-2xl font-extrabold text-white">{metrics.errors_found}</span>
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-emerald-400 uppercase font-bold block mb-1">Errors Fixed</span>
          <span className="text-2xl font-extrabold text-emerald-400">{metrics.errors_fixed}</span>
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-amber-400 uppercase font-bold block mb-1">Retries Used</span>
          <span className="text-2xl font-extrabold text-amber-400">{metrics.retries_used}</span>
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-center">
          <span className="text-[10px] text-indigo-400 uppercase font-bold block mb-1">Avg Confidence</span>
          <span className="text-2xl font-extrabold text-indigo-400">{metrics.average_confidence}%</span>
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-center col-span-2 sm:col-span-1">
          <span className="text-[10px] text-cyan-400 uppercase font-bold block mb-1">Build Success %</span>
          <span className="text-2xl font-extrabold text-cyan-400">{metrics.build_success_pct}%</span>
        </div>
      </div>

      {/* Error History Log Table */}
      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <FaHistory className="text-amber-400" /> Error History Log (backend/logs/error_history.json)
        </h4>

        <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
          {(!metrics.recent_history || metrics.recent_history.length === 0) ? (
            <div className="text-center py-6 text-slate-500 text-xs italic">
              No historical error events recorded yet. Click 'Run Self-Healing Pipeline' above.
            </div>
          ) : (
            metrics.recent_history.map((log, idx) => (
              <div key={idx} className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-between text-[11px]">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className={`font-bold px-1.5 py-0.5 rounded text-[9px] ${log.success ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'}`}>
                      {log.success ? 'PASSED' : 'FAILED'}
                    </span>
                    <span className="font-bold text-slate-200">{log.error}</span>
                  </div>
                  <p className="text-slate-400 text-[10px]">Fix: {log.solution}</p>
                </div>
                <div className="text-right">
                  <span className="text-indigo-300 font-bold block text-[10px]">{log.confidence}% Conf</span>
                  <span className="text-slate-500 text-[9px]">{log.time || 'recent'}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
