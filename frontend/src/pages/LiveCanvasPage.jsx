import React, { useState, useEffect } from "react";
import { FaPaintBrush, FaPlus } from "react-icons/fa";
import LiveCanvasContainer from "../components/canvas/LiveCanvasContainer";
import { fetchCanvases, createCanvas } from "../services/canvasApi";
import toast from "react-hot-toast";

const CANVAS_TYPES = ["DOCUMENT", "CODE", "ROADMAP", "TABLE", "DIAGRAM", "VISUALIZATION"];

export default function LiveCanvasPage({ activeProjectId = null }) {
  const [canvases, setCanvases] = useState([]);
  const [activeCanvas, setActiveCanvas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [newType, setNewType] = useState("DOCUMENT");
  const [isFullscreenCanvas, setIsFullscreenCanvas] = useState(false);

  const loadCanvasesData = async () => {
    try {
      const list = await fetchCanvases({ projectId: activeProjectId || undefined });
      setCanvases(list);
      setLoadError(null);
      setActiveCanvas((current) => (current && list.find((c) => c.id === current.id)) || list[0] || null);
    } catch (err) {
      setLoadError(err?.response?.data?.detail || err?.message || "Could not load canvases.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCanvasesData();
    const handleUpdate = () => loadCanvasesData();
    window.addEventListener("aiforge:canvas-updated", handleUpdate);
    return () => window.removeEventListener("aiforge:canvas-updated", handleUpdate);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeProjectId]);

  const handleCreateNew = async () => {
    const title = prompt("Enter new canvas title:");
    if (!title || !title.trim()) return;
    try {
      const created = await createCanvas({
        title: title.trim(),
        canvas_type: newType,
        project_id: activeProjectId || undefined
      });
      toast.success(`Created canvas: ${created.title}`);
      setActiveCanvas(created);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not create the canvas.");
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-3 bg-[#0F172A] border-b border-gray-800 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-[#6366F1] to-[#8D5CF6] text-white shadow-md shadow-indigo-500/20">
            <FaPaintBrush size={13} />
          </div>
          <h1 className="text-sm font-bold text-white">Canvas</h1>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={activeCanvas?.id || ""}
            onChange={(e) => {
              const selected = canvases.find(c => c.id === e.target.value);
              if (selected) setActiveCanvas(selected);
            }}
            disabled={canvases.length === 0}
            className="bg-[#1E293B] border border-gray-800 text-white rounded-xl px-3 py-1.5 outline-none text-xs focus:border-[#6366F1] cursor-pointer max-w-[220px] truncate"
          >
            {canvases.length === 0 && <option value="">No canvases yet</option>}
            {canvases.map((c) => (
              <option key={c.id} value={c.id}>{c.title} ({c.canvas_type.toLowerCase()})</option>
            ))}
          </select>

          <select
            value={newType}
            onChange={(e) => setNewType(e.target.value)}
            className="bg-[#1E293B] border border-gray-800 text-white rounded-xl px-2 py-1.5 outline-none text-xs cursor-pointer"
            aria-label="Type of the new canvas"
          >
            {CANVAS_TYPES.map((t) => <option key={t} value={t}>{t.toLowerCase()}</option>)}
          </select>

          <button
            onClick={handleCreateNew}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#6366F1] hover:bg-[#5053e1] text-white rounded-xl font-bold transition shadow text-xs cursor-pointer"
          >
            <FaPlus size={10} />
            <span>New Canvas</span>
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
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
          <div className="h-full flex items-center justify-center text-gray-500 text-xs px-6 text-center">
            {loading ? "Loading canvases..." : loadError ? `Could not load canvases: ${loadError}` : "No canvases yet. Choose a type and click New Canvas."}
          </div>
        )}
      </div>
    </div>
  );
}
