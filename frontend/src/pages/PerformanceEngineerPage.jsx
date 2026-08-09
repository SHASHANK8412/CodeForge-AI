import React, { useState, useEffect } from 'react';
import { FaBolt, FaSpinner, FaTachometerAlt, FaDatabase, FaLayerGroup, FaExclamationTriangle, FaCheckCircle, FaTimesCircle, FaChartLine, FaUndo, FaMagic } from 'react-icons/fa';
import {
  fetchPerformanceReport,
  profilePerformance,
  optimizePerformanceAutomatically,
  fetchPerformanceHistory,
  simulatePerformanceWhatIf
} from '../services/performance';

export default function PerformanceEngineerPage({ projectId = 'aiforge-demo' }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profiling, setProfiling] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizationDiff, setOptimizationDiff] = useState(null);
  const [history, setHistory] = useState([]);
  const [whatIfInput, setWhatIfInput] = useState('Add Redis caching for product catalog queries');
  const [whatIfResult, setWhatIfResult] = useState(null);

  useEffect(() => {
    loadAllData();
  }, [projectId]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [repRes, histRes] = await Promise.all([
        fetchPerformanceReport(projectId),
        fetchPerformanceHistory(projectId)
      ]);
      if (repRes?.report) setReport(repRes.report);
      if (histRes?.history?.snapshots) setHistory(histRes.history.snapshots);
    } catch (err) {
      console.warn('Failed to load performance data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleProfile = async () => {
    setProfiling(true);
    try {
      const res = await profilePerformance(projectId);
      if (res?.report) setReport(res.report);
      setOptimizationDiff(null);
    } catch (err) {
      alert(`Profiling failed: ${err.message}`);
    } finally {
      setProfiling(false);
    }
  };

  const handleOptimize = async (simulateRegression = false) => {
    setOptimizing(true);
    try {
      const res = await optimizePerformanceAutomatically(projectId, simulateRegression);
      if (res?.diff) {
        setOptimizationDiff(res.diff);
        await loadAllData();
      }
    } catch (err) {
      alert(`Optimization failed: ${err.message}`);
    } finally {
      setOptimizing(false);
    }
  };

  const handleSimulateWhatIf = async (e) => {
    e.preventDefault();
    try {
      const res = await simulatePerformanceWhatIf(projectId, whatIfInput);
      setWhatIfResult(res.simulation);
    } catch (err) {
      alert(`Simulation failed: ${err.message}`);
    }
  };

  const snap = report?.latest_snapshot || {};
  const bottlenecks = report?.bottlenecks || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-amber-600/20 border border-amber-500/40 rounded-xl text-amber-400">
            <FaBolt className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              ⚡ Autonomous Performance Engineer
              <span className="text-xs px-2.5 py-0.5 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-full font-mono">
                PROFILER & AUTO-REPAIR V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              API Latency Profiling, N+1 Query Detection, Multi-Metric Verification & Auto-Rollback on Regression.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleProfile}
            disabled={profiling}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5 shadow"
          >
            {profiling ? <FaSpinner className="animate-spin" /> : <FaTachometerAlt />} Re-Profile Metrics
          </button>
          <button
            onClick={() => handleOptimize(false)}
            disabled={optimizing}
            className="px-5 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl shadow transition flex items-center gap-2 disabled:opacity-50"
          >
            {optimizing ? <FaSpinner className="w-3.5 h-3.5 animate-spin" /> : <FaMagic className="w-3.5 h-3.5" />}
            Optimize Automatically
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-400 font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-amber-400 mr-2" /> Collecting real performance metrics…
        </div>
      ) : (
        <>
          {/* OVERALL PERFORMANCE METRICS CARD */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl font-extrabold text-amber-400 font-mono">
                  {report?.overall_performance_score || 88} / 100
                </span>
                <div>
                  <h3 className="text-sm font-bold text-white uppercase font-mono">Overall System Health Score</h3>
                  <span className="text-[10px] text-slate-400">Based on Latency, DB Queries, Bundle Size & Memory</span>
                </div>
              </div>

              <button
                onClick={() => handleOptimize(true)}
                className="px-3.5 py-1.5 bg-rose-950/40 hover:bg-rose-900/40 border border-rose-500/40 text-rose-300 text-xs font-mono font-bold rounded-xl transition flex items-center gap-1.5"
              >
                <FaUndo /> Simulate Regression & Test Rollback
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-6 gap-3 font-mono text-center">
              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase block">API Latency</span>
                <span className={`text-lg font-extrabold ${snap.api_latency_ms > 200 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {snap.api_latency_ms}ms
                </span>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase block">P95 Latency</span>
                <span className="text-lg font-extrabold text-white">{snap.p95_latency_ms}ms</span>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase block">Throughput</span>
                <span className="text-lg font-extrabold text-cyan-400">{snap.throughput_req_sec} req/s</span>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase block">DB Queries/Req</span>
                <span className={`text-lg font-extrabold ${snap.db_query_count > 15 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {snap.db_query_count}
                </span>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase block">JS Bundle Size</span>
                <span className="text-lg font-extrabold text-purple-400">{snap.bundle_size_mb}MB</span>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 p-3 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase block">Memory Usage</span>
                <span className="text-lg font-extrabold text-indigo-400">{snap.memory_usage_mb}MB</span>
              </div>
            </div>
          </div>

          {/* MULTI-METRIC OPTIMIZATION DIFF INSPECTOR */}
          {optimizationDiff && (
            <div className={`p-6 rounded-2xl border-2 shadow-2xl space-y-4 font-mono ${
              optimizationDiff.decision === 'KEEP'
                ? 'bg-slate-950 border-emerald-500/60'
                : 'bg-rose-950/30 border-rose-500/60'
            }`}>
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <span className={`text-xs font-bold uppercase tracking-wider ${
                  optimizationDiff.decision === 'KEEP' ? 'text-emerald-400' : 'text-rose-400'
                }`}>
                  {optimizationDiff.decision === 'KEEP' ? '✓ OPTIMIZATION RETAINED' : '❌ PERFORMANCE REGRESSION DETECTED — AUTOMATICALLY ROLLED BACK'}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  Latency Improvement: {optimizationDiff.latency_improvement_percent}%
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center text-xs">
                <div className="bg-slate-900 p-3 rounded-xl">
                  <span className="text-[9px] text-slate-400 block uppercase">API Latency</span>
                  <span className="text-white font-bold">{optimizationDiff.baseline_snapshot.api_latency_ms}ms ➔ {optimizationDiff.optimized_snapshot.api_latency_ms}ms</span>
                </div>
                <div className="bg-slate-900 p-3 rounded-xl">
                  <span className="text-[9px] text-slate-400 block uppercase">DB Queries</span>
                  <span className="text-white font-bold">{optimizationDiff.baseline_snapshot.db_query_count} ➔ {optimizationDiff.optimized_snapshot.db_query_count}</span>
                </div>
                <div className="bg-slate-900 p-3 rounded-xl">
                  <span className="text-[9px] text-slate-400 block uppercase">Unit + Security</span>
                  <span className="text-emerald-400 font-bold">{optimizationDiff.unit_tests_status} | {optimizationDiff.security_status}</span>
                </div>
                <div className="bg-slate-900 p-3 rounded-xl">
                  <span className="text-[9px] text-slate-400 block uppercase">Browser Tests</span>
                  <span className="text-emerald-400 font-bold">{optimizationDiff.browser_status}</span>
                </div>
              </div>
            </div>
          )}

          {/* BOTTLENECKS LIST & WHAT-IF SIMULATOR GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-sans">
            {/* Bottlenecks Column */}
            <div className="lg:col-span-2 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-2">
                <FaExclamationTriangle className="text-amber-400" /> Detected Performance Bottlenecks ({bottlenecks.length})
              </h3>

              <div className="space-y-3 font-mono text-xs">
                {bottlenecks.map((b) => (
                  <div key={b.bottleneck_id} className="p-4 bg-slate-950/70 border border-slate-800 rounded-2xl space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white font-sans text-sm">{b.name}</span>
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                        b.severity === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      }`}>
                        {b.severity}
                      </span>
                    </div>

                    <p className="text-slate-300 font-sans text-xs">{b.impact_summary}</p>

                    <div className="text-[10px] text-slate-400 space-y-0.5 pt-1 border-t border-slate-800/80 font-mono">
                      <div>Affected Files: {b.affected_files.join(', ')}</div>
                      <div>Evidence: {b.evidence}</div>
                      <div className="text-cyan-400 font-sans mt-1">💡 Recommendation: {b.recommendation}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Performance What-If Simulator Sidebar */}
            <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4 font-mono text-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-2">
                Performance What-If Simulator
              </h3>

              <form onSubmit={handleSimulateWhatIf} className="space-y-3">
                <label className="text-[10px] text-slate-400 uppercase block">Simulate Optimization Impact</label>
                <input
                  type="text"
                  value={whatIfInput}
                  onChange={(e) => setWhatIfInput(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-white outline-none focus:border-amber-500"
                />
                <button
                  type="submit"
                  className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow transition"
                >
                  Simulate Impact
                </button>
              </form>

              {whatIfResult && (
                <div className="p-3 bg-slate-900 border border-amber-500/30 rounded-xl space-y-2 text-[11px] font-sans">
                  <div className="font-bold text-amber-400 font-mono text-[9px] uppercase">Simulation Result</div>
                  <div className="text-slate-200">Expected Latency Reduction: -{whatIfResult.expected_latency_reduction_ms}ms</div>
                  <div className="text-slate-200">Throughput Gain: +{whatIfResult.expected_throughput_gain_percent}%</div>
                  <div className="text-emerald-400 font-mono text-[10px] mt-1">{whatIfResult.security_impact}</div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
