import React, { useState, useEffect } from 'react';
import { fetchObservabilityData } from '../services/observability';
import { FaChartLine, FaCheckCircle, FaSpinner, FaServer, FaMicrochip, FaDatabase, FaExchangeAlt, FaExclamationTriangle, FaClock, FaBolt, FaHistory } from 'react-icons/fa';


export default function ObservabilityDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const res = await fetchObservabilityData();
      setData(res);
      setLoading(false);
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-white font-sans flex flex-col items-center justify-center p-6 space-y-4">
        <FaSpinner className="w-8 h-8 text-cyan-400 animate-spin" />
        <h3 className="text-base font-bold">Loading System Observability Telemetry</h3>
      </div>
    );
  }

  const health = data.health || {};
  const genMetrics = data.generation_metrics || {};
  const agentPerf = data.agent_performance || [];
  const timeline = data.agent_timeline || [];
  const modelUsage = data.model_usage || {};
  const errorAnalytics = data.error_analytics || {};
  const failedGens = data.failed_generations || [];
  const relMetrics = data.reliability_metrics || {};
  const cacheMetrics = data.cache_metrics || {};
  const parallelMetrics = data.parallel_metrics || {};

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 selection:bg-cyan-500 selection:text-white">
      {/* Header */}
      <div className="max-w-7xl mx-auto border-b border-slate-800 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
            <FaChartLine className="text-cyan-400" /> AIForge System Observability & Telemetry
          </h1>
          <p className="text-xs text-slate-400 mt-1">Real-time metrics, multi-agent latencies, LLM token usage, and reliability analytics.</p>
        </div>

        <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-mono font-bold flex items-center gap-1.5">
          <FaCheckCircle className="w-3 h-3" /> System Operational
        </span>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* System Health Probes */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-xs">
          {Object.entries(health).map(([svc, st]) => (
            <div key={svc} className="bg-slate-950 border border-slate-800 p-3.5 rounded-2xl flex items-center justify-between">
              <span className="text-slate-400 uppercase font-sans text-[11px]">{svc}</span>
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <FaCheckCircle className="w-3 h-3" /> {st}
              </span>
            </div>
          ))}
        </div>

        {/* Generation High-Level Telemetry Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-sans">
          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl">
            <span className="text-xs text-slate-400 font-medium block mb-1">Total Generations</span>
            <div className="text-2xl font-black font-mono text-white">{genMetrics.total_generations?.toLocaleString()}</div>
            <span className="text-[10px] text-emerald-400 font-mono font-bold mt-1 block">
              Success Rate: {genMetrics.success_rate_pct}%
            </span>
          </div>

          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl">
            <span className="text-xs text-slate-400 font-medium block mb-1">Average Generation Time</span>
            <div className="text-2xl font-black font-mono text-cyan-400">{genMetrics.avg_generation_time}</div>
            <span className="text-[10px] text-slate-500 font-mono mt-1 block">
              Median: {genMetrics.median_generation_time}
            </span>
          </div>

          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl">
            <span className="text-xs text-slate-400 font-medium block mb-1">P95 Generation Latency</span>
            <div className="text-2xl font-black font-mono text-amber-400">{genMetrics.p95_generation_time}</div>
            <span className="text-[10px] text-slate-500 font-mono mt-1 block">95th Percentile Bound</span>
          </div>

          <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl">
            <span className="text-xs text-slate-400 font-medium block mb-1">Parallel Efficiency</span>
            <div className="text-2xl font-black font-mono text-purple-400">{parallelMetrics.parallel_efficiency_pct}%</div>
            <span className="text-[10px] text-purple-400 font-mono mt-1 block">Saved {parallelMetrics.time_saved}</span>
          </div>
        </div>

        {/* Agent Performance Table */}
        <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3 flex items-center gap-2">
            <FaMicrochip className="text-cyan-400" /> Multi-Agent Execution Performance Matrix

          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase">
                  <th className="pb-2">Agent</th>
                  <th className="pb-2">Executions</th>
                  <th className="pb-2">Success Rate</th>
                  <th className="pb-2">Avg Duration</th>
                  <th className="pb-2 text-right">Failures</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {agentPerf.map((ag, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/50">
                    <td className="py-3 font-bold text-white font-sans">{ag.agent}</td>
                    <td className="py-3 text-slate-300">{ag.executions}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        ag.success_rate_pct >= 95 ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' : 'text-amber-400 bg-amber-500/10'
                      }`}>
                        {ag.success_rate_pct}%
                      </span>
                    </td>
                    <td className="py-3 text-cyan-400">{ag.avg_time_s}s</td>
                    <td className="py-3 text-right text-rose-400 font-bold">{ag.failures}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Execution Timeline & Model Tokens Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 font-sans">
          {/* Timeline Bar Visualizer */}
          <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3 flex items-center gap-2">
              <FaClock className="text-indigo-400" /> Parallel Execution Timeline (Per-Agent Durations)
            </h3>

            <div className="space-y-2.5 font-mono text-xs">
              {timeline.map((t, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-300 font-sans font-bold flex items-center gap-1.5">
                      {t.agent} {t.parallel && <span className="text-[10px] text-purple-400 bg-purple-500/10 px-1.5 py-0.2 rounded border border-purple-500/20 font-mono">PARALLEL</span>}
                    </span>
                    <span className="text-cyan-400">{t.duration_s}s</span>
                  </div>
                  <div className="h-3 bg-slate-900 rounded-lg overflow-hidden border border-slate-800">
                    <div
                      className={`h-full ${t.parallel ? 'bg-gradient-to-r from-purple-500 to-indigo-500' : 'bg-gradient-to-r from-cyan-500 to-emerald-500'}`}
                      style={{ width: `${Math.min(100, (t.duration_s / 90) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* LLM Usage & Performance */}
          <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3 flex items-center gap-2">
              <FaExchangeAlt className="text-emerald-400" /> LLM & Token Telemetry ({modelUsage.model})
            </h3>

            <div className="grid grid-cols-2 gap-3 font-mono text-xs">
              <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
                <span className="text-slate-400 text-[10px] font-sans block mb-1">Total LLM Requests</span>
                <span className="text-white font-bold text-base">{modelUsage.requests?.toLocaleString()}</span>
              </div>
              <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
                <span className="text-slate-400 text-[10px] font-sans block mb-1">Tokens (In / Out)</span>
                <span className="text-cyan-400 font-bold text-base">{modelUsage.input_tokens} / {modelUsage.output_tokens}</span>
              </div>
              <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
                <span className="text-slate-400 text-[10px] font-sans block mb-1">Avg Tokens / Gen</span>
                <span className="text-white font-bold text-base">{modelUsage.avg_tokens_per_gen}</span>
              </div>
              <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl">
                <span className="text-slate-400 text-[10px] font-sans block mb-1">LLM P50 / P95 Latency</span>
                <span className="text-amber-400 font-bold text-base">{modelUsage.p50_s}s / {modelUsage.p95_s}s</span>
              </div>
            </div>

            {/* Cache Analytics */}
            <div className="pt-2 border-t border-slate-800/80 font-mono text-xs flex items-center justify-between">
              <span className="text-slate-400 font-sans">Prompt Cache Hit Rate:</span>
              <span className="text-emerald-400 font-bold">{cacheMetrics.hit_rate_pct}% ({cacheMetrics.cache_hits} hits)</span>
            </div>
          </div>
        </div>

        {/* Failed Generation Logs */}
        <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3 flex items-center gap-2">
            <FaExclamationTriangle className="text-rose-400" /> Failed Generation Diagnostics
          </h3>

          <div className="space-y-2 font-mono text-xs">
            {failedGens.map((fg, idx) => (
              <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-rose-400">{fg.generation_id}</span>
                  <span className="px-2 py-0.5 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[10px] font-bold rounded">
                    Stage: {fg.failed_stage}
                  </span>
                  <span className="text-slate-300 font-sans text-xs">{fg.reason}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
