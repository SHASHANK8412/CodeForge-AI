import React, { useState, useEffect } from "react";
import { 
  FaSave, FaHistory, FaDownload, FaExpand, FaCompress, FaUndo, 
  FaRedo, FaMagic, FaTimes, FaCheck, FaFileAlt, FaCode, 
  FaProjectDiagram, FaTable, FaChartBar, FaBrain, FaShareAlt, FaPlus
} from "react-icons/fa";
import DocumentCanvas from "./DocumentCanvas";
import CodeCanvas from "./CodeCanvas";
import RoadmapCanvas from "./RoadmapCanvas";
import TableCanvas from "./TableCanvas";
import DiagramCanvas from "./DiagramCanvas";
import VisualizationCanvas from "./VisualizationCanvas";
import { updateCanvas, aiTransformCanvas, restoreCanvasVersion } from "../../services/canvasApi";
import toast from "react-hot-toast";

export default function LiveCanvasContainer({ 
  canvas, 
  onUpdateCanvas, 
  isFullscreen, 
  onToggleFullscreen,
  onCreateNewCanvas
}) {
  const [currentContent, setCurrentContent] = useState(canvas?.content);
  const [currentFiles, setCurrentFiles] = useState(canvas?.files || {});
  const [currentTitle, setCurrentTitle] = useState(canvas?.title);
  const [canvasType, setCanvasType] = useState(canvas?.canvas_type || "DOCUMENT");
  const [aiPrompt, setAiPrompt] = useState("");
  const [isAiWorking, setIsAiWorking] = useState(false);
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [saveStatus, setSaveStatus] = useState("Saved");

  useEffect(() => {
    if (!canvas) return;
    setCurrentContent(canvas.content);
    setCurrentFiles(canvas.files || {});
    setCurrentTitle(canvas.title);
    setCanvasType(canvas.canvas_type || "DOCUMENT");
  }, [canvas?.id]);

  if (!canvas) return null;

  const handleContentChange = (newContent) => {
    setCurrentContent(newContent);
    setSaveStatus("Saving...");
    // Debounced autosave
    const timer = setTimeout(async () => {
      await updateCanvas(canvas.id, {
        content: newContent,
        title: currentTitle,
        files: currentFiles,
        change_summary: "Autosave"
      });
      setSaveStatus("Saved");
    }, 1000);
    return () => clearTimeout(timer);
  };

  const handleAiTransform = async (instruction, selectionText = null) => {
    if (!instruction.trim()) return;
    setIsAiWorking(true);
    toast("AI transforming canvas...", { icon: "✨" });

    try {
      const updated = await aiTransformCanvas(canvas.id, {
        instruction,
        selectionText
      });
      if (updated) {
        setCurrentContent(updated.content);
        setCurrentFiles(updated.files || {});
        setCanvasType(updated.canvas_type);
        if (onUpdateCanvas) onUpdateCanvas(updated);
        toast.success("Canvas updated by AI!", { icon: "🎨" });
      }
    } catch (err) {
      toast.error("AI Transform failed");
    } finally {
      setIsAiWorking(false);
      setAiPrompt("");
    }
  };

  const handleRestoreVersion = async (versionId) => {
    const updated = await restoreCanvasVersion(canvas.id, versionId);
    if (updated) {
      setCurrentContent(updated.content);
      setCurrentFiles(updated.files || {});
      setCanvasType(updated.canvas_type);
      setShowVersionModal(false);
      toast.success("Restored previous version!", { icon: "⏱️" });
    }
  };

  const handleExport = (format) => {
    const contentString = typeof currentContent === "string" 
      ? currentContent 
      : JSON.stringify(currentContent, null, 2);

    const blob = new Blob([contentString], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentTitle.toLowerCase().replace(/\s+/g, "_")}.${format === "json" ? "json" : format === "code" ? "py" : "md"}`;
    a.click();
    toast.success(`Exported as .${format}!`);
  };

  return (
    <div className="h-full flex flex-col bg-[#0B0F19] text-[#F5F7FA] font-sans border-l border-[#242833] overflow-hidden">
      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 bg-[#0F1117] border-b border-[#242833] select-none text-xs">
        {/* Title and Type Selector */}
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 font-bold">
            🎨 Live Canvas
          </span>

          <input
            type="text"
            value={currentTitle}
            onChange={(e) => setCurrentTitle(e.target.value)}
            onBlur={async () => {
              await updateCanvas(canvas.id, { title: currentTitle });
            }}
            className="bg-transparent font-bold text-white text-xs outline-none border-b border-transparent focus:border-indigo-500 truncate max-w-[200px]"
          />

          <select
            value={canvasType}
            onChange={async (e) => {
              const newType = e.target.value;
              setCanvasType(newType);
              const updated = await updateCanvas(canvas.id, { canvas_type: newType });
              if (onUpdateCanvas) onUpdateCanvas(updated);
            }}
            className="bg-[#151821] border border-[#242833] rounded-lg px-2 py-1 text-[11px] text-[#9AA1B2] outline-none cursor-pointer"
          >
            <option value="DOCUMENT">Document</option>
            <option value="CODE">Code Workspace</option>
            <option value="ROADMAP">Roadmap</option>
            <option value="TABLE">Table / Matrix</option>
            <option value="DIAGRAM">Architecture Diagram</option>
            <option value="VISUALIZATION">Visualization</option>
          </select>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>{saveStatus}</span>
          </span>

          <button
            onClick={() => setShowVersionModal(true)}
            className="flex items-center gap-1 px-2.5 py-1 bg-[#151821] hover:bg-[#1E2330] text-gray-300 border border-[#242833] rounded-lg text-[11px] font-semibold transition cursor-pointer"
            title="Version History"
          >
            <FaHistory size={10} />
            <span>v{canvas.versions?.length || 1}</span>
          </button>

          <button
            onClick={() => handleExport("md")}
            className="p-1.5 bg-[#151821] hover:bg-[#1E2330] text-gray-300 border border-[#242833] rounded-lg transition"
            title="Export Markdown"
          >
            <FaDownload size={11} />
          </button>

          <button
            onClick={onToggleFullscreen}
            className="p-1.5 bg-[#151821] hover:bg-[#1E2330] text-gray-300 border border-[#242833] rounded-lg transition"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? <FaCompress size={11} /> : <FaExpand size={11} />}
          </button>
        </div>
      </div>

      {/* AI Contextual Transform Bar */}
      <div className="px-4 py-2 bg-[#12151F] border-b border-[#1C202B] flex items-center gap-2 text-xs">
        <FaMagic className="text-indigo-400 shrink-0" size={11} />
        <input
          type="text"
          value={aiPrompt}
          onChange={(e) => setAiPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && aiPrompt.trim()) {
              handleAiTransform(aiPrompt);
            }
          }}
          placeholder="Ask AI to modify canvas... e.g. 'Make section 2 shorter', 'Turn into presentation', 'Add pricing column'"
          disabled={isAiWorking}
          className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-[11px] font-medium"
        />
        <button
          onClick={() => handleAiTransform(aiPrompt)}
          disabled={!aiPrompt.trim() || isAiWorking}
          className="px-3 py-1 bg-[#6366F1] hover:bg-[#5053e1] disabled:bg-gray-800 disabled:text-gray-600 text-white rounded-lg text-[11px] font-bold transition cursor-pointer"
        >
          {isAiWorking ? "Working..." : "Transform"}
        </button>
      </div>

      {/* Main Canvas Body */}
      <div className="flex-1 overflow-hidden relative">
        {canvasType === "DOCUMENT" && (
          <DocumentCanvas 
            content={currentContent} 
            onChange={handleContentChange} 
            onAiTransform={handleAiTransform} 
          />
        )}
        {canvasType === "CODE" && (
          <CodeCanvas 
            content={currentContent} 
            files={currentFiles}
            onChange={handleContentChange}
            onFilesChange={(newFiles) => {
              setCurrentFiles(newFiles);
              updateCanvas(canvas.id, { files: newFiles });
            }}
            onAiTransform={handleAiTransform} 
          />
        )}
        {canvasType === "ROADMAP" && (
          <RoadmapCanvas 
            content={currentContent} 
            onChange={handleContentChange} 
            onAiTransform={handleAiTransform} 
          />
        )}
        {canvasType === "TABLE" && (
          <TableCanvas 
            content={currentContent} 
            onChange={handleContentChange} 
            onAiTransform={handleAiTransform} 
          />
        )}
        {canvasType === "DIAGRAM" && (
          <DiagramCanvas 
            content={currentContent} 
            onChange={handleContentChange} 
            onAiTransform={handleAiTransform} 
          />
        )}
        {canvasType === "VISUALIZATION" && (
          <VisualizationCanvas 
            content={currentContent} 
            onChange={handleContentChange} 
            onAiTransform={handleAiTransform} 
          />
        )}
      </div>

      {/* Version History Modal */}
      {showVersionModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in text-xs">
          <div 
            className="w-full max-w-md bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl space-y-4 glow-violet flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#242833]">
              <div className="flex items-center gap-2">
                <FaHistory className="text-indigo-400" size={13} />
                <h3 className="text-sm font-bold text-white">Canvas Version History</h3>
              </div>
              <button
                onClick={() => setShowVersionModal(false)}
                className="text-gray-500 hover:text-white p-1"
              >
                <FaTimes size={12} />
              </button>
            </div>

            <div className="max-h-72 overflow-y-auto space-y-2.5 custom-scrollbar pr-1">
              {(canvas.versions || []).slice().reverse().map((ver) => (
                <div 
                  key={ver.version_id}
                  className="p-3 bg-[#151821] border border-[#242833] rounded-2xl flex items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-0.5 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-white">v{ver.version_number}</span>
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono ${ver.author === "AI" ? "bg-indigo-500/20 text-indigo-300" : "bg-slate-800 text-slate-300"}`}>
                        {ver.author}
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-400 truncate">
                      {ver.change_summary}
                    </p>
                    <span className="text-[9px] font-mono text-gray-500">
                      {ver.created_at}
                    </span>
                  </div>

                  <button
                    onClick={() => handleRestoreVersion(ver.version_id)}
                    className="px-2.5 py-1 bg-[#1E293B] hover:bg-[#6366F1] text-gray-200 hover:text-white rounded-lg text-[10px] font-bold transition shrink-0 cursor-pointer"
                  >
                    Restore
                  </button>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-[#242833] flex justify-end">
              <button
                onClick={() => setShowVersionModal(false)}
                className="px-4 py-1.5 bg-[#151821] hover:bg-[#1E2330] text-gray-300 rounded-xl text-xs font-semibold cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
