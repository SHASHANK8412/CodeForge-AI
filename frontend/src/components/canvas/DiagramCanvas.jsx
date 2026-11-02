import React from "react";
import { FaProjectDiagram, FaServer, FaDatabase, FaBolt, FaPlus, FaBrain } from "react-icons/fa";

export default function DiagramCanvas({ 
  content = [], 
  onChange, 
  onAiTransform, 
  isReadOnly = false 
}) {
  const nodes = Array.isArray(content) ? content : [
    { id: "node-1", label: "Client Web App", category: "Frontend", x: 60, y: 100 },
    { id: "node-2", label: "FastAPI Gateway", category: "Gateway", x: 260, y: 100 },
    { id: "node-3", label: "PostgreSQL & Redis", category: "Storage", x: 480, y: 100 }
  ];

  const categoryIcons = {
    Frontend: <FaBolt className="text-violet-400" size={14} />,
    Gateway: <FaServer className="text-cyan-400" size={14} />,
    Compute: <FaBrain className="text-indigo-400" size={14} />,
    Memory: <FaBrain className="text-pink-400" size={14} />,
    Storage: <FaDatabase className="text-emerald-400" size={14} />
  };

  const handleAddNode = () => {
    const label = prompt("Enter service node name (e.g. Auth Service, Worker Pool):");
    if (!label || !label.trim()) return;
    const newNode = {
      id: `node-${Date.now()}`,
      label: label.trim(),
      category: "Compute",
      x: 200,
      y: 150
    };
    if (onChange) onChange([...nodes, newNode]);
  };

  return (
    <div className="h-full flex flex-col p-6 space-y-4 font-sans text-xs">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#242833]">
        <div>
          <h2 className="text-sm font-bold text-white">System Architecture & Service Topology</h2>
          <span className="text-[10px] text-[#64748B] font-mono">
            {nodes.length} Distributed Components
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onAiTransform("Generate an event-driven Kafka / Redis streams microservice topology")}
            className="px-2.5 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-indigo-300 rounded-xl font-semibold transition border border-[#242833] cursor-pointer"
          >
            ⚡ Event-Driven Microservices
          </button>

          <button
            onClick={handleAddNode}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl font-bold transition shadow cursor-pointer"
          >
            <FaPlus size={10} /> Add Node
          </button>
        </div>
      </div>

      {/* Visual Canvas Diagram Layout */}
      <div className="flex-1 bg-[#08090D] border border-[#242833] rounded-2xl p-6 relative overflow-auto custom-scrollbar flex flex-col justify-center items-center">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
          {nodes.map((node, idx) => (
            <div
              key={node.id || idx}
              className="p-4 rounded-2xl bg-[#0F1117]/90 border border-[#242833] hover:border-indigo-500/50 shadow-xl space-y-2 transition-all group"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-xl bg-[#151821] border border-[#242833]">
                    {categoryIcons[node.category] || <FaServer className="text-indigo-400" size={14} />}
                  </div>
                  <div>
                    <span className="font-bold text-white text-xs block">
                      {node.label}
                    </span>
                    <span className="text-[10px] font-mono text-[#64748B]">
                      {node.category || "Service"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>Healthy • 99.98% SLA</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
