import React, { useState, useEffect } from "react";
import { 
  FaProjectDiagram, FaPlay, FaPlus, FaClock, FaCheckCircle, 
  FaRobot, FaTools, FaBell, FaBolt, FaArrowRight
} from "react-icons/fa";
import { fetchWorkflows, createWorkflow, executeWorkflow } from "../services/workflowBuilderApi";
import toast from "react-hot-toast";

export default function WorkflowsPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [workflows, setWorkflows] = useState([]);
  const [activeWf, setActiveWf] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // New Workflow Modal
  const [showNewModal, setShowNewModal] = useState(false);
  const [titleInput, setTitleInput] = useState("");
  const [descInput, setDescInput] = useState("");
  const [cronInput, setCronInput] = useState("Every Monday at 9:00 AM");

  const loadWorkflows = async () => {
    try {
      const data = await fetchWorkflows(activeProjectId);
      setWorkflows(data || []);
      if (!activeWf && data && data.length > 0) {
        setActiveWf(data[0]);
      }
    } catch (err) {
      console.error("Error loading workflows:", err);
    }
  };

  useEffect(() => {
    loadWorkflows();
  }, [activeProjectId]);

  const handleExecute = async (wfId) => {
    setIsExecuting(true);
    toast("Executing multi-node autonomous workflow...", { icon: "⚡" });
    try {
      const res = await executeWorkflow(wfId);
      toast.success(res.summary || "Workflow completed!", { icon: "🚀" });
      loadWorkflows();
    } catch (err) {
      toast.error("Execution failed");
    } finally {
      setIsExecuting(false);
    }
  };

  const handleCreate = async () => {
    if (!titleInput.trim()) return;
    await createWorkflow({
      title: titleInput.trim(),
      description: descInput.trim(),
      trigger_type: "SCHEDULED_CRON",
      schedule_cron: cronInput.trim(),
      project_id: activeProjectId,
      nodes: [
        { id: "n1", type: "TRIGGER", label: `Schedule: ${cronInput}`, config: {} },
        { id: "n2", type: "AGENT", label: "🔬 Research Agent: Benchmark", config: {} },
        { id: "n3", type: "AGENT", label: "💻 Coding Agent: Run Tests", config: {} },
        { id: "n4", type: "OUTPUT", label: "📢 Save to Live Canvas", config: {} }
      ]
    });
    toast.success("Workflow created!", { icon: "✓" });
    setShowNewModal(false);
    setTitleInput("");
    setDescInput("");
    loadWorkflows();
  };

  const nodeTypeColors = {
    TRIGGER: "border-amber-500/50 bg-amber-500/10 text-amber-300",
    AI: "border-indigo-500/50 bg-indigo-500/10 text-indigo-300",
    AGENT: "border-violet-500/50 bg-violet-500/10 text-violet-300",
    TOOL: "border-cyan-500/50 bg-cyan-500/10 text-cyan-300",
    OUTPUT: "border-emerald-500/50 bg-emerald-500/10 text-emerald-300"
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 text-white shadow-lg shadow-indigo-500/20">
            <FaProjectDiagram size={16} />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Visual AI Workflow Builder & Automations
            </h1>
            <p className="text-xs text-gray-400">
              Connect Triggers → Agents → Tools → Automations in unified reactive pipelines
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowNewModal(true)}
          className="flex items-center gap-1.5 px-3.5 py-2 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl font-bold transition shadow cursor-pointer text-xs"
        >
          <FaPlus size={10} />
          <span>New Workflow</span>
        </button>
      </div>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Workflows List (35%) */}
        <div className="w-96 bg-[#0F1117] border-r border-[#242833] overflow-y-auto p-4 space-y-3 custom-scrollbar">
          <span className="text-[10px] font-mono text-gray-500 uppercase block font-bold">
            Active Pipelines ({workflows.length})
          </span>

          {workflows.map((wf) => (
            <div
              key={wf.id}
              onClick={() => setActiveWf(wf)}
              className={`p-4 rounded-2xl cursor-pointer transition-all space-y-2 ${
                activeWf?.id === wf.id
                  ? "bg-[#1E293B] border border-[#6366F1]/50 shadow-lg"
                  : "bg-[#151821] hover:bg-[#1C202B] border border-[#242833]"
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                  ACTIVE
                </span>
                <span className="text-gray-400">{wf.schedule_cron || "Manual Trigger"}</span>
              </div>
              <h3 className="font-bold text-xs text-white">
                {wf.title}
              </h3>
              <p className="text-[11px] text-gray-400 line-clamp-2">
                {wf.description}
              </p>
              <div className="pt-2 border-t border-[#242833] flex items-center justify-between text-[10px] font-mono text-gray-500">
                <span>Runs: {wf.run_count || 0}</span>
                <span>Last: {wf.last_run_status || "SUCCESS"}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Right Side: Visual Node Pipeline Editor (65%) */}
        <div className="flex-1 bg-[#0B0F19] overflow-y-auto p-6 space-y-6 custom-scrollbar flex flex-col">
          {activeWf ? (
            <div className="max-w-3xl w-full mx-auto space-y-6">
              <div className="flex items-center justify-between pb-3 border-b border-[#242833]">
                <div>
                  <h2 className="text-base font-bold text-white">{activeWf.title}</h2>
                  <p className="text-xs text-gray-400">{activeWf.description}</p>
                </div>

                <button
                  onClick={() => handleExecute(activeWf.id)}
                  disabled={isExecuting}
                  className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:bg-gray-800 text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
                >
                  <FaPlay size={10} />
                  <span>{isExecuting ? "Executing Pipeline..." : "Run Pipeline"}</span>
                </button>
              </div>

              {/* Visual Node Chain */}
              <div className="space-y-4 pt-4">
                <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase block">
                  Pipeline Execution Flow ({activeWf.nodes?.length || 0} Nodes)
                </span>

                <div className="space-y-3">
                  {(activeWf.nodes || []).map((node, idx) => (
                    <div key={node.id || idx} className="relative">
                      <div className={`p-4 rounded-2xl border ${nodeTypeColors[node.type] || nodeTypeColors.AI} flex items-center justify-between gap-3 shadow-md`}>
                        <div className="flex items-center gap-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-black/40">
                            {node.type}
                          </span>
                          <span className="font-bold text-xs text-white">
                            {node.label}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-emerald-400">
                          ✓ Verified
                        </span>
                      </div>

                      {idx < (activeWf.nodes?.length || 0) - 1 && (
                        <div className="flex justify-center my-1.5 text-indigo-400">
                          ↓
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select or create a workflow to view pipeline
            </div>
          )}
        </div>
      </div>

      {/* New Workflow Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-lg bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Create AI Workflow</h3>
            <input
              type="text"
              value={titleInput}
              onChange={(e) => setTitleInput(e.target.value)}
              placeholder="Workflow Title..."
              className="w-full bg-[#08090D] border border-[#242833] rounded-xl p-3 text-xs text-white outline-none focus:border-indigo-500"
            />
            <textarea
              value={descInput}
              onChange={(e) => setDescInput(e.target.value)}
              placeholder="Workflow Description..."
              rows={2}
              className="w-full bg-[#08090D] border border-[#242833] rounded-xl p-3 text-xs text-white outline-none resize-none"
            />
            <div>
              <label className="text-[10px] font-mono text-gray-400 block mb-1">Automation Schedule</label>
              <input
                type="text"
                value={cronInput}
                onChange={(e) => setCronInput(e.target.value)}
                placeholder="e.g. Every Monday at 9:00 AM"
                className="w-full bg-[#08090D] border border-[#242833] rounded-xl p-2.5 text-xs text-white outline-none"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowNewModal(false)}
                className="px-4 py-2 bg-[#151821] text-gray-300 rounded-xl font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl font-bold cursor-pointer transition shadow"
              >
                Create Workflow
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
