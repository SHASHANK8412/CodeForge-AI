import React from "react";
import { FaCheckCircle, FaClock, FaArrowDown, FaPlus, FaTrash, FaMagic, FaRegCircle } from "react-icons/fa";

export default function RoadmapCanvas({ 
  content = [], 
  onChange, 
  onAiTransform, 
  isReadOnly = false 
}) {
  const roadmapNodes = Array.isArray(content) ? content : [];

  const handleUpdateNode = (index, field, value) => {
    const updated = [...roadmapNodes];
    updated[index] = { ...updated[index], [field]: value };
    if (onChange) onChange(updated);
  };

  const handleAddNode = () => {
    const nextIdx = roadmapNodes.length + 1;
    const newNode = {
      phase: String(nextIdx).padStart(2, "0"),
      title: `Phase ${nextIdx}: New Milestone`,
      duration: `Week ${nextIdx}`,
      status: "UPCOMING",
      description: "Define learning objectives, architecture goals, and deliverables.",
      milestones: ["Task 1", "Task 2"]
    };
    if (onChange) onChange([...roadmapNodes, newNode]);
  };

  const handleDeleteNode = (index) => {
    const updated = roadmapNodes.filter((_, i) => i !== index);
    if (onChange) onChange(updated);
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 font-sans text-xs custom-scrollbar">
      {/* Roadmap Action Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-[#242833]">
        <div>
          <h2 className="text-sm font-bold text-white">Visual Execution Roadmap</h2>
          <span className="text-[10px] text-indigo-400 font-mono">
            {roadmapNodes.length} Sequential Milestones
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onAiTransform("Condense roadmap schedule into 30 Days")}
            className="px-2.5 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-indigo-300 rounded-xl font-semibold transition border border-[#242833] cursor-pointer"
          >
            ⏱️ 30-Day Schedule
          </button>

          <button
            onClick={() => onAiTransform("Expand milestone deliverables with practical capstone tasks")}
            className="px-2.5 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-violet-300 rounded-xl font-semibold transition border border-[#242833] cursor-pointer"
          >
            ✨ Add Deep Tasks
          </button>

          <button
            onClick={handleAddNode}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl font-bold transition shadow cursor-pointer"
          >
            <FaPlus size={10} /> Add Milestone
          </button>
        </div>
      </div>

      {/* Sequential Milestone Node Cards */}
      <div className="max-w-2xl mx-auto space-y-4">
        {roadmapNodes.map((node, index) => (
          <div key={index} className="relative">
            <div className="bg-[#0F1117]/95 border border-[#242833] hover:border-indigo-500/50 rounded-2xl p-5 shadow-lg space-y-3 transition-all">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="px-2 py-0.5 rounded-md bg-gradient-to-r from-[#6366F1] to-[#8D5CF6] text-white font-mono font-bold text-[11px]">
                    {node.phase || `0${index + 1}`}
                  </span>
                  <input
                    type="text"
                    value={node.title || ""}
                    onChange={(e) => handleUpdateNode(index, "title", e.target.value)}
                    disabled={isReadOnly}
                    className="bg-transparent font-bold text-white text-sm outline-none border-b border-transparent focus:border-indigo-500"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={node.duration || ""}
                    onChange={(e) => handleUpdateNode(index, "duration", e.target.value)}
                    disabled={isReadOnly}
                    className="bg-[#151821] px-2 py-0.5 rounded text-[10px] font-mono text-indigo-300 border border-[#242833] outline-none text-right"
                  />

                  <button
                    onClick={() => handleDeleteNode(index)}
                    className="text-gray-500 hover:text-rose-400 p-1"
                    title="Remove milestone"
                  >
                    <FaTrash size={10} />
                  </button>
                </div>
              </div>

              <textarea
                value={node.description || ""}
                onChange={(e) => handleUpdateNode(index, "description", e.target.value)}
                disabled={isReadOnly}
                rows={2}
                className="w-full bg-[#08090D] border border-[#1C202B] focus:border-indigo-500 rounded-xl p-2.5 text-xs text-[#9AA1B2] outline-none resize-none leading-relaxed"
              />

              {/* Milestones List */}
              {node.milestones && (
                <div className="space-y-1 pt-1">
                  <span className="text-[10px] font-mono text-gray-500 uppercase block font-bold">
                    Key Deliverables:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                    {node.milestones.map((m, mIdx) => (
                      <div key={mIdx} className="flex items-center gap-2 p-1.5 bg-[#08090D] border border-[#1C202B] rounded-lg text-[11px] text-gray-300">
                        <FaCheckCircle className="text-emerald-400 shrink-0" size={10} />
                        <span className="truncate">{m}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Connecting Arrow */}
            {index < roadmapNodes.length - 1 && (
              <div className="flex justify-center my-2 text-indigo-500">
                <FaArrowDown size={14} className="animate-pulse" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
