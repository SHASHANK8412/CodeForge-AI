import React, { useState, useEffect } from "react";
import { 
  FaPaintBrush, FaRobot, FaPaperPlane, FaPlus, FaFolder, 
  FaBrain, FaColumns, FaExpand, FaCompress, FaMagic, FaSlidersH
} from "react-icons/fa";
import LiveCanvasContainer from "../components/canvas/LiveCanvasContainer";
import { fetchCanvases, createCanvas, fetchCanvas } from "../services/canvasApi";
import { sendMessage } from "../services/api";
import toast from "react-hot-toast";

export default function LiveCanvasPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [canvases, setCanvases] = useState([]);
  const [activeCanvas, setActiveCanvas] = useState(null);
  const [loading, setLoading] = useState(true);

  // Chat State
  const [chatMessages, setChatMessages] = useState([
    { sender: "ai", text: "Hello! I'm your Live Canvas Assistant. I can generate roadmaps, code workspaces, comparison matrices, and architecture diagrams directly on your canvas. Tell me what you'd like to build!" }
  ]);
  const [promptInput, setPromptInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  // Layout State
  const [mobileTab, setMobileTab] = useState("canvas"); // "chat" or "canvas"
  const [isFullscreenCanvas, setIsFullscreenCanvas] = useState(false);
  const [splitRatio, setSplitRatio] = useState(40); // 40% Chat, 60% Canvas

  const loadCanvasesData = async () => {
    try {
      const list = await fetchCanvases({ projectId: activeProjectId });
      setCanvases(list || []);
      if (!activeCanvas && list && list.length > 0) {
        setActiveCanvas(list[0]);
      }
    } catch (err) {
      console.error("Error loading canvases:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCanvasesData();
    const handleUpdate = () => loadCanvasesData();
    window.addEventListener("aiforge:canvas-updated", handleUpdate);
    return () => window.removeEventListener("aiforge:canvas-updated", handleUpdate);
  }, [activeProjectId]);

  const handleSendChat = async (textToSend = null) => {
    const text = textToSend || promptInput;
    if (!text.trim() || isSending) return;

    const userMsg = { sender: "user", text: text.trim() };
    setChatMessages((prev) => [...prev, userMsg]);
    setPromptInput("");
    setIsSending(true);

    const q = text.toLowerCase();

    // Check if the chat should create or switch canvas
    setTimeout(async () => {
      let aiReply = "I have updated the Live Canvas workspace based on your instructions.";

      if (q.includes("roadmap") || q.includes("learning")) {
        const target = canvases.find(c => c.canvas_type === "ROADMAP") || canvases[0];
        if (target) setActiveCanvas(target);
        aiReply = "I've loaded and aligned the **Machine Learning Roadmap Canvas** on your right. You can ask me to modify phases, shorten to 30 days, or expand capstone milestones.";
      } else if (q.includes("table") || q.includes("compare") || q.includes("matrix")) {
        const target = canvases.find(c => c.canvas_type === "TABLE") || canvases[1];
        if (target) setActiveCanvas(target);
        aiReply = "I've pulled up the **Frontend Frameworks Matrix Canvas**. Try asking: *'Add a pricing column'* or *'Sort by performance'*!";
      } else if (q.includes("code") || q.includes("backend") || q.includes("fastapi")) {
        const target = canvases.find(c => c.canvas_type === "CODE") || canvases[2];
        if (target) setActiveCanvas(target);
        aiReply = "Opened the **Async Task Queue Code Canvas**. You can view multiple files, run the sandbox, or ask me to refactor.";
      } else if (q.includes("prd") || q.includes("document") || q.includes("spec")) {
        const target = canvases.find(c => c.canvas_type === "DOCUMENT") || canvases[3];
        if (target) setActiveCanvas(target);
        aiReply = "Loaded the **Product Requirement Document (PRD) Canvas**. Select any sentence to trigger contextual AI improvements.";
      }

      setChatMessages((prev) => [...prev, { sender: "ai", text: aiReply }]);
      setIsSending(false);
    }, 900);
  };

  const handleCreateNew = async () => {
    const title = prompt("Enter new canvas title:");
    if (!title || !title.trim()) return;

    const created = await createCanvas({
      title: title.trim(),
      canvas_type: "DOCUMENT",
      project_id: activeProjectId
    });

    toast.success(`Created Canvas: ${created.title}!`, { icon: "🎨" });
    setActiveCanvas(created);
    loadCanvasesData();
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      {/* Top Split Header / Canvas Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-3 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-[#6366F1] to-[#8D5CF6] text-white shadow-md shadow-indigo-500/20">
            <FaPaintBrush size={13} />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white flex items-center gap-2">
              AIForge Live Canvas
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono text-[10px]">
                Interactive Split Workspace
              </span>
            </h1>
          </div>
        </div>

        {/* Canvas Switcher Selector & New Button */}
        <div className="flex items-center gap-2">
          <select
            value={activeCanvas?.id || ""}
            onChange={(e) => {
              const selected = canvases.find(c => c.id === e.target.value);
              if (selected) setActiveCanvas(selected);
            }}
            className="bg-[#1E293B] border border-gray-800 text-white rounded-xl px-3 py-1.5 outline-none text-xs focus:border-[#6366F1] cursor-pointer max-w-[220px] truncate"
          >
            {canvases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.canvas_type === "ROADMAP" ? "🗺️" : c.canvas_type === "TABLE" ? "📊" : c.canvas_type === "CODE" ? "💻" : "📝"} {c.title}
              </option>
            ))}
          </select>

          <button
            onClick={handleCreateNew}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl font-bold transition shadow text-xs cursor-pointer"
          >
            <FaPlus size={10} />
            <span>New Canvas</span>
          </button>
        </div>

        {/* Mobile View Switcher */}
        <div className="flex md:hidden items-center gap-1 bg-[#151821] p-1 rounded-xl border border-gray-800">
          <button
            onClick={() => setMobileTab("chat")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold ${mobileTab === "chat" ? "bg-[#6366F1] text-white" : "text-gray-400"}`}
          >
            AI Chat
          </button>
          <button
            onClick={() => setMobileTab("canvas")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold ${mobileTab === "canvas" ? "bg-[#6366F1] text-white" : "text-gray-400"}`}
          >
            Live Canvas
          </button>
        </div>
      </div>

      {/* Main Split Screen Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: AI Chat & Prompts (Desktop ~40%) */}
        <div 
          className={`flex flex-col bg-[#0F1117] border-r border-[#242833] ${
            isFullscreenCanvas ? "hidden" : mobileTab === "chat" ? "w-full flex" : "hidden md:flex"
          }`}
          style={{ width: isFullscreenCanvas ? "0%" : `${splitRatio}%` }}
        >
          {/* Chat Messages Log */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5 custom-scrollbar">
            {chatMessages.map((msg, idx) => (
              <div 
                key={idx}
                className={`flex gap-2.5 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.sender === "ai" && (
                  <div className="w-7 h-7 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 text-xs font-bold">
                    🤖
                  </div>
                )}
                <div 
                  className={`p-3 rounded-2xl max-w-[85%] text-xs leading-relaxed ${
                    msg.sender === "user" 
                      ? "bg-gradient-to-r from-[#6366F1] to-[#8D5CF6] text-white rounded-br-none shadow-md" 
                      : "bg-[#151821] border border-[#242833] text-gray-200 rounded-bl-none"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {isSending && (
              <div className="flex items-center gap-2 text-indigo-400 text-xs italic animate-pulse">
                <span>🤖 AI syncing with Live Canvas...</span>
              </div>
            )}
          </div>

          {/* Preset Canvas Quick Action Prompts */}
          <div className="p-2.5 bg-[#0A0C10] border-t border-[#1C202B] flex items-center gap-1.5 overflow-x-auto custom-scrollbar">
            {[
              { label: "🗺️ ML Roadmap", prompt: "Build me a roadmap for learning machine learning" },
              { label: "📊 React vs Vue", prompt: "Create a comparison table of React, Vue, and Angular" },
              { label: "💻 Task Queue Code", prompt: "Create an async task queue in Python" },
              { label: "📝 PRD Specs", prompt: "Generate a product requirements document for FoodDelivery AI" },
            ].map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSendChat(p.prompt)}
                className="px-2.5 py-1 rounded-lg bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-[10px] font-semibold text-gray-300 hover:text-white transition shrink-0 cursor-pointer"
              >
                {p.label}
              </button>
            ))}
          </div>

          {/* Chat Input Console */}
          <div className="p-3 bg-[#0F1117] border-t border-[#242833] flex items-center gap-2">
            <input
              type="text"
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSendChat();
              }}
              placeholder="Ask AI to create or modify canvas..."
              className="flex-1 bg-[#08090D] border border-[#242833] focus:border-indigo-500 rounded-xl px-3 py-2 text-xs text-white placeholder-gray-500 outline-none"
            />
            <button
              onClick={() => handleSendChat()}
              disabled={!promptInput.trim() || isSending}
              className="p-2.5 bg-[#6366F1] hover:bg-[#5053e1] disabled:bg-gray-800 text-white rounded-xl transition cursor-pointer"
            >
              <FaPaperPlane size={11} />
            </button>
          </div>
        </div>

        {/* Right Side: Interactive Live Canvas (Desktop ~60%) */}
        <div 
          className={`flex-1 flex flex-col bg-[#0B0F19] overflow-hidden ${
            mobileTab === "canvas" ? "flex" : "hidden md:flex"
          }`}
        >
          {activeCanvas ? (
            <LiveCanvasContainer
              canvas={activeCanvas}
              onUpdateCanvas={(updated) => {
                setActiveCanvas(updated);
                setCanvases((prev) => prev.map(c => c.id === updated.id ? updated : c));
              }}
              isFullscreen={isFullscreenCanvas}
              onToggleFullscreen={() => setIsFullscreenCanvas(!isFullscreenCanvas)}
              onCreateNewCanvas={handleCreateNew}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              Select or create a canvas to get started
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
