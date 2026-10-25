import React, { useState, useEffect } from "react";
import { 
  FaProjectDiagram, FaPlay, FaPause, FaCheckCircle, FaLock, 
  FaClock, FaBolt, FaPlus, FaSave, FaExternalLinkAlt, FaRobot, FaShieldAlt 
} from "react-icons/fa";
import { fetchAutonomousWorkflows, dispatchAutonomousWorkflow, approveWorkflowStep } from "../services/autonomousWorkflowApi";
import { saveOutputItem } from "../utils/workspaceStorage";
import toast from "react-hot-toast";

const SAMPLE_GOALS = [
  "Whenever a critical security alert appears, investigate telemetry, check policies, assess risk, and require human approval before applying containment.",
  "Every morning at 09:00, parse project RFCs, run sandbox AST regression suites, and prepare an executive architecture diff summary.",
  "Continuously monitor microservice API contracts, run test suites on commit, and anchor verified audit records to the ledger."
];

export default function AutonomousWorkflowPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);

  // New Workflow Goal Dispatch
  const [goal, setGoal] = useState("");
  const [triggerType, setTriggerType] = useState("EVENT_DRIVEN");
  const [isDispatching, setIsDispatching] = useState(false);

  const loadData = async () => {
    try {
      const list = await fetchAutonomousWorkflows();
      setWorkflows(list || []);
      if (list && list.length > 0 && !selectedWorkflow) {
        setSelectedWorkflow(list[0]);
      }
    } catch (err) {
      console.error("Error loading workflows:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProjectId]);

  const handleDispatch = async (gToRun) => {
    const text = gToRun || goal;
    if (!text.trim()) return;
    setIsDispatching(true);
    setGoal(text);
    toast("AI Goal Understanding → Compiling Multi-Agent Workflow DAG...", { icon: "⚙️" });
    try {
      const created = await dispatchAutonomousWorkflow({
        goal: text.trim(),
        triggerType
      });
      setWorkflows([created, ...workflows]);
      setSelectedWorkflow(created);
      setGoal("");
      toast.success("Autonomous AI Workflow Compiled & Executed!", { icon: "✓" });
    } catch (err) {
      toast.error("Workflow compilation failed");
    } finally {
      setIsDispatching(false);
    }
  };

  const handleApprove = async (stepId) => {
    if (!selectedWorkflow) return;
    toast("Processing Operator Approval Gate...", { icon: "🔒" });
    try {
      const res = await approveWorkflowStep(selectedWorkflow.id, stepId);
      if (res.success) {
        toast.success("Step Approved & Completed!", { icon: "✓" });
        setSelectedWorkflow((prev) => ({
          ...prev,
          steps_dag: prev.steps_dag.map((s) => s.id === stepId ? { ...s, is_approved: true, status: "COMPLETED" } : s)
        }));
      }
    } catch (err) {
      toast.error("Approval failed");
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-cyan-500 via-teal-600 to-indigo-600 text-white shadow-lg shadow-cyan-500/20">
            <FaProjectDiagram size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Autonomous AI Workflow & Automation Engine
              <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-mono text-[10px] font-bold">
                Goal-to-DAG Runtime
              </span>
            </h1>
            <p className="text-xs text-gray-400">
              Goal Understanding, Event-Driven Triggers, Multi-Agent Execution, Approval Gates & Ledger Anchors
            </p>
          </div>
        </div>

        {/* Global Flow Counter */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="px-3 py-1.5 bg-[#151821] border border-gray-800 rounded-xl text-cyan-300 font-bold">
            {workflows.length} Active Automations
          </span>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Workflow Catalog & Goal Planner (55%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar border-r border-[#242833]">
          {/* Goal-to-Workflow AI Planner */}
          <div className="p-5 rounded-3xl bg-[#0F1117] border border-[#242833] space-y-3 shadow-xl text-xs">
            <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold flex items-center gap-1.5">
              <FaBolt size={10} /> State Your High-Level Objective / Automation Goal
            </span>

            <textarea
              rows={3}
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Whenever a critical security alert appears, investigate telemetry, check policies, assess risk, and require human approval before applying WAF containment..."
              className="w-full bg-[#08090D] border border-[#242833] focus:border-cyan-500 rounded-xl p-3 text-xs text-white outline-none resize-none"
            />

            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-gray-400">Trigger:</span>
                <select
                  value={triggerType}
                  onChange={(e) => setTriggerType(e.target.value)}
                  className="bg-[#08090D] border border-[#242833] text-gray-300 rounded-lg px-2.5 py-1.5 text-xs outline-none cursor-pointer"
                >
                  <option value="EVENT_DRIVEN">Event-Driven (Alerts / Commits)</option>
                  <option value="SCHEDULED">Scheduled (Cron 09:00 Daily)</option>
                  <option value="MANUAL">Manual / On-Demand</option>
                  <option value="WEBHOOK">Webhook Inbound</option>
                </select>
              </div>

              <button
                onClick={() => handleDispatch()}
                disabled={isDispatching || !goal.trim()}
                className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-500 hover:to-teal-500 disabled:bg-gray-800 text-white rounded-xl font-bold transition shadow cursor-pointer text-xs flex items-center gap-1.5"
              >
                <FaPlay size={10} />
                <span>{isDispatching ? "Planning DAG..." : "Compile & Run Workflow"}</span>
              </button>
            </div>

            {/* Quick Goal Pills */}
            <div className="flex flex-wrap gap-1.5 pt-1">
              {SAMPLE_GOALS.map((sg, i) => (
                <button
                  key={i}
                  onClick={() => handleDispatch(sg)}
                  className="px-2.5 py-1 rounded-lg bg-[#08090D] hover:bg-[#151821] border border-[#1C202B] text-[10px] text-gray-400 hover:text-cyan-300 font-mono transition cursor-pointer text-left truncate max-w-md"
                >
                  ⚙️ {sg}
                </button>
              ))}
            </div>
          </div>

          {/* Workflow List */}
          <div className="space-y-3">
            <span className="text-[10px] font-mono text-gray-400 uppercase font-bold block">
              Configured Autonomous Workflows ({workflows.length})
            </span>
            <div className="space-y-3">
              {workflows.map((wf) => (
                <div
                  key={wf.id}
                  onClick={() => setSelectedWorkflow(wf)}
                  className={`p-4 rounded-2xl cursor-pointer transition space-y-2 ${
                    selectedWorkflow?.id === wf.id
                      ? "bg-[#101E24] border border-cyan-500 shadow-xl"
                      : "bg-[#0F1117] hover:bg-[#151821] border border-[#242833]"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold">
                      {wf.trigger_type} • {wf.autonomy_level}
                    </span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <FaCheckCircle size={10} /> {wf.status}
                    </span>
                  </div>

                  <h3 className="font-bold text-xs text-white">{wf.name}</h3>
                  <p className="text-[11px] text-gray-400 line-clamp-2 leading-relaxed">{wf.goal_description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Side: Live Workflow Execution DAG & Approval Gates (45%) */}
        <div className="w-[480px] bg-[#0F1117] overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {selectedWorkflow ? (
            <div className="space-y-5">
              <div className="space-y-1.5 pb-4 border-b border-[#1C202B]">
                <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono text-[10px] font-bold">
                  {selectedWorkflow.id}
                </span>
                <h2 className="text-base font-bold text-white">{selectedWorkflow.name}</h2>
                <p className="text-xs text-gray-400 leading-relaxed">{selectedWorkflow.goal_description}</p>
                {selectedWorkflow.verifiable_anchor_ref && (
                  <div className="pt-1">
                    <span className="px-2 py-0.5 rounded bg-purple-950/60 border border-purple-500/30 text-purple-300 font-mono text-[9px] block truncate">
                      Ledger Anchor: {selectedWorkflow.verifiable_anchor_ref}
                    </span>
                  </div>
                )}
              </div>

              {/* Multi-Step Execution DAG */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">
                  Workflow Execution Pipeline DAG ({selectedWorkflow.steps_dag?.length || 0} Steps)
                </span>

                <div className="space-y-3">
                  {(selectedWorkflow.steps_dag || []).map((step, idx) => (
                    <div key={step.id} className="p-4 rounded-2xl bg-[#08090D] border border-[#1C202B] space-y-2 text-xs">
                      <div className="flex items-center justify-between font-mono text-[10px]">
                        <span className="text-cyan-300 font-bold flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-300 flex items-center justify-center font-bold text-[9px]">
                            {idx + 1}
                          </span>
                          <span>{step.title}</span>
                        </span>
                        <span className="text-emerald-400">✓ {step.status}</span>
                      </div>

                      <p className="text-gray-400 text-[11px] leading-relaxed pl-5">{step.output_summary}</p>

                      <div className="flex items-center justify-between pl-5 pt-1 text-[9px] font-mono text-gray-500">
                        <span>Agent: {step.assigned_agent}</span>
                        <span>Duration: {step.duration_seconds}s</span>
                      </div>

                      {/* Approval Gate */}
                      {step.requires_approval && !step.is_approved && (
                        <div className="mt-2 p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 space-y-2">
                          <span className="text-[10px] font-mono text-amber-300 font-bold flex items-center gap-1">
                            <FaLock size={10} /> Operator Approval Required
                          </span>
                          <p className="text-[11px] text-gray-300">{step.remediation_action}</p>
                          <button
                            onClick={() => handleApprove(step.id)}
                            className="w-full py-1.5 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-bold text-[11px] transition shadow cursor-pointer flex items-center justify-center gap-1"
                          >
                            <FaCheckCircle size={10} /> Approve Step Execution
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select an autonomous workflow to view execution graph
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
