import React, { useState, useEffect } from "react";
import { 
  FaChartLine, FaRobot, FaBolt, FaCoins, FaBrain, 
  FaServer, FaClock, FaCheckCircle, FaLayerGroup 
} from "react-icons/fa";
import { fetchAnalyticsMetrics } from "../services/analyticsApi";

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalyticsMetrics().then((data) => {
      setMetrics(data);
      setLoading(false);
    });
  }, []);

  if (loading || !metrics) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500 text-xs">
        Loading platform telemetry...
      </div>
    );
  }

  const { summary, model_distribution, top_tools, daily_activity } = metrics;

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-y-auto custom-scrollbar p-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-500 text-white shadow-lg shadow-indigo-500/20">
            <FaChartLine size={18} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              AI Usage & Platform Telemetry
            </h1>
            <p className="text-xs text-[#9AA1B2]">
              Real-time APM token telemetry, autonomous agent compute, and model distribution
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>SLA: {summary.uptime_sla}</span>
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-[#0F1117] border border-[#242833] space-y-1">
          <span className="text-[10px] font-mono text-[#64748B] uppercase block">Total AI Requests</span>
          <div className="text-2xl font-bold text-white">{summary.total_ai_requests.toLocaleString()}</div>
          <span className="text-[10px] font-mono text-emerald-400 font-bold">+18.4% this week</span>
        </div>

        <div className="p-5 rounded-2xl bg-[#0F1117] border border-[#242833] space-y-1">
          <span className="text-[10px] font-mono text-[#64748B] uppercase block">Agent Tasks Completed</span>
          <div className="text-2xl font-bold text-indigo-300">{summary.autonomous_agent_tasks}</div>
          <span className="text-[10px] font-mono text-indigo-400 font-bold">100% Success Rate</span>
        </div>

        <div className="p-5 rounded-2xl bg-[#0F1117] border border-[#242833] space-y-1">
          <span className="text-[10px] font-mono text-[#64748B] uppercase block">Tokens Processed</span>
          <div className="text-2xl font-bold text-violet-300">{summary.total_tokens_consumed}</div>
          <span className="text-[10px] font-mono text-violet-400 font-bold">Optimized Context</span>
        </div>

        <div className="p-5 rounded-2xl bg-[#0F1117] border border-[#242833] space-y-1">
          <span className="text-[10px] font-mono text-[#64748B] uppercase block">Estimated Compute Cost</span>
          <div className="text-2xl font-bold text-cyan-300">{summary.estimated_cost_usd}</div>
          <span className="text-[10px] font-mono text-cyan-400 font-bold">Cost-Efficient</span>
        </div>
      </div>

      {/* Model Distribution & Top Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Model Distribution */}
        <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <FaBrain className="text-indigo-400" /> AI Model Utilization
          </h3>

          <div className="space-y-3 pt-2">
            {model_distribution.map((m, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-gray-300 font-bold">{m.model}</span>
                  <span className="text-indigo-300">{m.usage_pct}%</span>
                </div>
                <div className="w-full bg-[#151821] rounded-full h-2 overflow-hidden">
                  <div className={`h-full ${m.color}`} style={{ width: `${m.usage_pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Tools Leaderboard */}
        <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <FaBolt className="text-amber-400" /> Most Invoked AI Tools
          </h3>

          <div className="space-y-2.5 pt-2">
            {top_tools.map((tool, idx) => (
              <div key={idx} className="p-3 bg-[#151821] border border-[#242833] rounded-2xl flex items-center justify-between gap-3 text-xs">
                <div className="space-y-0.5">
                  <span className="font-bold text-white block">{tool.tool_name}</span>
                  <span className="text-[10px] font-mono text-gray-500">{tool.category}</span>
                </div>
                <span className="px-2.5 py-1 rounded-lg bg-[#08090D] border border-[#242833] text-indigo-300 font-mono text-[11px] font-bold">
                  {tool.invocations.toLocaleString()} runs
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Daily Volume Bar Chart */}
      <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <FaServer className="text-cyan-400" /> Daily AI Request Volume
        </h3>

        <div className="h-44 flex items-end gap-4 pt-6 px-4 border-b border-[#1C202B]">
          {daily_activity.map((d, idx) => {
            const heightPct = Math.round((d.requests / 3500) * 100);
            return (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                <div 
                  className="w-full bg-gradient-to-t from-[#6366F1] to-[#8D5CF6] rounded-t-xl transition-all duration-500 group-hover:opacity-80 shadow-md shadow-indigo-500/20"
                  style={{ height: `${heightPct}%` }}
                />
                <span className="text-[10px] font-mono text-gray-400">{d.day}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
