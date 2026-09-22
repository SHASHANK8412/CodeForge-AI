import React, { useState } from "react";
import { 
  FaBolt, FaLightbulb, FaFileAlt, FaBug, FaSearch, FaBrain, 
  FaPaperPlane, FaMicrochip
} from "react-icons/fa";

export default function AICommandCenter({ onLaunchPrompt, setView }) {
  const [promptInput, setPromptInput] = useState("");
  const [selectedModel, setSelectedModel] = useState("claude-3.7");
  const [activeMode, setActiveMode] = useState("generate");

  const models = [
    { id: "claude-3.7", name: "Claude 3.7 Sonnet (Reasoning)", badge: "Primary" },
    { id: "gpt-4o", name: "GPT-4o (Omni Engine)", badge: "Fast" },
    { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro (2M Context)", badge: "Deep" },
    { id: "deepseek-r1", name: "DeepSeek R1 (Math/Logic)", badge: "Audit" },
    { id: "llama-3-70b", name: "Llama 3 70B (Local Edge)", badge: "Edge" },
  ];

  const quickActions = [
    { 
      id: "generate", 
      label: "Generate", 
      icon: <FaBolt className="text-violet-400" />, 
      hint: "Generate full-stack app or component", 
      promptSample: "Build a real-time collaborative Kanban board with drag-and-drop, WebSocket sync, and SQLite backend."
    },
    { 
      id: "explain", 
      label: "Explain", 
      icon: <FaLightbulb className="text-cyan-400" />, 
      hint: "Explain algorithms or architecture", 
      promptSample: "Explain the memory sync model and AST graph dependency resolution in AIForge."
    },
    { 
      id: "summarize", 
      label: "Summarize", 
      icon: <FaFileAlt className="text-emerald-400" />, 
      hint: "Summarize codebase & specs", 
      promptSample: "Summarize the architectural differences between our REST API routers and GraphQL schemas."
    },
    { 
      id: "debug", 
      label: "Debug", 
      icon: <FaBug className="text-amber-400" />, 
      hint: "Trace stacktraces & fix errors", 
      promptSample: "Analyze potential race conditions in concurrent FastAPI background tasks and propose a mutex lock."
    },
    { 
      id: "research", 
      label: "Research", 
      icon: <FaSearch className="text-indigo-400" />, 
      hint: "Evaluate libraries & benchmarks", 
      promptSample: "Benchmark Redis vs DragonflyDB for session caching under 50,000 req/sec load."
    },
    { 
      id: "brainstorm", 
      label: "Brainstorm", 
      icon: <FaBrain className="text-pink-400" />, 
      hint: "System design & RFC ideation", 
      promptSample: "Brainstorm an autonomous failover architecture for multi-region Kubernetes deployments."
    },
  ];

  const handleQuickActionClick = (action) => {
    setActiveMode(action.id);
    setPromptInput(action.promptSample);
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!promptInput.trim()) return;

    if (onLaunchPrompt) {
      onLaunchPrompt(promptInput.trim(), activeMode, selectedModel);
    } else {
      sessionStorage.setItem("aiforge_pending_prompt", promptInput.trim());
      if (setView) setView("create");
    }
  };

  return (
    <div className="space-y-6">
      {/* Primary Command Center Hero Box */}
      <div className="relative bg-gradient-to-b from-[#11141E] to-[#0D0F17] border border-[#242833] rounded-3xl p-6 md:p-8 shadow-2xl overflow-hidden glow-violet">
        {/* Ambient background aura */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Hero Title & Status Header */}
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#242833]/80">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full bg-gradient-to-r from-violet-600/30 to-cyan-500/30 border border-violet-500/40 text-violet-300 font-mono text-[10px] font-bold uppercase tracking-widest flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-ping" />
                AI Workspace Operating System
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              AI Command Center
            </h1>
            <p className="text-xs text-[#9AA1B2] mt-1 max-w-xl">
              Architect, generate, debug, and orchestrate autonomous full-stack software systems with multi-agent consensus.
            </p>
          </div>

          {/* Model Selector Pill */}
          <div className="flex items-center gap-2 bg-[#08090D]/90 border border-[#242833] p-1.5 rounded-2xl shrink-0">
            <FaMicrochip className="text-[#8D5CF6] ml-2" size={13} />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              aria-label="Select AI Model"
              className="bg-transparent text-xs font-semibold text-[#F5F7FA] outline-none pr-3 py-1 cursor-pointer font-sans"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id} className="bg-[#0F1117] text-white">
                  {m.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Interactive Prompt Console */}
        <form onSubmit={handleSubmit} className="relative z-10 mt-6 space-y-4">
          <div className="relative bg-[#08090D]/90 border border-[#242833] focus-within:border-[#8D5CF6] rounded-2xl p-3 shadow-inner transition-all group">
            <textarea
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              placeholder="Describe your software architecture, debug a bug, or enter an engineering prompt..."
              rows={3}
              className="w-full bg-transparent text-xs md:text-sm text-white placeholder-[#64748B] outline-none resize-none font-mono leading-relaxed p-1"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
            />

            {/* Prompt Console Bottom Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#1C202B]">
              <div className="flex items-center gap-2 text-[11px] text-[#64748B]">
                <span className="hidden sm:inline">Mode:</span>
                <span className="px-2 py-0.5 rounded-md bg-[#151821] text-[#9AA1B2] font-mono capitalize">
                  {activeMode}
                </span>
                <span className="hidden sm:inline">• Press Enter to execute</span>
              </div>

              <div className="flex items-center gap-2">
                {promptInput && (
                  <button
                    type="button"
                    onClick={() => setPromptInput("")}
                    className="px-2.5 py-1.5 text-xs text-[#64748B] hover:text-white transition cursor-pointer"
                  >
                    Clear
                  </button>
                )}
                <button
                  type="submit"
                  className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-[#8D5CF6] to-[#6366F1] hover:from-[#7c4ee4] hover:to-[#4f46e5] text-white rounded-xl text-xs font-bold transition shadow-lg shadow-violet-500/25 hover:scale-[1.02] active:scale-95 cursor-pointer"
                >
                  <FaPaperPlane size={11} />
                  <span>Execute Command</span>
                </button>
              </div>
            </div>
          </div>

          {/* Quick Action Buttons Row */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider">
                Quick Actions
              </span>
              <span className="text-[10px] text-[#64748B]">Click to load specialized workflow</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              {quickActions.map((action) => {
                const isActive = activeMode === action.id;
                return (
                  <button
                    key={action.id}
                    type="button"
                    onClick={() => handleQuickActionClick(action)}
                    className={`p-2.5 rounded-xl border text-left transition-all relative overflow-hidden group cursor-pointer ${
                      isActive
                        ? "bg-[#8D5CF6]/15 border-[#8D5CF6] text-white shadow-md shadow-violet-500/10"
                        : "bg-[#0F1117]/80 hover:bg-[#151821] border-[#242833] text-[#9AA1B2] hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="p-1 rounded bg-[#151821] group-hover:scale-110 transition-transform">
                        {action.icon}
                      </span>
                      <span className="text-xs font-bold text-white">{action.label}</span>
                    </div>
                    <p className="text-[10px] text-[#64748B] group-hover:text-[#9AA1B2] truncate">
                      {action.hint}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        </form>
      </div>

      {/* Live System Telemetry Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1 hover:border-[#8D5CF6]/40 transition">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider flex items-center justify-between">
            <span>Project Health</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          </div>
          <div className="text-xl font-bold text-emerald-400">96.4%</div>
          <div className="text-[10px] text-[#9AA1B2]">6 Core Pillars Verified</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1 hover:border-[#06B6D4]/40 transition">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider flex items-center justify-between">
            <span>Test Suite</span>
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
          </div>
          <div className="text-xl font-bold text-cyan-400">48 / 48 Passed</div>
          <div className="text-[10px] text-[#9AA1B2]">0 Failures • 100% Coverage</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1 hover:border-[#8D5CF6]/40 transition">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider flex items-center justify-between">
            <span>Project Memory</span>
            <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
          </div>
          <div className="text-xl font-bold text-violet-400">12 Decisions</div>
          <div className="text-[10px] text-[#9AA1B2]">Versioned Knowledge Graph</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1 hover:border-emerald-500/40 transition">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider flex items-center justify-between">
            <span>Active Agents</span>
            <span className="w-1.5 h-1.5 rounded-full bg-white" />
          </div>
          <div className="text-xl font-bold text-white">8 Agents Live</div>
          <div className="text-[10px] text-emerald-400 font-semibold">Consensus Synchronized</div>
        </div>
      </div>
    </div>
  );
}
