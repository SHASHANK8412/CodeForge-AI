import React, { useState, useEffect } from "react";
import { 
  FaTerminal, FaRobot, FaBrain, FaProjectDiagram, FaShieldAlt, 
  FaLink, FaPlay, FaStop, FaCheckCircle, FaExclamationTriangle, FaBolt, FaSave, FaExternalLinkAlt 
} from "react-icons/fa";
import { fetchOsOverview, executeUniversalCommand, fetchGoals, dispatchGoal, triggerEmergencyStop, resumeSystem } from "../services/aiOsApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

const SAMPLE_OS_COMMANDS = [
  "I need to understand the security posture of our application, correlate threats, and prepare a verifiable report for tomorrow.",
  "What technologies are indirectly affected if Apache Kafka fails?",
  "Run sandbox test suite on microservices, check RS256 JWT auth, and anchor consensus decision to blockchain."
];

export default function AiOsControlCenterPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [overview, setOverview] = useState(null);
  const [goals, setGoals] = useState([]);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [loading, setLoading] = useState(true);

  // Command Bar State
  const [command, setCommand] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);

  const loadData = async () => {
    try {
      const [ov, gList] = await Promise.all([
        fetchOsOverview(),
        fetchGoals()
      ]);
      setOverview(ov);
      setGoals(gList || []);
      if (gList && gList.length > 0 && !selectedGoal) {
        setSelectedGoal(gList[0]);
      }
    } catch (err) {
      console.error("Error loading OS overview:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleRunCommand = async (cmdToRun) => {
    const text = cmdToRun || command;
    if (!text.trim()) return;
    setIsExecuting(true);
    setCommand(text);
    toast("AIForge OS Kernel Routing Command via Universal Context Engine...", { icon: "🧠" });
    try {
      const res = await executeUniversalCommand(text.trim());
      setExecutionResult(res);
      toast.success(`Executed via ${res.route}!`, { icon: "✓" });
    } catch (err) {
      toast.error("Execution failed");
    } finally {
      setIsExecuting(false);
    }
  };

  const handleDispatchGoal = async (obj) => {
    toast("Dispatching Autonomous Goal to AIForge OS Kernel...", { icon: "🚀" });
    try {
      const g = await dispatchGoal({ objective: obj || command });
      setGoals([g, ...goals]);
      setSelectedGoal(g);
      toast.success("Goal Completed & Anchored into Ledger!", { icon: "✓" });
    } catch (err) {
      toast.error("Goal dispatch failed");
    }
  };

  const handleEmergencyStop = async () => {
    toast("Triggering Emergency Safety Interrupt...", { icon: "🚨" });
    try {
      const res = await triggerEmergencyStop();
      toast.error(res.message, { icon: "🛑" });
      setOverview((prev) => ({ ...prev, kernel_state: "EMERGENCY_STOPPED" }));
    } catch (err) {
      toast.error("Emergency stop failed");
    }
  };

  const handleResume = async () => {
    toast("Resuming AIForge OS Kernel...", { icon: "▶️" });
    try {
      const res = await resumeSystem();
      toast.success(res.message, { icon: "✓" });
      setOverview((prev) => ({ ...prev, kernel_state: "RUNNING" }));
    } catch (err) {
      toast.error("Resume failed");
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-violet-600 via-indigo-600 to-cyan-400 text-white shadow-lg shadow-violet-500/20">
            <FaTerminal size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              AIForge Autonomous AI Operating System
              <span className="px-2.5 py-0.5 rounded-full bg-violet-500/20 text-violet-300 font-mono text-[10px] font-bold">
                AIForge OS Kernel v7.0
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Universal Context Engine, Goal Decomposer, Multi-Agent Fleet, Zero-Trust SOC & Blockchain Trust Layer
            </p>
          </div>
        </div>

        {/* Global OS Health & Safety Controls */}
        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-emerald-400 font-bold">
            Health: {overview?.system_health || "99.4%"}
          </span>

          {overview?.kernel_state === "EMERGENCY_STOPPED" ? (
            <button
              onClick={handleResume}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold transition shadow cursor-pointer flex items-center gap-1.5"
            >
              <FaPlay size={10} /> Resume OS
            </button>
          ) : (
            <button
              onClick={handleEmergencyStop}
              className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl font-bold transition shadow cursor-pointer flex items-center gap-1.5"
              title="Emergency Safety Stop: Instantly suspend all autonomous agents and workflows"
            >
              <FaStop size={10} /> Emergency Stop
            </button>
          )}
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Universal Command Center & Subsystem Health (55%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar border-r border-[#242833]">
          {/* Universal AI Command Center Bar */}
          <div className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl text-xs">
            <span className="text-[10px] font-mono text-violet-400 uppercase font-bold flex items-center gap-1.5">
              <FaBolt size={10} /> Universal AIForge OS Command & Goal Center
            </span>

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleRunCommand()}
                placeholder="e.g. I need to understand the security posture and prepare a report for tomorrow..."
                className="flex-1 bg-[#08090D] border border-[#242833] focus:border-violet-500 rounded-xl p-3 text-xs text-white outline-none"
              />
              <button
                onClick={() => handleRunCommand()}
                disabled={isExecuting || !command.trim()}
                className="px-4 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:bg-gray-800 text-white rounded-xl font-bold transition shadow cursor-pointer text-xs flex items-center gap-1.5"
              >
                {isExecuting ? "Routing..." : "Execute"}
              </button>
            </div>

            {/* Quick Command Pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {SAMPLE_OS_COMMANDS.map((sc, i) => (
                <button
                  key={i}
                  onClick={() => handleRunCommand(sc)}
                  className="px-2.5 py-1 rounded-lg bg-[#08090D] hover:bg-[#151821] border border-[#1C202B] text-[10px] text-gray-400 hover:text-violet-300 font-mono transition cursor-pointer text-left truncate max-w-sm"
                >
                  ⚡ {sc}
                </button>
              ))}
            </div>
          </div>

          {/* Execution Result Banner */}
          {executionResult && (
            <div className="p-5 rounded-3xl bg-gradient-to-b from-[#181329] to-[#0F1117] border border-violet-500/40 space-y-3 animate-fade-in shadow-xl text-xs">
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-violet-300 font-bold uppercase">
                  ✓ Universal Context Engine Route: {executionResult.route}
                </span>
                <span className="text-gray-400">{executionResult.duration_seconds}s</span>
              </div>
              <p className="text-gray-300 text-xs">{executionResult.summary}</p>
            </div>
          )}

          {/* AIForge OS Subsystem Architecture Matrix */}
          <div className="space-y-3">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              AIForge OS Subsystem Digital Twin (6 Unified Tiers)
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {(overview?.active_subsystems || []).map((sub, i) => (
                <div key={i} className="p-3.5 rounded-2xl bg-[#0F1117] border border-[#242833] space-y-1.5">
                  <div className="flex items-center justify-between font-mono text-[9px]">
                    <span className="px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 font-bold">{sub.tier}</span>
                    <span className="text-emerald-400 font-bold">● {sub.status}</span>
                  </div>
                  <h3 className="font-bold text-xs text-white">{sub.name}</h3>
                </div>
              ))}
            </div>
          </div>

          {/* Autonomous Goals Feed */}
          <div className="space-y-3">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              Autonomous AI Goals & Success Criteria ({goals.length})
            </span>

            <div className="space-y-3">
              {goals.map((g) => (
                <div
                  key={g.id}
                  onClick={() => setSelectedGoal(g)}
                  className={`p-4 rounded-2xl cursor-pointer transition space-y-2 ${
                    selectedGoal?.id === g.id
                      ? "bg-[#18142B] border border-violet-500 shadow-xl"
                      : "bg-[#0F1117] hover:bg-[#151821] border border-[#242833]"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 font-bold">
                      {g.autonomy_level}
                    </span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <FaCheckCircle size={10} /> {g.status}
                    </span>
                  </div>

                  <h3 className="font-bold text-xs text-white">{g.objective}</h3>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Active Goal Inspector & Success Criteria (45%) */}
        <div className="w-[480px] bg-[#0F1117] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {selectedGoal ? (
            <div className="space-y-5">
              <div className="space-y-1.5 pb-4 border-b border-[#1C202B]">
                <span className="px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 font-mono text-[10px] font-bold">
                  {selectedGoal.id}
                </span>
                <h2 className="text-base font-bold text-white">{selectedGoal.objective}</h2>
                {selectedGoal.verifiable_ref && (
                  <div className="pt-1">
                    <span className="px-2 py-0.5 rounded bg-amber-950/60 border border-amber-500/30 text-amber-300 font-mono text-[9px] block truncate">
                      Ledger Anchor: {selectedGoal.verifiable_ref}
                    </span>
                  </div>
                )}
              </div>

              {/* Measurable Success Criteria */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold block">
                  Measurable Success Criteria (100% Satisfied)
                </span>

                <div className="space-y-2">
                  {(selectedGoal.success_criteria || []).map((crit, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-[#08090D] border border-[#1C202B] text-xs text-gray-300 font-mono">
                      {crit}
                    </div>
                  ))}
                </div>
              </div>

              {/* Output Deliverable */}
              {selectedGoal.output_deliverable && (
                <div className="space-y-2 pt-2 border-t border-[#1C202B]">
                  <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
                    Synthesized Deliverable Brief
                  </span>
                  <div className="p-4 rounded-2xl bg-[#08090D] border border-[#1C202B] text-xs text-gray-300 whitespace-pre-wrap font-mono">
                    {selectedGoal.output_deliverable}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select an autonomous goal to view success criteria & deliverable
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
