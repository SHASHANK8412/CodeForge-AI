import React, { useState, useEffect } from "react";
import { 
  FaRocket, FaShieldAlt, FaTerminal, FaPlay, FaPause, FaStop, 
  FaCheckCircle, FaExclamationTriangle, FaFileCode, FaEye, 
  FaServer, FaTools, FaPlus, FaCheck, FaTimes, FaCodeBranch,
  FaLightbulb, FaPaintBrush, FaSave, FaDownload, FaUndo, FaSlidersH
} from "react-icons/fa";
import { 
  fetchMissions, 
  fetchMission, 
  launchMission, 
  approveMission, 
  fetchMcpServers 
} from "../services/missionControlApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

const MISSION_TEMPLATES = [
  { id: "tpl-build-feature", title: "Build Full-Stack Feature", category: "Engineering", default_goal: "Build real-time courier tracking with Redis Streams and interactive map UI." },
  { id: "tpl-fix-bug", title: "Diagnose & Auto-Fix Bug", category: "Debugging", default_goal: "Diagnose async event loop collision in background worker and repair." },
  { id: "tpl-research-topic", title: "Deep Tech Research & RFC", category: "Research", default_goal: "Benchmark Kafka vs Redis Streams vs NATS for geolocation latency." },
  { id: "tpl-analyze-data", title: "Statistical Data Analysis", category: "Analytics", default_goal: "Analyze peak dinner delivery cohorts and generate dynamic surge pricing models." },
  { id: "tpl-improve-ui", title: "Modernize UI & Visual QA", category: "Design", default_goal: "Improve AIForge Dashboard with dark mode contrast and responsive layout." },
  { id: "tpl-security-audit", title: "Security & CVE Compliance Audit", category: "Security", default_goal: "Run SAST audit on authentication and payment webhook endpoints." },
  { id: "tpl-code-review", title: "Pull Request Code Review", category: "Quality", default_goal: "Perform multi-agent architectural review on latest feature branch." },
  { id: "tpl-study-plan", title: "Adaptive Study Plan", category: "Study", default_goal: "Create 5-day DBMS exam study plan covering normalization and indexing." },
  { id: "tpl-prepare-report", title: "Executive Platform Report", category: "Product", default_goal: "Generate Q3 AIForge Platform Engineering & SLA Report." },
  { id: "tpl-competitive-analysis", title: "Competitive Benchmark", category: "Strategy", default_goal: "Compare AIForge Autonomous Computer vs OpenAI Agents SDK and Cursor." }
];

export default function MissionControlPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [missions, setMissions] = useState([]);
  const [activeMission, setActiveMission] = useState(null);
  const [mcpServers, setMcpServers] = useState([]);
  const [loading, setLoading] = useState(true);

  // New Mission Input & Plan Inspector
  const [missionTitle, setMissionTitle] = useState("");
  const [missionGoal, setMissionGoal] = useState("");
  const [isLaunching, setIsLaunching] = useState(false);
  const [showLaunchModal, setShowLaunchModal] = useState(false);
  const [showPlanInspector, setShowPlanInspector] = useState(false);

  // Diff Review Modal
  const [showDiffModal, setShowDiffModal] = useState(false);

  const loadData = async () => {
    try {
      const missionList = await fetchMissions(activeProjectId);
      setMissions(missionList || []);
      if (!activeMission && missionList && missionList.length > 0) {
        setActiveMission(missionList[0]);
      }
      const servers = await fetchMcpServers();
      setMcpServers(servers || []);
    } catch (err) {
      console.error("Error loading mission control data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleSelectTemplate = (tpl) => {
    setMissionTitle(tpl.title);
    setMissionGoal(tpl.default_goal);
    setShowPlanInspector(true);
    setShowLaunchModal(false);
  };

  const handleStartMission = async () => {
    if (!missionTitle.trim() || !missionGoal.trim()) return;
    setIsLaunching(true);
    toast("Dispatching Specialist Agents to Isolated Sandbox...", { icon: "🚀" });
    try {
      const created = await launchMission({
        title: missionTitle.trim(),
        goal: missionGoal.trim(),
        projectId: activeProjectId
      });
      toast.success("Mission active in isolated sandbox runtime!", { icon: "⚡" });
      setActiveMission(created);
      setShowPlanInspector(false);
      setShowLaunchModal(false);
      setMissionTitle("");
      setMissionGoal("");
      loadData();
    } catch (err) {
      toast.error("Mission launch failed");
    } finally {
      setIsLaunching(false);
    }
  };

  const handleApprove = async (approved) => {
    if (!activeMission) return;
    try {
      const updated = await approveMission(activeMission.id, approved);
      setActiveMission(updated);
      setShowDiffModal(false);
      toast.success(approved ? "Approved! Changes applied to workspace." : "Action rejected. Execution halted.", {
        icon: approved ? "✓" : "✕"
      });
      loadData();
    } catch (err) {
      toast.error("Approval action failed");
    }
  };

  const handleSaveToLibrary = () => {
    if (!activeMission?.final_report) return;
    saveOutputItem({
      title: activeMission.title,
      category: "Coding",
      content: activeMission.final_report,
      language: "markdown"
    });
    toast.success("Saved Mission Report to Library!", { icon: "📑" });
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Mission Control Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-rose-600 via-indigo-600 to-cyan-500 text-white shadow-lg shadow-indigo-500/20">
            <FaRocket size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              AIForge Mission Control
              <span className="px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-mono text-[10px] font-bold">
                Autonomous AI Operating Layer
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              User Goal → Specialist Agents → MCP Tools → Sandbox Computer → Verification → Human Consent
            </p>
          </div>
        </div>

        {/* Launch Mission CTA & Templates */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowLaunchModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-rose-600 to-indigo-600 hover:from-rose-500 hover:to-indigo-500 text-white rounded-xl font-bold transition shadow-lg shadow-rose-500/20 cursor-pointer text-xs"
          >
            <FaPlus size={10} />
            <span>Give AIForge a Mission</span>
          </button>
        </div>
      </div>

      {/* Main Split Screen Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Mission Selector & Templates (30%) */}
        <div className="w-80 bg-[#0F1117] border-r border-[#242833] overflow-y-auto p-4 space-y-4 custom-scrollbar">
          {/* Ready-Made Mission Templates */}
          <div className="space-y-2">
            <span className="text-[10px] font-mono text-indigo-400 uppercase block font-bold flex items-center gap-1">
              <FaLightbulb size={10} /> Mission Templates (10)
            </span>
            <div className="grid grid-cols-1 gap-1.5">
              {MISSION_TEMPLATES.slice(0, 5).map((tpl) => (
                <button
                  key={tpl.id}
                  onClick={() => handleSelectTemplate(tpl)}
                  className="p-2.5 rounded-xl bg-[#08090D] hover:bg-[#151821] border border-[#1C202B] hover:border-indigo-500/40 text-left transition text-xs group cursor-pointer"
                >
                  <span className="font-bold text-gray-200 group-hover:text-indigo-300 block truncate">{tpl.title}</span>
                  <span className="text-[10px] text-gray-500 font-mono">{tpl.category}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Active Missions List */}
          <div className="space-y-2 pt-3 border-t border-[#1C202B]">
            <span className="text-[10px] font-mono text-gray-400 uppercase block font-bold">
              Mission History ({missions.length})
            </span>
            {missions.map((m) => (
              <div
                key={m.id}
                onClick={() => setActiveMission(m)}
                className={`p-3.5 rounded-2xl cursor-pointer transition-all space-y-1.5 ${
                  activeMission?.id === m.id
                    ? "bg-[#1E293B] border border-rose-500/50 shadow-md"
                    : "bg-[#151821] hover:bg-[#1C202B] border border-[#242833]"
                }`}
              >
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className={`px-1.5 py-0.5 rounded font-bold ${
                    m.status === "COMPLETED" ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"
                  }`}>
                    {m.status}
                  </span>
                  <span className="text-gray-500">{m.progress_percent}%</span>
                </div>
                <h3 className="font-bold text-xs text-white line-clamp-1">{m.title}</h3>
                <p className="text-[10px] text-gray-400 line-clamp-1">{m.goal}</p>
              </div>
            ))}
          </div>

          {/* MCP Server Connections */}
          <div className="space-y-2 pt-3 border-t border-[#1C202B]">
            <span className="text-[10px] font-mono text-indigo-400 uppercase block font-bold flex items-center gap-1.5">
              <FaServer size={10} /> Connected MCP Servers ({mcpServers.length})
            </span>
            <div className="space-y-1.5">
              {mcpServers.map((srv) => (
                <div key={srv.id} className="p-2.5 bg-[#08090D] border border-[#1C202B] rounded-xl flex items-center justify-between gap-2 text-[11px]">
                  <div className="truncate">
                    <span className="font-bold text-gray-200 block truncate">{srv.name}</span>
                    <span className="text-[9px] font-mono text-gray-500">{srv.tools_count} MCP Tools Active</span>
                  </div>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" title="Connected" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Active Mission Operations Console (70%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {activeMission ? (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Mission Header Card */}
              <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4 shadow-xl">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono text-rose-400 font-bold uppercase tracking-wider block">
                      MISSION STATUS • {activeMission.status}
                    </span>
                    <h2 className="text-lg font-bold text-white">{activeMission.title}</h2>
                    <p className="text-xs text-gray-300">{activeMission.goal}</p>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 rounded-xl text-xs font-mono font-bold">
                      Agent: {activeMission.active_agent}
                    </span>
                    <span className="px-3 py-1 bg-slate-800 border border-slate-700 text-slate-300 rounded-xl text-xs font-mono">
                      {activeMission.environment}
                    </span>
                  </div>
                </div>

                {/* KPI Metrics Strip */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-[#1C202B]">
                  <div className="p-2.5 rounded-xl bg-[#08090D] border border-[#1C202B]">
                    <span className="text-[9px] font-mono text-gray-500 uppercase block">Files Changed</span>
                    <span className="text-sm font-bold text-white">{activeMission.files_changed_count}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#08090D] border border-[#1C202B]">
                    <span className="text-[9px] font-mono text-gray-500 uppercase block">Automated Tests</span>
                    <span className="text-sm font-bold text-emerald-400">{activeMission.tests_passed_count} / {activeMission.tests_count} Pass</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#08090D] border border-[#1C202B]">
                    <span className="text-[9px] font-mono text-gray-500 uppercase block">Approvals Gate</span>
                    <span className="text-sm font-bold text-amber-400">{activeMission.approvals_required_count} Checkpoint</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#08090D] border border-[#1C202B]">
                    <span className="text-[9px] font-mono text-gray-500 uppercase block">Progress</span>
                    <span className="text-sm font-bold text-indigo-400">{activeMission.progress_percent}%</span>
                  </div>
                </div>
              </div>

              {/* Human Approval Required Warning Banner (If Pending) */}
              {activeMission.pending_approval && (
                <div className="p-5 rounded-3xl bg-gradient-to-r from-amber-950/80 to-rose-950/80 border border-amber-500/50 space-y-3 shadow-2xl animate-fade-in">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="p-2.5 rounded-2xl bg-amber-500/20 text-amber-300 mt-0.5">
                        <FaExclamationTriangle size={18} />
                      </div>
                      <div>
                        <span className="text-[10px] font-mono text-amber-300 font-bold uppercase block">
                          ⚠️ HUMAN APPROVAL REQUIRED
                        </span>
                        <h3 className="text-sm font-bold text-white">
                          {activeMission.pending_approval.title}
                        </h3>
                        <p className="text-xs text-amber-100/90 mt-0.5">
                          {activeMission.pending_approval.reason}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-[10px] font-mono text-gray-300">Target Files:</span>
                          {activeMission.pending_approval.target_files.map((f, i) => (
                            <span key={i} className="px-2 py-0.5 rounded bg-black/50 border border-amber-500/30 text-[10px] font-mono text-amber-200">
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => setShowDiffModal(true)}
                        className="px-3 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-gray-200 border border-gray-700 rounded-xl text-xs font-semibold cursor-pointer"
                      >
                        Review Diffs
                      </button>
                      <button
                        onClick={() => handleApprove(true)}
                        className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold transition shadow cursor-pointer flex items-center gap-1.5"
                      >
                        <FaCheck size={9} /> Approve
                      </button>
                      <button
                        onClick={() => handleApprove(false)}
                        className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold transition shadow cursor-pointer flex items-center gap-1.5"
                      >
                        <FaTimes size={9} /> Reject
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Mission Stages Timeline */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono text-gray-400 uppercase block font-bold">
                  Autonomous Multi-Stage Execution Pipeline
                </span>
                <div className="space-y-2">
                  {(activeMission.stages || []).map((stage, idx) => (
                    <div
                      key={stage.id || idx}
                      className={`p-3.5 rounded-2xl border flex items-center justify-between gap-3 text-xs transition ${
                        stage.status === "COMPLETED" 
                          ? "bg-[#0F1117] border-[#242833]" 
                          : stage.status === "IN_PROGRESS"
                          ? "bg-indigo-950/40 border-indigo-500/50 shadow-md animate-pulse"
                          : "bg-[#0A0C10] border-[#1C202B] opacity-60"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-base">{stage.icon}</span>
                        <div>
                          <span className="font-bold text-white block">{stage.name}</span>
                          {stage.output_summary && (
                            <span className="text-[11px] text-gray-400">{stage.output_summary}</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 font-mono text-[10px]">
                        {stage.duration_seconds > 0 && (
                          <span className="text-gray-500">{stage.duration_seconds}s</span>
                        )}
                        <span className={`px-2 py-0.5 rounded font-bold ${
                          stage.status === "COMPLETED" ? "bg-emerald-500/20 text-emerald-300" : stage.status === "IN_PROGRESS" ? "bg-indigo-500/20 text-indigo-300" : "bg-gray-800 text-gray-400"
                        }`}>
                          {stage.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sandbox Terminal & Logs */}
              <div className="p-5 rounded-3xl bg-[#08090D] border border-[#242833] space-y-3 shadow-inner">
                <div className="flex items-center justify-between text-[#64748B] pb-2 border-b border-[#1C202B] text-xs">
                  <span className="flex items-center gap-2 font-mono font-bold text-gray-300">
                    <FaTerminal size={11} className="text-rose-400" /> Sandbox Computer Logs
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400">✓ Isolated vNode-22</span>
                </div>
                <div className="font-mono text-[11px] text-emerald-400 space-y-1 max-h-40 overflow-y-auto custom-scrollbar">
                  {(activeMission.terminal_logs || []).map((log, idx) => (
                    <div key={idx} className="leading-relaxed whitespace-pre-wrap">{log}</div>
                  ))}
                </div>
              </div>

              {/* Final Report Deliverables & Actions */}
              {activeMission.final_report && (
                <div className="p-6 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold">
                      Mission Deliverables & Artifacts
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setView("canvas")}
                        className="px-3 py-1.5 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow"
                      >
                        <FaPaintBrush size={10} /> Open in Live Canvas
                      </button>
                      <button
                        onClick={handleSaveToLibrary}
                        className="px-3 py-1.5 bg-[#1E293B] hover:bg-[#334155] text-indigo-300 rounded-xl text-xs font-semibold transition border border-gray-700 cursor-pointer flex items-center gap-1.5"
                      >
                        <FaSave size={10} /> Save to Library
                      </button>
                    </div>
                  </div>

                  <div className="text-xs font-mono text-gray-300 whitespace-pre-wrap bg-[#08090D] p-4 rounded-2xl border border-[#1C202B]">
                    {activeMission.final_report}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select or launch a mission to view execution
            </div>
          )}
        </div>
      </div>

      {/* Give AIForge A Mission Modal */}
      {showLaunchModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-lg bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl space-y-4 glow-violet">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FaRocket className="text-rose-400" /> Give AIForge a Mission
            </h3>
            <p className="text-xs text-gray-400">
              AIForge will coordinate specialist agents, discover MCP tools, inspect your workspace, execute changes in an isolated sandbox, run automated tests, perform visual QA, and present verified results.
            </p>
            <input
              type="text"
              value={missionTitle}
              onChange={(e) => setMissionTitle(e.target.value)}
              placeholder="Mission Title... e.g. 'Build landing page & test UI'"
              className="w-full bg-[#08090D] border border-[#242833] focus:border-rose-500 rounded-xl p-3 text-xs text-white outline-none"
            />
            <textarea
              value={missionGoal}
              onChange={(e) => setMissionGoal(e.target.value)}
              placeholder="Describe full mission objective and constraints..."
              rows={4}
              className="w-full bg-[#08090D] border border-[#242833] focus:border-rose-500 rounded-xl p-3 text-xs text-white outline-none resize-none"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowLaunchModal(false)}
                className="px-4 py-2 bg-[#151821] text-gray-300 rounded-xl font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowLaunchModal(false);
                  setShowPlanInspector(true);
                }}
                disabled={!missionTitle.trim() || !missionGoal.trim()}
                className="px-4 py-2 bg-gradient-to-r from-rose-600 to-indigo-600 hover:from-rose-500 hover:to-indigo-500 disabled:bg-gray-800 text-white rounded-xl font-bold transition shadow cursor-pointer"
              >
                Inspect Plan →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Plan Inspector Modal */}
      {showPlanInspector && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-lg bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl space-y-4 glow-violet">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              📋 Autonomous Mission Plan Inspector
            </h3>
            <p className="text-xs text-gray-300">
              Target Goal: <span className="font-bold text-white">{missionTitle}</span>
            </p>
            <div className="space-y-2 bg-[#08090D] p-4 rounded-2xl border border-[#1C202B]">
              <div className="flex items-center gap-2 text-xs text-gray-200">
                <span className="font-mono text-indigo-400 font-bold">1.</span> 🧠 Planner Agent: Inspect workspace AST & dependencies.
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-200">
                <span className="font-mono text-indigo-400 font-bold">2.</span> 🔍 Specialist UI Agent: Analyze component hierarchy.
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-200">
                <span className="font-mono text-indigo-400 font-bold">3.</span> 💻 Coding Agent: Implement verified code patches in Sandbox.
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-200">
                <span className="font-mono text-indigo-400 font-bold">4.</span> 🧪 Testing Agent: Run unit & integration tests.
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-200">
                <span className="font-mono text-indigo-400 font-bold">5.</span> 👁 Visual QA Agent: Check contrast & DOM layout shifts.
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-200">
                <span className="font-mono text-indigo-400 font-bold">6.</span> 🛡️ Human Consent Gateway: Checkpoint approval before write.
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowPlanInspector(false)}
                className="px-4 py-2 bg-[#151821] text-gray-300 rounded-xl font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleStartMission}
                disabled={isLaunching}
                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl font-bold transition shadow cursor-pointer"
              >
                {isLaunching ? "Launching..." : "Start Mission"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Review Diffs Modal */}
      {showDiffModal && activeMission?.pending_approval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-2xl bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FaCodeBranch className="text-indigo-400" /> Review Sandbox File Diffs
            </h3>
            <div className="p-4 bg-[#08090D] border border-[#1C202B] rounded-2xl font-mono text-xs text-emerald-400 whitespace-pre-wrap max-h-80 overflow-y-auto">
              {activeMission.pending_approval.diff_preview}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowDiffModal(false)}
                className="px-4 py-2 bg-[#151821] text-gray-300 rounded-xl font-semibold cursor-pointer"
              >
                Close
              </button>
              <button
                onClick={() => handleApprove(true)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold cursor-pointer transition shadow"
              >
                Approve & Apply
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
