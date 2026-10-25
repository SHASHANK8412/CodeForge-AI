import React, { useState, useEffect, useRef } from "react";
import { 
  FaRobot, FaPlay, FaPause, FaStop, FaPlus, FaCheck, FaExclamationTriangle, 
  FaTools, FaBrain, FaFolder, FaHistory, FaTimes, FaShieldAlt, FaCode, 
  FaBook, FaSearch, FaChartBar, FaFileAlt, FaPaintBrush, FaRedo, FaExternalLinkAlt,
  FaCheckCircle, FaSpinner, FaClock, FaCopy, FaSave, FaSlidersH
} from "react-icons/fa";
import { 
  fetchAgents, 
  fetchTasks, 
  fetchTask, 
  launchTask, 
  pauseTask, 
  resumeTask, 
  stopTask, 
  approveTaskAction, 
  saveTaskToMemory,
  createCustomAgent,
  deleteCustomAgent,
  BUILTIN_AGENT_TEMPLATES
} from "../services/agentModeApi";
import toast from "react-hot-toast";

export default function AgentsPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [agents, setAgents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [activeTask, setActiveTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("tasks"); // "tasks", "templates", "history"

  // Launch Task Modal State
  const [showLaunchModal, setShowLaunchModal] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState("agent-coding");
  const [taskGoal, setTaskGoal] = useState("");
  const [taskProjectId, setTaskProjectId] = useState(activeProjectId || "aiforge-fooddelivery-ai");
  const [taskMemoryEnabled, setTaskMemoryEnabled] = useState(true);

  // Create Agent Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentDesc, setNewAgentDesc] = useState("");
  const [newAgentGoal, setNewAgentGoal] = useState("");
  const [newAgentInstructions, setNewAgentInstructions] = useState("");
  const [newAgentTools, setNewAgentTools] = useState(["Code Editor", "Memory Recall"]);
  const [newAgentApproval, setNewAgentApproval] = useState(false);
  const [newAgentMaxSteps, setNewAgentMaxSteps] = useState(6);

  // Poll active task when running
  const pollingRef = useRef(null);

  const loadData = async () => {
    try {
      const [agentList, taskList] = await Promise.all([
        fetchAgents(),
        fetchTasks()
      ]);
      setAgents(agentList || BUILTIN_AGENT_TEMPLATES);
      setTasks(taskList || []);
      if (!activeTask && taskList && taskList.length > 0) {
        setActiveTask(taskList[0]);
      }
    } catch (err) {
      console.error("Error loading agent data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const handleUpdate = () => loadData();
    window.addEventListener("aiforge:agent-tasks-updated", handleUpdate);
    return () => window.removeEventListener("aiforge:agent-tasks-updated", handleUpdate);
  }, []);

  // Polling loop for active running task
  useEffect(() => {
    if (activeTask && activeTask.status === "RUNNING") {
      pollingRef.current = setInterval(async () => {
        const updated = await fetchTask(activeTask.task_id);
        if (updated) {
          setActiveTask(updated);
          setTasks((prev) => prev.map(t => t.task_id === updated.task_id ? updated : t));
          if (updated.status !== "RUNNING") {
            clearInterval(pollingRef.current);
          }
        }
      }, 1500);
    } else {
      if (pollingRef.current) clearInterval(pollingRef.current);
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [activeTask?.task_id, activeTask?.status]);

  const handleLaunchTask = async (e) => {
    e.preventDefault();
    if (!taskGoal.trim()) return;

    try {
      const launched = await launchTask({
        agentId: selectedAgentId,
        goal: taskGoal.trim(),
        projectId: taskProjectId,
        memoryEnabled: taskMemoryEnabled
      });

      toast.success("Agent dispatched on task!", { icon: "🚀" });
      setShowLaunchModal(false);
      setTaskGoal("");
      setActiveTask(launched);
      setActiveTab("tasks");
      loadData();
    } catch (err) {
      toast.error("Failed to launch agent task");
    }
  };

  const handleCreateAgent = async (e) => {
    e.preventDefault();
    if (!newAgentName.trim() || !newAgentDesc.trim()) return;

    try {
      const created = await createCustomAgent({
        name: newAgentName.trim(),
        description: newAgentDesc.trim(),
        goal_placeholder: newAgentGoal.trim() || "Describe custom task...",
        system_instructions: newAgentInstructions.trim() || "You are an autonomous custom assistant.",
        tools: newAgentTools,
        requires_human_approval: newAgentApproval,
        max_steps: Number(newAgentMaxSteps) || 6
      });

      toast.success(`Custom Agent '${created.name}' created!`, { icon: "⚡" });
      setShowCreateModal(false);
      setNewAgentName("");
      setNewAgentDesc("");
      loadData();
    } catch (err) {
      toast.error("Failed to create agent");
    }
  };

  const handlePause = async () => {
    if (!activeTask) return;
    const res = await pauseTask(activeTask.task_id);
    if (res) setActiveTask(res);
    loadData();
  };

  const handleResume = async () => {
    if (!activeTask) return;
    const res = await resumeTask(activeTask.task_id);
    if (res) setActiveTask(res);
    loadData();
  };

  const handleStop = async () => {
    if (!activeTask) return;
    const res = await stopTask(activeTask.task_id);
    if (res) setActiveTask(res);
    loadData();
  };

  const handleApproval = async (approved) => {
    if (!activeTask) return;
    const res = await approveTaskAction(activeTask.task_id, approved);
    if (res) {
      setActiveTask(res);
      toast(approved ? "Action Approved. Resuming agent." : "Action Rejected. Agent stopped.", {
        icon: approved ? "✅" : "🛑"
      });
    }
    loadData();
  };

  const handleSaveToMemory = async () => {
    if (!activeTask) return;
    await saveTaskToMemory(activeTask.task_id);
    toast.success("Result saved to AI Memory!", { icon: "🧠" });
  };

  const openLaunchWithAgent = (agentId, placeholder = "") => {
    setSelectedAgentId(agentId);
    setTaskGoal(placeholder.replace(/^e\.g\.\s*/i, ""));
    setShowLaunchModal(true);
  };

  // Metrics
  const runningCount = tasks.filter(t => t.status === "RUNNING").length;
  const waitingApprovalCount = tasks.filter(t => t.status === "WAITING_APPROVAL").length;
  const completedCount = tasks.filter(t => t.status === "COMPLETED").length;

  return (
    <div className="min-h-full p-4 sm:p-6 lg:p-8 space-y-6 text-[#F5F7FA] font-sans max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#242833]">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-[#6366F1] to-[#8D5CF6] text-white shadow-lg shadow-indigo-500/25">
              <FaRobot size={18} />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
                AI Agent Mode & Autonomous Task Engine
              </h1>
              <span className="text-[10px] text-[#8D5CF6] font-mono uppercase tracking-widest font-bold">
                PLAN → EXECUTE → VERIFY → REPORT
              </span>
            </div>
          </div>
          <p className="text-xs text-[#9AA1B2] mt-1.5 max-w-2xl">
            Autonomous multi-step agents that break down complex goals, invoke toolchains, verify intermediate outputs, and require human approval for critical actions.
          </p>
        </div>

        <div className="flex items-center gap-2.5 self-start md:self-auto">
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-2.5 bg-[#151821] hover:bg-[#1E2330] text-[#9AA1B2] hover:text-white border border-[#242833] rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-2"
          >
            <FaPlus size={11} />
            <span>Create Custom Agent</span>
          </button>

          <button
            onClick={() => setShowLaunchModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[#6366F1] to-[#8D5CF6] hover:from-[#4f46e5] hover:to-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow-lg shadow-indigo-500/25 hover:scale-[1.02] active:scale-95 cursor-pointer"
          >
            <FaPlay size={10} />
            <span>Launch Agent Task</span>
          </button>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider">Agent Fleet</div>
          <div className="text-xl font-bold text-white">{agents.length}</div>
          <div className="text-[10px] text-[#9AA1B2]">Ready-made & Custom Agents</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider">Running Tasks</div>
          <div className="text-xl font-bold text-indigo-400 flex items-center gap-2">
            <span>{runningCount}</span>
            {runningCount > 0 && <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />}
          </div>
          <div className="text-[10px] text-[#9AA1B2]">Active Autonomous Executions</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider">Completed Tasks</div>
          <div className="text-xl font-bold text-emerald-400">{completedCount}</div>
          <div className="text-[10px] text-[#9AA1B2]">Verified & Finalized</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider">Approval Required</div>
          <div className="text-xl font-bold text-amber-400">{waitingApprovalCount}</div>
          <div className="text-[10px] text-[#9AA1B2]">Human Gateways Pending</div>
        </div>
      </div>

      {/* Navigation View Tabs */}
      <div className="flex items-center gap-2 border-b border-[#242833] pb-3">
        {[
          { id: "tasks", label: "Active Task & Timeline", icon: <FaPlay size={11} /> },
          { id: "templates", label: "Agent Fleet & Templates", icon: <FaRobot size={12} /> },
          { id: "history", label: "Task History & Artifacts", icon: <FaHistory size={11} /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              activeTab === tab.id
                ? "bg-[#6366F1] text-white shadow-md shadow-indigo-500/20"
                : "text-[#9AA1B2] hover:text-white hover:bg-[#151821]"
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* TAB 1: ACTIVE TASK & EXECUTION TIMELINE */}
      {activeTab === "tasks" && (
        <div className="space-y-6">
          {tasks.length === 0 ? (
            <div className="bg-[#0F1117]/60 border border-dashed border-[#242833] rounded-3xl p-12 text-center space-y-4">
              <div className="w-14 h-14 rounded-2xl bg-[#151821] border border-[#242833] flex items-center justify-center mx-auto text-[#64748B]">
                <FaRobot size={24} className="text-indigo-400" />
              </div>
              <div className="space-y-1.5 max-w-md mx-auto">
                <h3 className="text-base font-bold text-white">No active agent tasks</h3>
                <p className="text-xs text-[#9AA1B2]">
                  Select an agent template or enter a multi-step goal to watch the agent plan, execute tool calls, and verify results.
                </p>
              </div>
              <button
                onClick={() => setShowLaunchModal(true)}
                className="px-5 py-2.5 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl text-xs font-bold transition shadow-md shadow-indigo-500/25 cursor-pointer"
              >
                + Launch First Task
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Sidebar: Task Selector */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider font-bold block">
                  Select Task Run ({tasks.length})
                </span>

                <div className="space-y-2 max-h-[580px] overflow-y-auto custom-scrollbar pr-1">
                  {tasks.map((task) => (
                    <div
                      key={task.task_id}
                      onClick={() => setActiveTask(task)}
                      className={`p-3.5 rounded-2xl border transition-all cursor-pointer text-left space-y-2 ${
                        activeTask?.task_id === task.task_id
                          ? "bg-[#151821] border-[#6366F1] shadow-lg shadow-indigo-500/10"
                          : "bg-[#0F1117]/80 hover:bg-[#151821] border-[#242833]"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <span className="text-xs font-bold text-white truncate">
                          {task.agent_name}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold ${
                          task.status === "RUNNING" ? "bg-indigo-500/20 text-indigo-300 animate-pulse" :
                          task.status === "WAITING_APPROVAL" ? "bg-amber-500/20 text-amber-300 animate-bounce" :
                          task.status === "COMPLETED" ? "bg-emerald-500/20 text-emerald-300" :
                          task.status === "PAUSED" ? "bg-blue-500/20 text-blue-300" :
                          "bg-rose-500/20 text-rose-300"
                        }`}>
                          {task.status}
                        </span>
                      </div>

                      <p className="text-[11px] text-[#9AA1B2] line-clamp-2 leading-relaxed">
                        {task.goal}
                      </p>

                      <div className="flex items-center justify-between text-[10px] font-mono text-[#64748B] pt-1 border-t border-[#1C202B]">
                        <span>{task.steps?.length || 0} Steps</span>
                        <span>{task.created_at?.slice(11, 16) || "Recent"}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Main Area: Real-Time Interactive Timeline & Control Center */}
              {activeTask && (
                <div className="lg:col-span-2 space-y-4">
                  {/* Task Card Header & Controls */}
                  <div className="bg-[#0F1117]/90 border border-[#242833] rounded-3xl p-5 shadow-xl space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#242833]">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 font-bold text-xs">
                            {activeTask.agent_name}
                          </span>
                          {activeTask.project_id && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                              📁 {activeTask.project_id}
                            </span>
                          )}
                        </div>
                        <h2 className="text-base font-bold text-white mt-1.5">
                          {activeTask.goal}
                        </h2>
                      </div>

                      {/* Control Buttons: Pause / Resume / Stop */}
                      <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">
                        {activeTask.status === "RUNNING" && (
                          <button
                            onClick={handlePause}
                            className="flex items-center gap-1 px-3 py-1.5 bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-amber-300 rounded-xl text-xs font-semibold transition cursor-pointer"
                          >
                            <FaPause size={10} />
                            <span>Pause</span>
                          </button>
                        )}

                        {activeTask.status === "PAUSED" && (
                          <button
                            onClick={handleResume}
                            className="flex items-center gap-1 px-3 py-1.5 bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-emerald-300 rounded-xl text-xs font-semibold transition cursor-pointer"
                          >
                            <FaPlay size={10} />
                            <span>Resume</span>
                          </button>
                        )}

                        {["RUNNING", "PAUSED", "WAITING_APPROVAL"].includes(activeTask.status) && (
                          <button
                            onClick={handleStop}
                            className="flex items-center gap-1 px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 rounded-xl text-xs font-semibold transition cursor-pointer"
                          >
                            <FaStop size={10} />
                            <span>Stop</span>
                          </button>
                        )}

                        {activeTask.status === "COMPLETED" && (
                          <button
                            onClick={handleSaveToMemory}
                            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
                          >
                            <FaBrain size={11} />
                            <span>Save to Memory</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] font-mono">
                        <span className="text-[#9AA1B2]">Execution Progress</span>
                        <span className="font-bold text-indigo-400">{activeTask.progress_percent}%</span>
                      </div>
                      <div className="w-full h-2 bg-[#08090D] border border-[#242833] rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-[#6366F1] to-[#8D5CF6] transition-all duration-500 rounded-full"
                          style={{ width: `${activeTask.progress_percent}%` }}
                        />
                      </div>
                    </div>

                    {/* Human Approval Required Warning Card */}
                    {activeTask.status === "WAITING_APPROVAL" && activeTask.pending_approval && (
                      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 space-y-3 animate-fade-in text-xs">
                        <div className="flex items-center gap-2 text-amber-400 font-bold">
                          <FaExclamationTriangle size={15} />
                          <span>Human Approval Required</span>
                        </div>
                        <p className="text-[#F5F7FA] leading-relaxed">
                          {activeTask.pending_approval.description}
                        </p>
                        <div className="flex items-center gap-2 pt-1">
                          <button
                            onClick={() => handleApproval(true)}
                            className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold transition shadow cursor-pointer"
                          >
                            ✓ Approve Action
                          </button>
                          <button
                            onClick={() => handleApproval(false)}
                            className="px-3.5 py-1.5 bg-[#151821] hover:bg-rose-500/20 text-rose-400 border border-[#242833] rounded-xl font-semibold transition cursor-pointer"
                          >
                            ✕ Reject & Stop
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Interactive Multi-Step Timeline */}
                    <div className="space-y-3 pt-2">
                      <span className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider font-bold block">
                        Autonomous Execution Timeline
                      </span>

                      <div className="space-y-3">
                        {activeTask.steps?.map((step, idx) => (
                          <div 
                            key={step.step_id || idx}
                            className={`p-3.5 rounded-2xl border transition-all ${
                              step.status === "RUNNING"
                                ? "bg-[#151821] border-[#6366F1] shadow-md shadow-indigo-500/10"
                                : step.status === "COMPLETED"
                                ? "bg-[#0F1117] border-[#242833]"
                                : step.status === "WAITING_APPROVAL"
                                ? "bg-amber-500/5 border-amber-500/30"
                                : "bg-[#08090D] border-[#1C202B] opacity-60"
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="flex items-center gap-2.5 min-w-0">
                                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                                  step.status === "COMPLETED" ? "bg-emerald-500 text-black" :
                                  step.status === "RUNNING" ? "bg-indigo-500 text-white animate-spin" :
                                  step.status === "WAITING_APPROVAL" ? "bg-amber-500 text-black animate-bounce" :
                                  "bg-slate-800 text-slate-500"
                                }`}>
                                  {step.status === "COMPLETED" ? "✓" : step.status === "RUNNING" ? "●" : idx + 1}
                                </span>

                                <span className="font-bold text-white text-xs truncate">
                                  {step.name}
                                </span>
                              </div>

                              <div className="flex items-center gap-2 shrink-0">
                                {step.tool_used && (
                                  <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-[#151821] text-indigo-300 border border-[#242833] flex items-center gap-1">
                                    <FaTools size={8} /> {step.tool_used}
                                  </span>
                                )}

                                <span className="text-[10px] font-mono text-[#64748B]">
                                  {step.duration_ms ? `${(step.duration_ms / 1000).toFixed(1)}s` : ""}
                                </span>
                              </div>
                            </div>

                            {step.output && (
                              <div className="mt-2.5 p-2.5 bg-[#08090D] border border-[#242833] rounded-xl text-[11px] text-[#9AA1B2] font-mono leading-relaxed whitespace-pre-wrap">
                                {step.output}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Final Output Report Box (When Completed) */}
                    {activeTask.status === "COMPLETED" && activeTask.final_output && (
                      <div className="mt-4 p-5 rounded-2xl bg-[#08090D] border border-emerald-500/30 space-y-3 text-xs animate-fade-in">
                        <div className="flex items-center justify-between pb-2 border-b border-[#242833]">
                          <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                            <FaCheckCircle size={13} /> Final Agent Deliverable
                          </span>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(activeTask.final_output);
                              toast.success("Report copied to clipboard!");
                            }}
                            className="text-[#9AA1B2] hover:text-white p-1"
                            title="Copy Report"
                          >
                            <FaCopy size={12} />
                          </button>
                        </div>
                        <div className="text-white text-xs leading-relaxed whitespace-pre-wrap font-sans">
                          {activeTask.final_output}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: AGENT FLEET & TEMPLATES */}
      {activeTab === "templates" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="bg-[#0F1117]/90 hover:bg-[#151821] border border-[#242833] hover:border-[#6366F1]/50 rounded-2xl p-5 flex flex-col justify-between transition-all group shadow-lg"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{agent.icon || "🤖"}</span>
                    <div>
                      <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                        {agent.name}
                      </h3>
                      <span className="text-[10px] font-mono text-[#64748B] uppercase">
                        {agent.template_type} agent
                      </span>
                    </div>
                  </div>

                  {agent.requires_human_approval && (
                    <span className="px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[9px] font-mono font-bold" title="Requires human approval before actions">
                      🛡️ Approval Gate
                    </span>
                  )}
                </div>

                <p className="text-xs text-[#9AA1B2] leading-relaxed">
                  {agent.description}
                </p>

                {/* Available Tools */}
                <div className="space-y-1 pt-1">
                  <span className="text-[10px] font-mono text-[#64748B] block uppercase">
                    Available Tool Suite:
                  </span>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {agent.tools?.map((tool, idx) => (
                      <span key={idx} className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#08090D] border border-[#242833] text-indigo-300">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-[#1C202B] flex items-center justify-between gap-2">
                <span className="text-[10px] font-mono text-[#64748B]">
                  Max Steps: {agent.max_steps || 6}
                </span>

                <button
                  onClick={() => openLaunchWithAgent(agent.id, agent.goal_placeholder)}
                  className="px-3.5 py-1.5 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer flex items-center gap-1.5"
                >
                  <FaPlay size={9} />
                  <span>Run Agent</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 3: TASK HISTORY & ARTIFACTS */}
      {activeTab === "history" && (
        <div className="space-y-4">
          <div className="bg-[#0F1117]/80 border border-[#242833] rounded-2xl p-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#242833] text-[10px] font-mono text-[#64748B] uppercase">
                  <th className="pb-3 px-3">Agent</th>
                  <th className="pb-3 px-3">Goal</th>
                  <th className="pb-3 px-3">Status</th>
                  <th className="pb-3 px-3">Steps</th>
                  <th className="pb-3 px-3">Date</th>
                  <th className="pb-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1C202B]">
                {tasks.map((task) => (
                  <tr key={task.task_id} className="hover:bg-[#151821]/60 transition">
                    <td className="py-3 px-3 font-bold text-white flex items-center gap-1.5">
                      <FaRobot className="text-indigo-400" size={12} />
                      <span>{task.agent_name}</span>
                    </td>
                    <td className="py-3 px-3 text-[#9AA1B2] max-w-xs truncate">
                      {task.goal}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                        task.status === "COMPLETED" ? "bg-emerald-500/10 text-emerald-400" :
                        task.status === "RUNNING" ? "bg-indigo-500/10 text-indigo-400 animate-pulse" :
                        "bg-slate-800 text-slate-400"
                      }`}>
                        {task.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-[#64748B]">
                      {task.steps?.length || 0}
                    </td>
                    <td className="py-3 px-3 font-mono text-[#64748B]">
                      {task.created_at || "Recent"}
                    </td>
                    <td className="py-3 px-3 text-right space-x-2">
                      <button
                        onClick={() => {
                          setActiveTask(task);
                          setActiveTab("tasks");
                        }}
                        className="px-2.5 py-1 bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-indigo-300 rounded-lg text-[11px] font-semibold transition cursor-pointer"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL 1: LAUNCH TASK MODAL */}
      {showLaunchModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <form
            onSubmit={handleLaunchTask}
            className="w-full max-w-lg bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl text-xs space-y-4 flex flex-col glow-violet"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#242833]">
              <div className="flex items-center gap-2">
                <FaPlay className="text-indigo-400" size={13} />
                <h3 className="text-sm font-bold text-white">
                  Dispatch Autonomous Agent Task
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowLaunchModal(false)}
                className="text-[#64748B] hover:text-white p-1 rounded-lg transition"
              >
                <FaTimes size={13} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Select Agent</label>
                <select
                  value={selectedAgentId}
                  onChange={(e) => setSelectedAgentId(e.target.value)}
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#6366F1] rounded-xl px-3 py-2 text-white outline-none cursor-pointer"
                >
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>{a.name} ({a.template_type})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Target Goal / Task Instruction</label>
                <textarea
                  value={taskGoal}
                  onChange={(e) => setTaskGoal(e.target.value)}
                  placeholder="e.g. Build an async task queue worker with Redis and FastAPI"
                  rows={4}
                  required
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#6366F1] rounded-xl p-3 text-white outline-none resize-none leading-relaxed"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Target Project</label>
                  <select
                    value={taskProjectId}
                    onChange={(e) => setTaskProjectId(e.target.value)}
                    className="w-full bg-[#08090D] border border-[#242833] rounded-xl px-3 py-2 text-white outline-none cursor-pointer"
                  >
                    <option value="aiforge-fooddelivery-ai">FoodDelivery AI</option>
                    <option value="global-workspace">Global Workspace</option>
                  </select>
                </div>

                <div className="flex flex-col justify-end">
                  <label className="flex items-center gap-2 pb-2.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={taskMemoryEnabled}
                      onChange={(e) => setTaskMemoryEnabled(e.target.checked)}
                      className="rounded bg-[#08090D] border-[#242833] text-[#6366F1]"
                    />
                    <span className="text-xs text-white font-semibold">Enable AI Memory</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#242833]">
              <button
                type="button"
                onClick={() => setShowLaunchModal(false)}
                className="px-3.5 py-2 text-xs text-[#9AA1B2] hover:text-white transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
              >
                Launch Task
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL 2: CREATE CUSTOM AGENT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <form
            onSubmit={handleCreateAgent}
            className="w-full max-w-lg bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl text-xs space-y-4 flex flex-col glow-violet"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#242833]">
              <div className="flex items-center gap-2">
                <FaRobot className="text-amber-400" size={14} />
                <h3 className="text-sm font-bold text-white">
                  Create Custom Autonomous Agent
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-[#64748B] hover:text-white p-1 rounded-lg transition"
              >
                <FaTimes size={13} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Agent Name</label>
                <input
                  type="text"
                  value={newAgentName}
                  onChange={(e) => setNewAgentName(e.target.value)}
                  placeholder="e.g. Security Compliance Auditor"
                  required
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#6366F1] rounded-xl px-3 py-2 text-white outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Description</label>
                <input
                  type="text"
                  value={newAgentDesc}
                  onChange={(e) => setNewAgentDesc(e.target.value)}
                  placeholder="e.g. Scans repos for CVEs, audits secrets, and enforces GDPR compliance"
                  required
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#6366F1] rounded-xl px-3 py-2 text-white outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">System Instructions</label>
                <textarea
                  value={newAgentInstructions}
                  onChange={(e) => setNewAgentInstructions(e.target.value)}
                  placeholder="Describe role, behavioral constraints, and verification protocols..."
                  rows={3}
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#6366F1] rounded-xl p-3 text-white outline-none resize-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="approvalReq"
                  checked={newAgentApproval}
                  onChange={(e) => setNewAgentApproval(e.target.checked)}
                  className="rounded bg-[#08090D] border-[#242833] text-[#6366F1]"
                />
                <label htmlFor="approvalReq" className="text-xs text-[#9AA1B2] cursor-pointer select-none">
                  Require human approval before executing file writes or terminal actions
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#242833]">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-3.5 py-2 text-xs text-[#9AA1B2] hover:text-white transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-gradient-to-r from-[#6366F1] to-[#8D5CF6] hover:from-[#4f46e5] hover:to-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
              >
                Create Agent
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
