import React from "react";
import { FaChartBar, FaChartLine, FaChartPie, FaPlus } from "react-icons/fa";

export default function VisualizationCanvas({ 
  content = {}, 
  onChange, 
  isReadOnly = false 
}) {
  // Only the data stored in the canvas is shown; there are no built-in sample figures.
  const metrics = content?.metrics || [];
  const chartBars = content?.bars || [];

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
