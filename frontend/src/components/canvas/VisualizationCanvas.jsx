import React from "react";
import { FaChartBar, FaChartLine, FaChartPie, FaPlus } from "react-icons/fa";

export default function VisualizationCanvas({ 
  content = {}, 
  onChange, 
  onAiTransform, 
  isReadOnly = false 
}) {
  const metrics = content?.metrics || [
    { label: "Daily Active Users", value: "48.2k", change: "+14.2%", trend: "up" },
    { label: "Avg Request Latency", value: "42ms", change: "-8.5%", trend: "down" },
    { label: "Cache Hit Rate", value: "98.6%", change: "+2.1%", trend: "up" },
    { label: "Error Rate (5xx)", value: "0.012%", change: "-45%", trend: "down" }
  ];

  const chartBars = content?.bars || [
    { label: "Mon", value: 65, color: "bg-indigo-500" },
    { label: "Tue", value: 78, color: "bg-indigo-500" },
    { label: "Wed", value: 92, color: "bg-violet-500" },
    { label: "Thu", value: 85, color: "bg-indigo-500" },
    { label: "Fri", value: 98, color: "bg-violet-500" },
    { label: "Sat", value: 72, color: "bg-indigo-500" },
    { label: "Sun", value: 60, color: "bg-indigo-500" }
  ];

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 font-sans text-xs custom-scrollbar">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#242833]">
        <div>
          <h2 className="text-sm font-bold text-white">Data Visualization & Analytics Dashboard</h2>
          <span className="text-[10px] text-[#64748B] font-mono">
            Interactive Telemetry & Retention Models
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onAiTransform("Generate a 12-month cohort retention curves visualization")}
            className="px-2.5 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-indigo-300 rounded-xl font-semibold transition border border-[#242833] cursor-pointer"
          >
            📈 Cohort Curves
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {metrics.map((m, idx) => (
          <div key={idx} className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
            <span className="text-[10px] font-mono text-[#64748B] uppercase block truncate">{m.label}</span>
            <div className="text-xl font-bold text-white">{m.value}</div>
            <span className={`text-[10px] font-mono font-bold ${m.trend === "up" ? "text-emerald-400" : "text-cyan-400"}`}>
              {m.change}
            </span>
          </div>
        ))}
      </div>

      {/* Interactive Bar Chart Visualization */}
      <div className="p-5 bg-[#0F1117]/90 border border-[#242833] rounded-3xl space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <span className="font-bold text-white text-xs flex items-center gap-2">
            <FaChartBar className="text-indigo-400" /> Weekly Activity Throughput
          </span>
          <span className="text-[10px] font-mono text-[#64748B]">Units: k-Requests</span>
        </div>

        <div className="h-44 flex items-end gap-3 pt-6 px-2 border-b border-[#1C202B]">
          {chartBars.map((bar, idx) => (
            <div key={idx} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
              <div 
                className={`w-full ${bar.color} rounded-t-lg transition-all duration-500 group-hover:opacity-80`}
                style={{ height: `${bar.value}%` }}
              />
              <span className="text-[10px] font-mono text-[#64748B]">{bar.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
