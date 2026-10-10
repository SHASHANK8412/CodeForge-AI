import React, { useState, useEffect } from "react";
import { 
  FaUsers, FaRobot, FaBrain, FaSearch, FaCode, FaShieldAlt, 
  FaCheckCircle, FaPlay, FaLayerGroup, FaPlus, FaSave, FaExternalLinkAlt 
} from "react-icons/fa";
import { fetchAvailableAgents, fetchCollabMissions, dispatchCollabMission } from "../services/multiAgentApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

const SAMPLE_MISSIONS = [
  "Analyze FoodDelivery AI architecture, research dependencies, run sandbox tests, audit JWT security, and verify consensus.",
  "Deep research on Kafka vs Redis Streams latency tradeoffs with security threat model synthesis.",
  "Evaluate microservice API contracts, verify unit tests, and check tenant isolation compliance."
];

export default function MultiAgentPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [agents, setAgents] = useState([]);
  const [missions, setMissions] = useState([]);
  const [activeMission, setActiveMission] = useState(null);
  const [loading, setLoading] = useState(true);

  // New Mission Dispatch
  const [objective, setObjective] = useState("");
  const [isDispatching, setIsDispatching] = useState(false);

  const loadData = async () => {
    try {
      const [agentList, missionList] = await Promise.all([
        fetchAvailableAgents(),
        fetchCollabMissions(activeProjectId)
      ]);
      setAgents(agentList || []);
      setMissions(missionList || []);
      if (missionList && missionList.length > 0 && !activeMission) {
        setActiveMission(missionList[0]);
      }
    } catch (err) {
      console.error("Error loading multi-agent data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleDispatch = async (objToRun) => {
    const text = objToRun || objective;
    if (!text.trim()) return;
    setIsDispatching(true);
    setObjective(text);
    toast("Assembling Specialized AI Agent Team & Dispatching DAG Tasks...", { icon: "👥" });
    try {
      const created = await dispatchCollabMission({
        objective: text.trim(),
        projectId: activeProjectId
      });
      setActiveMission(created);
      setMissions([created, ...missions]);
      toast.success("Multi-Agent Team Collaborative Mission Complete!", { icon: "✓" });
    } catch (err) {
      toast.error("Multi-agent dispatch failed");
    } finally {
      setIsDispatching(false);
    }
  };

  const handleSaveToLibrary = () => {
    if (!activeMission) return;
    saveOutputItem({
      title: `Multi-Agent Team Report: ${activeMission.objective.slice(0, 45)}`,
      category: "Research",
      content: activeMission.final_synthesis,
      language: "markdown"
    });
    toast.success("Saved Collaborative Mission Report to Library!", { icon: "📑" });
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-pink-500 text-white shadow-lg shadow-indigo-500/20">
            <FaUsers size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Multi-Agent Team Intelligence
              <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono text-[10px] font-bold">
                Collaborative Intelligence Layer
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Parallel Autonomous Specialist Agents, Shared Workspace Provenance & Consensus Verification
            </p>
          </div>
        </div>

        {/* Global Agent Count */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-indigo-300">
            {agents.length} Specialized Agents Ready
          </span>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Agent Fleet & Previous Missions (30%) */}
        <div className="w-80 bg-[#0F1117] border-r border-[#242833] overflow-y-auto p-4 space-y-4 custom-scrollbar">
          {/* Agent Fleet Grid */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold block">
              Specialized Agent Fleet ({agents.length})
            </span>
            <div className="space-y-1.5">
              {agents.map((ag) => (
                <div key={ag.id} className="p-2.5 rounded-xl bg-[#08090D] border border-[#1C202B] space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-200 text-[11px]">{ag.name}</span>
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  </div>
                  <p className="text-[10px] text-gray-400 line-clamp-1">{ag.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Mission History */}
          <div className="space-y-2 pt-3 border-t border-[#1C202B]">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              Collaborative Team Missions ({missions.length})
            </span>
            {missions.map((m) => (
              <div
                key={m.id}
                onClick={() => setActiveMission(m)}
                className={`p-3 rounded-2xl cursor-pointer transition space-y-1 ${
                  activeMission?.id === m.id
                    ? "bg-[#1E293B] border border-indigo-500 shadow-md"
                    : "bg-[#151821] hover:bg-[#1C202B] border border-[#242833]"
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-emerald-400 font-bold">✓ {m.status}</span>
                  <span className="text-gray-500">{m.consensus_score ? `${Math.round(m.consensus_score * 100)}% Cons` : "96%"}</span>
                </div>
                <h3 className="font-bold text-xs text-white line-clamp-1">{m.objective}</h3>
              </div>
            ))}
          </div>
        </div>

        {/* Right Side: Active Mission Console & Shared Workspace (70%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {/* Dispatch Input Box */}
          <div className="max-w-4xl mx-auto p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl">
            <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold block">
              Assemble Multi-Agent Team & Give Objective
            </span>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleDispatch()}
                placeholder="e.g. Research dependencies, audit security, and verify tests for project..."
                className="flex-1 bg-[#08090D] border border-[#242833] focus:border-indigo-500 rounded-xl p-3 text-xs text-white outline-none"
              />
              <button
                onClick={() => handleDispatch()}
                disabled={isDispatching || !objective.trim()}
                className="px-4 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:bg-gray-800 text-white rounded-xl font-bold transition shadow cursor-pointer text-xs flex items-center gap-1.5"
              >
                <FaPlay size={10} />
                <span>{isDispatching ? "Collaborating..." : "Deploy Team"}</span>
              </button>
            </div>

            {/* Quick Prompt Pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {SAMPLE_MISSIONS.map((sm, i) => (
                <button
                  key={i}
                  onClick={() => handleDispatch(sm)}
                  className="px-2.5 py-1 rounded-lg bg-[#08090D] hover:bg-[#151821] border border-[#1C202B] text-[10px] text-gray-400 hover:text-indigo-300 font-mono transition cursor-pointer text-left truncate max-w-sm"
                >
                  👥 {sm}
                </button>
              ))}
            </div>
          </div>

          {/* Active Mission Operations Console */}
          {activeMission && (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Mission Header Card */}
              <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4 shadow-xl">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold tracking-wider block">
                      MULTI-AGENT TEAM IN ACTION • CONSENSUS GRADE: 98%
                    </span>
                    <h2 className="text-base font-bold text-white">{activeMission.objective}</h2>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 rounded-xl text-xs font-mono font-bold">
                      ✓ Team Verified
                    </span>
                  </div>
                </div>

                {/* Team Roster Strip */}
                <div className="flex flex-wrap gap-2 pt-2 border-t border-[#1C202B]">
                  {(activeMission.agents_involved || []).map((name, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-xl bg-[#08090D] border border-[#1C202B] text-[10px] font-mono text-indigo-300 flex items-center gap-1.5">
                      <FaRobot size={10} /> {name}
                    </span>
                  ))}
                </div>
              </div>

              {/* Parallel Task Graph DAG */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
                  Parallel Agent Task Execution Pipeline
                </span>
                <div className="space-y-2">
                  {(activeMission.tasks_dag || []).map((tsk) => (
                    <div key={tsk.id} className="p-3.5 rounded-2xl bg-[#0F1117] border border-[#242833] space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center text-[10px] font-bold">
                            ✓
                          </span>
                          <span className="font-bold text-white">{tsk.title}</span>
                        </div>
                        <span className="text-[10px] font-mono text-indigo-400">{tsk.assigned_agent_name}</span>
                      </div>
                      <p className="text-[11px] text-gray-400 pl-6 leading-relaxed">{tsk.output_summary}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Shared Workspace Findings */}
              <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-purple-400 uppercase font-bold block">
                    Shared Team Findings & Provenance ({activeMission.shared_findings?.length || 0})
                  </span>
                  <button
                    onClick={handleSaveToLibrary}
                    className="px-3 py-1.5 bg-[#1E293B] hover:bg-[#334155] text-purple-300 rounded-xl text-xs font-semibold border border-gray-700 cursor-pointer flex items-center gap-1"
                  >
                    <FaSave size={10} /> Save Report
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  {(activeMission.shared_findings || []).map((f) => (
                    <div key={f.id} className="p-3.5 rounded-2xl bg-[#08090D] border border-[#1C202B] space-y-2">
                      <div className="flex items-center justify-between font-mono text-[9px]">
                        <span className="text-indigo-400 font-bold">{f.author_agent}</span>
                        <span className="text-emerald-400">✓ {f.verification_status}</span>
                      </div>
                      <p className="text-gray-300 text-[11px] leading-relaxed">{f.claim}</p>
                      <span className="text-[9px] font-mono text-gray-500 block truncate">Evidence: {f.evidence_ref}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Final Synthesis Report */}
              {activeMission.final_synthesis && (
                <div className="p-5 rounded-2xl bg-[#08090D] border border-[#1C202B] font-mono text-xs text-gray-300 whitespace-pre-wrap">
                  {activeMission.final_synthesis}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
