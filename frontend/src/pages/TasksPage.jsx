import React, { useState, useEffect } from "react";
import { 
  FaTasks, FaPlus, FaCheckCircle, FaClock, FaExclamationTriangle, 
  FaRobot, FaFilter, FaMagic, FaTrash, FaCheck, FaPlay, FaLightbulb
} from "react-icons/fa";
import { 
  fetchTasks, 
  createTask, 
  updateTask, 
  deleteTask, 
  fetchNextBestAction 
} from "../services/taskManagementApi";
import toast from "react-hot-toast";

export default function TasksPage({ activeProjectId = null }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [nextBestAction, setNextBestAction] = useState(null);

  // New Task Modal State
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDesc, setNewTaskDesc] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState("HIGH");
  const [newTaskAgent, setNewTaskAgent] = useState("agent-coding");

  const loadTasksData = async () => {
    try {
      const data = await fetchTasks({ projectId: activeProjectId || undefined, status: statusFilter });
      setTasks(data);
      setNextBestAction(await fetchNextBestAction(activeProjectId || undefined));
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not load your tasks.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasksData();
  }, [activeProjectId, statusFilter]);

  const runAndReload = async (action, successMessage) => {
    try {
      await action();
      toast.success(successMessage);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "The change was not saved.");
    }
    loadTasksData();
  };

  const handleStatusChange = (taskId, newStatus) =>
    runAndReload(() => updateTask(taskId, { status: newStatus }), `Task status updated to ${newStatus}`);

  const handleDelete = (taskId) => runAndReload(() => deleteTask(taskId), "Task deleted");

  const handleCreateNewTask = async () => {
    if (!newTaskTitle.trim()) return;
    await runAndReload(() => createTask({
      title: newTaskTitle.trim(),
      description: newTaskDesc.trim(),
      priority: newTaskPriority,
      status: "TODO",
      project_id: activeProjectId || undefined,
      assigned_agent: newTaskAgent
    }), "Task created");
    setShowNewTaskModal(false);
    setNewTaskTitle("");
    setNewTaskDesc("");
  };

  const priorityColors = {
    CRITICAL: "bg-rose-500/20 text-rose-300 border-rose-500/40",
    HIGH: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    MEDIUM: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
    LOW: "bg-slate-500/20 text-slate-300 border-slate-500/40"
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-y-auto custom-scrollbar p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-[#6366F1] to-[#8D5CF6] text-white shadow-lg shadow-indigo-500/20">
            <FaTasks size={18} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              Tasks
            </h1>
            <p className="text-xs text-[#9AA1B2]">
              Your task list, with the next thing to work on
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNewTaskModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
          >
            <FaPlus size={10} />
            <span>New Task</span>
          </button>
        </div>
      </div>

      {/* AI Recommendation: Next Best Action Card */}
      {nextBestAction && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-indigo-950/70 to-violet-950/70 border border-indigo-500/40 flex items-center justify-between gap-4 shadow-xl">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-300 mt-0.5">
              <FaLightbulb size={16} />
            </div>
            <div>
              <span className="text-[10px] font-mono text-indigo-300 font-bold uppercase block">
                Next up
              </span>
              <h3 className="text-sm font-bold text-white">
                {nextBestAction.recommendation}
              </h3>
              <p className="text-xs text-indigo-200 mt-0.5">
                {nextBestAction.reason}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-1 bg-[#151821] p-1 rounded-xl border border-gray-800">
          {["ALL", "TODO", "IN_PROGRESS", "REVIEW", "DONE"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition cursor-pointer ${
                statusFilter === s ? "bg-[#6366F1] text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              {s.replace("_", " ")}
            </button>
          ))}
        </div>

        <span className="text-xs text-gray-500 font-mono">
          {tasks.length} Active Items
        </span>
      </div>

      {/* Task Cards List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tasks.map((task) => (
          <div
            key={task.id}
            className="p-5 rounded-2xl bg-[#0F1117] border border-[#242833] hover:border-indigo-500/50 transition-all space-y-3 shadow-lg group"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-bold border ${priorityColors[task.priority] || priorityColors.MEDIUM}`}>
                    {task.priority}
                  </span>
                  <span className="text-[10px] font-mono text-gray-500">
                    {task.deadline || "No deadline"}
                  </span>
                </div>
                <h3 className="font-bold text-sm text-white group-hover:text-indigo-300 transition">
                  {task.title}
                </h3>
              </div>

              <button
                onClick={() => handleDelete(task.id)}
                className="text-gray-600 hover:text-rose-400 p-1 opacity-0 group-hover:opacity-100 transition"
              >
                <FaTrash size={11} />
              </button>
            </div>

            <p className="text-xs text-gray-400 leading-relaxed">
              {task.description}
            </p>

            <div className="pt-2 border-t border-[#1C202B] flex items-center justify-between text-xs">
              <div className="flex items-center gap-1.5 text-indigo-400 font-mono text-[11px]">
                <FaRobot size={11} />
                <span>{task.assigned_agent || "Unassigned"}</span>
              </div>

              {/* Status Action Dropdown */}
              <select
                value={task.status}
                onChange={(e) => handleStatusChange(task.id, e.target.value)}
                className="bg-[#151821] border border-[#242833] rounded-lg px-2 py-1 text-[11px] font-mono text-gray-300 outline-none cursor-pointer"
              >
                <option value="TODO">TODO</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="REVIEW">REVIEW</option>
                <option value="DONE">DONE</option>
              </select>
            </div>
          </div>
        ))}
      </div>

      {/* New Task Modal */}
      {showNewTaskModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in text-xs">
          <div className="w-full max-w-lg bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Create New Task</h3>
            <input
              type="text"
              value={newTaskTitle}
              onChange={(e) => setNewTaskTitle(e.target.value)}
              placeholder="Task Title..."
              className="w-full bg-[#08090D] border border-[#242833] rounded-xl p-3 text-xs text-white outline-none focus:border-indigo-500"
            />
            <textarea
              value={newTaskDesc}
              onChange={(e) => setNewTaskDesc(e.target.value)}
              placeholder="Task Description..."
              rows={3}
              className="w-full bg-[#08090D] border border-[#242833] rounded-xl p-3 text-xs text-white outline-none resize-none focus:border-indigo-500"
            />
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] font-mono text-gray-400 block mb-1">Priority</label>
                <select
                  value={newTaskPriority}
                  onChange={(e) => setNewTaskPriority(e.target.value)}
                  className="w-full bg-[#08090D] border border-[#242833] rounded-xl p-2.5 text-xs text-white outline-none"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] font-mono text-gray-400 block mb-1">Assigned Agent</label>
                <select
                  value={newTaskAgent}
                  onChange={(e) => setNewTaskAgent(e.target.value)}
                  className="w-full bg-[#08090D] border border-[#242833] rounded-xl p-2.5 text-xs text-white outline-none"
                >
                  <option value="agent-coding">Coding Agent</option>
                  <option value="agent-research">Research Agent</option>
                  <option value="agent-study">Study Agent</option>
                  <option value="agent-data-analyst">Data Analyst Agent</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowNewTaskModal(false)}
                className="px-4 py-2 bg-[#151821] text-gray-300 rounded-xl font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateNewTask}
                className="px-4 py-2 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl font-bold cursor-pointer transition"
              >
                Create Task
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
