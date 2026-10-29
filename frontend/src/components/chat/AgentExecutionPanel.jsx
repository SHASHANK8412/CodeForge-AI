import React, { useState } from "react";
import { 
  FaBrain, FaRobot, FaSearch, FaCode, FaChartBar, FaCheckCircle, 
  FaSpinner, FaBook, FaTools, FaBolt, FaLayerGroup, FaExternalLinkAlt 
} from "react-icons/fa";

const AGENT_MODES = [
  { id: "AGENT", label: "Autonomous Agent", icon: <FaRobot size={11} />, desc: "Plans, executes tools, and verifies deliverables." },
  { id: "CHAT", label: "Smart Chat", icon: <FaBrain size={11} />, desc: "High-speed conversational assistant." },
  { id: "RESEARCH", label: "Deep Research", icon: <FaSearch size={11} />, desc: "Investigates RFCs & citations." },
  { id: "CODE", label: "Coding Agent", icon: <FaCode size={11} />, desc: "Sandbox testing & AST refactoring." },
  { id: "ANALYZE", label: "Data Analyzer", icon: <FaChartBar size={11} />, desc: "Evaluates metrics & distributions." }
];

export default function AgentExecutionPanel({ 
  activeMode = "AGENT", 
  onSelectMode, 
  activeModel = "claude-3-5-sonnet", 
  onSelectModel,
  models = [],
  lastRun = null,
  isRunning = false 
}) {
  const [showDetails, setShowDetails] = useState(true);

  return (
    <div className="bg-[#0F1117] border border-[#242833] rounded-2xl p-3.5 space-y-3 shadow-lg text-xs">
      {/* Top Bar: Mode Selector & Model Picker */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#1C202B]">
        {/* Mode Switcher */}
        <div className="flex items-center gap-1 overflow-x-auto custom-scrollbar">
          {AGENT_MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => onSelectMode && onSelectMode(m.id)}
              className={`px-2.5 py-1 rounded-xl font-bold flex items-center gap-1.5 transition text-[11px] cursor-pointer ${
                activeMode === m.id
                  ? "bg-indigo-600 text-white shadow"
                  : "bg-[#151821] text-gray-400 hover:text-gray-200"
              }`}
              title={m.desc}
            >
              {m.icon}
              <span>{m.label}</span>
            </button>
          ))}
        </div>

        {/* Model Picker */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-gray-400">Model:</span>
          <select
            value={activeModel}
            onChange={(e) => onSelectModel && onSelectModel(e.target.value)}
            className="bg-[#08090D] border border-[#242833] text-indigo-300 font-mono text-[10px] font-bold rounded-lg px-2 py-1 outline-none cursor-pointer"
          >
            <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Reasoning)</option>
            <option value="gpt-4o">GPT-4o Omnimodal</option>
            <option value="gemini-2.0-flash">Gemini 2.0 Flash (Fast)</option>
            <option value="deepseek-r1">DeepSeek R1 (Math & Code)</option>
          </select>
        </div>
      </div>

      {/* Live Execution Stepper (When active or showing last run) */}
      {lastRun && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <span className="text-gray-400 font-bold uppercase flex items-center gap-1.5">
              {isRunning ? (
                <>
                  <FaSpinner className="animate-spin text-indigo-400" />
                  <span>Agent Core Executing Pipeline...</span>
                </>
              ) : (
                <>
                  <FaCheckCircle className="text-emerald-400" />
                  <span>Agent Execution Pipeline • Verified</span>
                </>
              )}
            </span>
            <span className="text-gray-500">
              {lastRun.duration_seconds}s • {lastRun.total_tokens} tokens
            </span>
          </div>

          {/* Stepper Pipeline */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {(lastRun.steps || []).map((step, idx) => (
              <div 
                key={step.step_id || idx}
                className="p-2 bg-[#08090D] border border-[#1C202B] rounded-xl flex items-center gap-2 text-[10px]"
              >
                <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center font-mono font-bold text-[9px]">
                  ✓
                </span>
                <span className="text-gray-300 truncate">{step.title}</span>
              </div>
            ))}
          </div>

          {/* Citations & Sources (If Available) */}
          {lastRun.citations && lastRun.citations.length > 0 && (
            <div className="p-2.5 bg-[#08090D] border border-[#1C202B] rounded-xl space-y-1">
              <span className="text-[9px] font-mono text-cyan-400 font-bold uppercase block">
                Verified Sourced Citations
              </span>
              <div className="flex flex-wrap gap-1.5">
                {lastRun.citations.map((c, i) => (
                  <span key={i} className="px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-[10px] font-mono text-cyan-300 flex items-center gap-1">
                    <FaBook size={8} /> {c.ref || c.source}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
