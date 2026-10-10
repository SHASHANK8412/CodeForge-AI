import React, { useState, useEffect, useRef, useMemo } from "react";
import { 
  FaSearch, FaBolt, FaCode, FaBook, FaBrain, FaRocket, 
  FaHistory, FaBookmark, FaFolder, FaShieldAlt, FaComments, 
  FaCog, FaKey, FaChartBar, FaArrowRight, FaTimes, FaRobot, 
  FaCheck, FaPlay, FaLightbulb, FaPlus, FaTrash, FaPaintBrush,
  FaTasks, FaProjectDiagram, FaTerminal, FaLink
} from "react-icons/fa";
import { getSavedOutputs } from "../../utils/workspaceStorage";
import { 
  resolveCommandIntent, 
  getRecentCommands, 
  addRecentCommand, 
  clearRecentCommands, 
  quickRememberNote 
} from "../../services/commandRouterApi";
import { fetchMemories } from "../../services/aiMemoryApi";
import { launchTask } from "../../services/agentModeApi";
import toast from "react-hot-toast";

export default function CommandPalette({ 
  isOpen, 
  onClose, 
  setView, 
  onSelectPromptMode,
  currentProjectId = "aiforge-fooddelivery-ai"
}) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [dynamicIntent, setDynamicIntent] = useState(null);
  const [relevantMemories, setRelevantMemories] = useState([]);
  const [recentCommands, setRecentCommands] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Focus input & initialize when opened
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setRecentCommands(getRecentCommands());
      setTimeout(() => inputRef.current?.focus(), 40);
    }
  }, [isOpen]);

  // Live Intent & Memory Resolution as user types
  useEffect(() => {
    if (!isOpen) return;

    const timer = setTimeout(async () => {
      if (query.trim().length > 2) {
        const resolution = await resolveCommandIntent({
          query: query.trim(),
          currentProjectId
        });
        setDynamicIntent(resolution);

        // Query matching memories
        try {
          const memories = await fetchMemories({ search: query.trim() });
          setRelevantMemories((memories || []).slice(0, 3));
        } catch (err) {
          setRelevantMemories([]);
        }
      } else {
        setDynamicIntent(null);
        setRelevantMemories([]);
      }
    }, 120);

    return () => clearTimeout(timer);
  }, [query, isOpen, currentProjectId]);

  const savedOutputs = useMemo(() => getSavedOutputs(), [isOpen]);

  // Static searchable catalog
  const catalogItems = useMemo(() => {
    const items = [
      // Quick AI Actions
      { id: "act-mission", category: "Quick Action", title: "Mission: Give AIForge an Autonomous Computer Mission", icon: <FaRocket className="text-rose-400" />, action: () => setView("mission-control") },
      { id: "act-generate", category: "Quick Action", title: "Generate: Full-Stack Project from Spec", icon: <FaRocket className="text-violet-400" />, action: () => { if (onSelectPromptMode) onSelectPromptMode("Generate"); setView("create"); } },
      { id: "act-explain", category: "Quick Action", title: "Explain: Code Logic & Architecture", icon: <FaBook className="text-cyan-400" />, action: () => { if (onSelectPromptMode) onSelectPromptMode("Explain"); setView("talk"); } },
      { id: "act-summarize", category: "Quick Action", title: "Summarize: Project Specs & Commits", icon: <FaBrain className="text-emerald-400" />, action: () => { if (onSelectPromptMode) onSelectPromptMode("Summarize"); setView("dashboard"); } },
      { id: "act-debug", category: "Quick Action", title: "Debug: Diagnose Runtime Errors & Stacktraces", icon: <FaShieldAlt className="text-amber-400" />, action: () => { if (onSelectPromptMode) onSelectPromptMode("Debug"); setView("bug-bounty"); } },
      { id: "act-research", category: "Quick Action", title: "Research: Deep Tech & Multi-Agent Debate", icon: <FaBrain className="text-indigo-400" />, action: () => { if (onSelectPromptMode) onSelectPromptMode("Research"); setView("debate"); } },
      { id: "act-remember", category: "Quick Action", title: "Remember: Save Preference or Architecture Decision", icon: <FaBrain className="text-violet-400" />, action: () => setView("memory") },
      { id: "act-agents", category: "Quick Action", title: "Agent: Launch Multi-Step Autonomous Task", icon: <FaRobot className="text-indigo-400" />, action: () => setView("agents") },
      { id: "act-brainstorm", category: "Quick Action", title: "Brainstorm: System Architecture & RFCs", icon: <FaBolt className="text-pink-400" />, action: () => { if (onSelectPromptMode) onSelectPromptMode("Brainstorm"); setView("chat"); } },

      // AI Agents Fleet
      { id: "agent-coding-item", category: "AI Agents", title: "Coding Agent (Plan → Code → Test → Fix)", icon: <FaCode className="text-violet-400" />, action: () => setView("agents") },
      { id: "agent-study-item", category: "AI Agents", title: "Study Agent (Syllabus → Notes → Quiz → Diagnostic)", icon: <FaBook className="text-cyan-400" />, action: () => setView("agents") },
      { id: "agent-research-item", category: "AI Agents", title: "Research Agent (Spec Benchmarking & RFC Synthesis)", icon: <FaSearch className="text-indigo-400" />, action: () => setView("agents") },
      { id: "agent-resume-item", category: "AI Agents", title: "Resume Agent (ATS Scoring & STAR Formulator)", icon: <FaBookmark className="text-amber-400" />, action: () => setView("agents") },
      { id: "agent-data-item", category: "AI Agents", title: "Data Analyst Agent (Statistical & Chart Engine)", icon: <FaChartBar className="text-emerald-400" />, action: () => setView("agents") },

      // Recent Projects
      { id: "proj-fooddelivery", category: "Projects", title: "FoodDelivery AI (FastAPI + React + PostgreSQL)", icon: <FaFolder className="text-cyan-400" />, action: () => setView("projects") },
      { id: "proj-saas", category: "Projects", title: "SaaS Subscription Engine (Stripe + RBAC)", icon: <FaFolder className="text-blue-400" />, action: () => setView("projects") },

      // Specialized Engineering Tools Suite
      { id: "tool-workspace", category: "AI Tools", title: "Code Workspace (Monaco IDE & Agent Panel)", icon: <FaCode className="text-violet-400" />, action: () => setView("code") },
      { id: "tool-autopilot", category: "AI Tools", title: "Autopilot Engine (Autonomous Coding)", icon: <FaRocket className="text-cyan-400" />, action: () => setView("autopilot") },
      { id: "tool-xray", category: "AI Tools", title: "Project X-Ray (Deep Structural Inspection)", icon: <FaBrain className="text-emerald-400" />, action: () => setView("xray") },
      { id: "tool-dna", category: "AI Tools", title: "DNA Dependency Graph & AST Topology", icon: <FaBrain className="text-purple-400" />, action: () => setView("dna") },
      { id: "tool-debate", category: "AI Tools", title: "Multi-Agent Debate Arena", icon: <FaComments className="text-indigo-400" />, action: () => setView("debate") },
      { id: "tool-bug-hunter", category: "AI Tools", title: "Bug Hunter (Automated SAST & Fuzzing)", icon: <FaShieldAlt className="text-rose-400" />, action: () => setView("bug-bounty") },
      { id: "tool-talk-code", category: "AI Tools", title: "Talk to Code (Natural Language Assistant)", icon: <FaComments className="text-blue-400" />, action: () => setView("talk") },
      { id: "tool-flight", category: "AI Tools", title: "Flight Recorder (Execution Time Machine)", icon: <FaHistory className="text-amber-400" />, action: () => setView("flight-recorder") },
      { id: "tool-security", category: "AI Tools", title: "AIForge Sentinel (Defensive AI-SOC Cybersecurity)", icon: <FaShieldAlt className="text-emerald-400" />, action: () => setView("security") },
      { id: "tool-observability", category: "AI Tools", title: "Observability & Live APM Telemetry", icon: <FaChartBar className="text-cyan-400" />, action: () => setView("observability") },

      // Primary Navigation Views
      { id: "nav-dashboard", category: "Navigation", title: "Dashboard & AI Command Center", icon: <FaBolt className="text-violet-400" />, action: () => setView("dashboard") },
      { id: "nav-ai-os", category: "Navigation", title: "AIForge Autonomous AI Operating System (AIForge OS)", icon: <FaTerminal className="text-violet-400" />, action: () => setView("ai-os") },
      { id: "nav-computer-agent", category: "Navigation", title: "Computer-Using AI / Browser Agent", icon: <FaRobot className="text-emerald-400" />, action: () => setView("computer-agent") },
      { id: "nav-intelligence", category: "Navigation", title: "AI Intelligence & Evaluation Platform", icon: <FaChartBar className="text-cyan-400" />, action: () => setView("intelligence") },
      { id: "nav-mission-control", category: "Navigation", title: "Mission Control (Autonomous Computer Layer)", icon: <FaRocket className="text-rose-400" />, action: () => setView("mission-control") },
      { id: "nav-chat", category: "Navigation", title: "AI Chat Assistant", icon: <FaComments className="text-cyan-400" />, action: () => setView("chat") },
      { id: "nav-agents", category: "Navigation", title: "AI Agents Center", icon: <FaRobot className="text-indigo-400" />, action: () => setView("agents") },
      { id: "nav-multi-agent", category: "Navigation", title: "Multi-Agent Team Collaboration", icon: <FaRobot className="text-pink-400" />, action: () => setView("multi-agent") },
      { id: "nav-projects", category: "Navigation", title: "Projects Explorer", icon: <FaFolder className="text-blue-400" />, action: () => setView("projects") },
      { id: "nav-tools", category: "Navigation", title: "AI Tools Directory", icon: <FaBrain className="text-indigo-400" />, action: () => setView("tools") },
      { id: "nav-canvas", category: "Navigation", title: "Live AI Canvas (Interactive Split Workspace)", icon: <FaPaintBrush className="text-pink-400" />, action: () => setView("canvas") },
      { id: "nav-memory", category: "Navigation", title: "AI Memory & Intelligence Graph", icon: <FaBrain className="text-violet-400" />, action: () => setView("memory") },
      { id: "nav-tasks", category: "Navigation", title: "AI Task Management & Execution Hub", icon: <FaTasks className="text-emerald-400" />, action: () => setView("tasks") },
      { id: "nav-research", category: "Navigation", title: "Deep Research & Evidence Engine", icon: <FaSearch className="text-cyan-400" />, action: () => setView("research") },
      { id: "nav-knowledge-graph", category: "Navigation", title: "Knowledge Graph & Graph RAG Intelligence", icon: <FaProjectDiagram className="text-purple-400" />, action: () => setView("knowledge-graph") },
      { id: "nav-workflows", category: "Navigation", title: "Visual AI Workflow Builder & Automations", icon: <FaProjectDiagram className="text-amber-400" />, action: () => setView("workflows") },
      { id: "nav-saved", category: "Navigation", title: "Saved AI Outputs & Snippets", icon: <FaBookmark className="text-amber-400" />, action: () => setView("saved") },
      { id: "nav-history", category: "Navigation", title: "Recent Activity & Audit Log", icon: <FaHistory className="text-emerald-400" />, action: () => setView("history") },
      { id: "nav-cyber-copilot", category: "Navigation", title: "AI Cybersecurity Copilot (Zero-Trust SOC)", icon: <FaShieldAlt className="text-rose-400" />, action: () => setView("cyber-copilot") },
      { id: "nav-verifiable-ai", category: "Navigation", title: "Blockchain Trust Layer & Verifiable AI", icon: <FaLink className="text-amber-400" />, action: () => setView("verifiable-ai") },
      { id: "nav-analytics", category: "Navigation", title: "AI Usage & Platform Telemetry", icon: <FaChartBar className="text-cyan-400" />, action: () => setView("analytics") },
      { id: "nav-settings", category: "Navigation", title: "System & AI Settings", icon: <FaCog className="text-[#9AA1B2]" />, action: () => setView("settings") },
      { id: "nav-api-keys", category: "Navigation", title: "API Keys & Provider Configuration", icon: <FaKey className="text-[#9AA1B2]" />, action: () => setView("api-keys") },
    ];

    savedOutputs.forEach(out => {
      items.push({
        id: `saved-${out.id}`,
        category: "Saved Outputs",
        title: `${out.title} (${out.category})`,
        icon: <FaBookmark className="text-amber-400" />,
        action: () => setView("saved")
      });
    });

    return items;
  }, [savedOutputs, setView, onSelectPromptMode]);

  // Filter items matching query
  const filteredItems = useMemo(() => {
    if (!query.trim()) return catalogItems.slice(0, 15);
    const q = query.toLowerCase();
    return catalogItems.filter(item => 
      item.title.toLowerCase().includes(q) || 
      item.category.toLowerCase().includes(q)
    );
  }, [catalogItems, query]);

  // Execute Dynamic Intent Action directly from palette
  const handleExecuteDynamicIntent = async () => {
    if (!dynamicIntent) return;
    addRecentCommand(query);
    setIsProcessing(true);

    if (dynamicIntent.action_type === "STORE_MEMORY") {
      const fact = dynamicIntent.action_payload?.content || query;
      await quickRememberNote(fact);
      toast.success("Saved directly to AI Memory!", { icon: "🧠" });
      onClose();
      setView("memory");
    } else if (dynamicIntent.action_type === "LAUNCH_AGENT") {
      const agentId = dynamicIntent.action_payload?.agent_id || "agent-coding";
      await launchTask({
        agentId,
        goal: query,
        projectId: currentProjectId,
        memoryEnabled: true
      });
      toast.success("Agent dispatched on task!", { icon: "🚀" });
      onClose();
      setView("agents");
    } else {
      if (dynamicIntent.target_view) {
        setView(dynamicIntent.target_view);
      }
      onClose();
    }
    setIsProcessing(false);
  };

  const handleSelectItem = (item) => {
    addRecentCommand(item.title);
    item.action();
    onClose();
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === "Escape") {
      onClose();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < filteredItems.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filteredItems.length - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (dynamicIntent && dynamicIntent.action_type !== "NAVIGATE") {
        handleExecuteDynamicIntent();
      } else if (filteredItems[selectedIndex]) {
        handleSelectItem(filteredItems[selectedIndex]);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 p-4 bg-black/75 backdrop-blur-md animate-fade-in text-[#F5F7FA] font-sans"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-2xl bg-[#0F1117] border border-[#242833] rounded-3xl shadow-2xl overflow-hidden flex flex-col glow-violet text-xs"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Input Bar with Glowing AI Badge */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-[#242833] bg-[#151821]/80">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-[#6366F1] to-[#8D5CF6] text-white shadow-md shadow-indigo-500/20">
            <FaSearch size={13} />
          </div>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Ask AIForge anything... e.g. 'Debug code', 'Create DBMS study plan', 'Remember we use FastAPI'"
            className="flex-1 bg-transparent text-sm text-white placeholder-[#64748B] outline-none font-medium"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="text-[#64748B] hover:text-white p-1"
            >
              <FaTimes size={12} />
            </button>
          )}
          <kbd className="hidden sm:inline-block px-2 py-0.5 rounded-lg bg-[#08090D] border border-[#242833] text-[10px] font-mono text-[#64748B]">
            ESC
          </kbd>
        </div>

        {/* Quick Action Category Chips */}
        <div className="flex items-center gap-1.5 px-5 py-2.5 bg-[#0A0C10] border-b border-[#1C202B] overflow-x-auto custom-scrollbar">
          {[
            { label: "🤖 Run Agent", query: "Run Coding Agent for " },
            { label: "💻 Code", query: "Write a React FastAPI module for " },
            { label: "📚 Study", query: "Build a study plan for " },
            { label: "🔬 Research", query: "Research and benchmark " },
            { label: "✍️ Write", query: "Draft an architecture RFC for " },
            { label: "📊 Analyze", query: "Analyze cohort metrics for " },
            { label: "🧠 Remember", query: "Remember that " },
          ].map((chip, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(chip.query);
                inputRef.current?.focus();
              }}
              className="px-2.5 py-1 rounded-lg bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-[11px] font-semibold text-[#9AA1B2] hover:text-white transition shrink-0 cursor-pointer"
            >
              {chip.label}
            </button>
          ))}
        </div>

        {/* Dynamic Natural Language Routing Card (When intent is identified) */}
        {dynamicIntent && query.trim().length > 2 && (
          <div className="mx-4 mt-3 p-3.5 rounded-2xl bg-gradient-to-r from-indigo-950/60 to-violet-950/60 border border-indigo-500/40 space-y-2 animate-fade-in">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-300">
                  <FaBolt size={12} />
                </span>
                <div>
                  <span className="font-bold text-white text-xs block">
                    ✨ {dynamicIntent.title}
                  </span>
                  <span className="text-[10px] text-indigo-200 block">
                    {dynamicIntent.description}
                  </span>
                </div>
              </div>

              <button
                onClick={handleExecuteDynamicIntent}
                disabled={isProcessing}
                className="px-3 py-1.5 bg-gradient-to-r from-[#6366F1] to-[#8D5CF6] hover:from-[#4f46e5] hover:to-[#7c4ee4] text-white rounded-xl text-[11px] font-bold transition shadow-md flex items-center gap-1.5 cursor-pointer shrink-0"
              >
                <FaPlay size={8} />
                <span>Execute (Enter ↵)</span>
              </button>
            </div>

            {/* Smart Memory Pills Attached to Intent */}
            {relevantMemories.length > 0 && (
              <div className="pt-1.5 border-t border-indigo-500/20 flex items-center gap-1.5 flex-wrap">
                <span className="text-[9px] font-mono text-indigo-300 font-bold">
                  🧠 Relevant Memory Active:
                </span>
                {relevantMemories.map((m) => (
                  <span key={m.id} className="text-[9px] font-mono px-2 py-0.5 rounded-md bg-[#08090D] border border-indigo-500/30 text-indigo-200 truncate max-w-[180px]">
                    ✓ {m.title}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Results List */}
        <div ref={listRef} className="max-h-80 overflow-y-auto p-3 space-y-1 custom-scrollbar">
          {filteredItems.length === 0 ? (
            <div className="py-8 text-center text-[#64748B] space-y-1">
              <p className="text-xs">No matching actions found for "{query}"</p>
              <p className="text-[11px]">Press Enter to send as prompt to AI Assistant</p>
            </div>
          ) : (
            filteredItems.map((item, index) => (
              <div
                key={item.id}
                onClick={() => handleSelectItem(item)}
                className={`flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all ${
                  selectedIndex === index 
                    ? "bg-[#1E2330] border border-[#6366F1]/50 text-white shadow-sm" 
                    : "hover:bg-[#151821] text-[#9AA1B2] hover:text-white border border-transparent"
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="p-1.5 rounded-lg bg-[#08090D] border border-[#242833]">
                    {item.icon}
                  </div>
                  <div className="truncate">
                    <div className="font-semibold text-xs text-white truncate">
                      {item.title}
                    </div>
                    <div className="text-[10px] text-[#64748B] font-mono">
                      {item.category}
                    </div>
                  </div>
                </div>

                <FaArrowRight size={10} className={`text-[#64748B] transition-transform ${selectedIndex === index ? "translate-x-0.5 text-indigo-400" : ""}`} />
              </div>
            ))
          )}
        </div>

        {/* Recent Commands History Section (when query is empty) */}
        {!query && recentCommands.length > 0 && (
          <div className="px-5 py-2.5 border-t border-[#1C202B] bg-[#0A0C10] flex items-center justify-between text-[10px] font-mono text-[#64748B]">
            <div className="flex items-center gap-2 truncate">
              <span className="font-bold text-[#9AA1B2]">Recent:</span>
              {recentCommands.slice(0, 2).map((cmd, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuery(cmd);
                    inputRef.current?.focus();
                  }}
                  className="hover:text-indigo-300 truncate max-w-[150px] underline cursor-pointer"
                >
                  {cmd}
                </button>
              ))}
            </div>

            <button
              onClick={() => {
                clearRecentCommands();
                setRecentCommands([]);
              }}
              className="hover:text-rose-400 transition cursor-pointer"
              title="Clear Command History"
            >
              Clear
            </button>
          </div>
        )}

        {/* Footer Navigation Hints */}
        <div className="flex items-center justify-between px-5 py-2.5 border-t border-[#242833] bg-[#151821]/60 text-[10px] font-mono text-[#64748B]">
          <div className="flex items-center gap-3">
            <span><kbd className="px-1.5 py-0.5 rounded bg-[#08090D] border border-[#242833] text-gray-400">↑↓</kbd> Navigate</span>
            <span><kbd className="px-1.5 py-0.5 rounded bg-[#08090D] border border-[#242833] text-gray-400">↵</kbd> Select / Execute</span>
            <span><kbd className="px-1.5 py-0.5 rounded bg-[#08090D] border border-[#242833] text-gray-400">Esc</kbd> Close</span>
          </div>

          <span className="text-indigo-400 font-bold">AIForge OS Universal Router</span>
        </div>
      </div>
    </div>
  );
}
