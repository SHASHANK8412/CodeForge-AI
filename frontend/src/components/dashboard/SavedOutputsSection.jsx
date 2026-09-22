import React, { useState, useEffect, useMemo } from "react";
import { 
  FaBookmark, FaCopy, FaCheck, FaTrash, FaPlus, FaExternalLinkAlt, 
  FaSearch, FaCode, FaFileAlt, FaBrain, FaTimes
} from "react-icons/fa";
import { getSavedOutputs, deleteSavedOutputItem, saveOutputItem } from "../../utils/workspaceStorage";

export default function SavedOutputsSection({ setView }) {
  const [outputs, setOutputs] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedId, setCopiedId] = useState(null);
  const [previewItem, setPreviewItem] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newCategory, setNewCategory] = useState("Coding");
  const [newContent, setNewContent] = useState("");

  const refreshOutputs = () => {
    setOutputs(getSavedOutputs());
  };

  useEffect(() => {
    refreshOutputs();
    const handleUpdate = () => refreshOutputs();
    window.addEventListener("aiforge:saved-outputs-updated", handleUpdate);
    return () => window.removeEventListener("aiforge:saved-outputs-updated", handleUpdate);
  }, []);

  const handleCopy = (item, e) => {
    if (e) e.stopPropagation();
    navigator.clipboard.writeText(item.content || "");
    setCopiedId(item.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDelete = (id, e) => {
    if (e) e.stopPropagation();
    deleteSavedOutputItem(id);
    refreshOutputs();
  };

  const handleAddSubmit = (e) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;

    saveOutputItem({
      title: newTitle.trim(),
      category: newCategory,
      type: newCategory === "Coding" ? "code" : newCategory === "Writing" ? "architecture" : "prompt",
      summary: newContent.slice(0, 100) + "...",
      content: newContent.trim(),
      tags: [newCategory, "Custom"]
    });

    setNewTitle("");
    setNewContent("");
    setShowAddModal(false);
    refreshOutputs();
  };

  const filteredOutputs = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return outputs;
    return outputs.filter(item => 
      item.title.toLowerCase().includes(q) || 
      item.category.toLowerCase().includes(q) || 
      (item.tags && item.tags.some(t => t.toLowerCase().includes(q)))
    );
  }, [outputs, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-md bg-amber-500/20 text-amber-400">
              <FaBookmark size={12} />
            </span>
            <h2 className="text-sm font-bold text-white tracking-tight">
              Saved AI Outputs & Blueprints
            </h2>
          </div>
          <p className="text-[11px] text-[#64748B] mt-0.5">
            Quickly access, copy, and reuse verified generated code snippets, prompts, and architecture RFCs
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#151821] hover:bg-[#1E2330] border border-[#242833] hover:border-[#8D5CF6] text-white rounded-xl text-xs font-semibold transition active:scale-95 cursor-pointer"
          >
            <FaPlus size={10} className="text-[#8D5CF6]" />
            <span>Save Snippet</span>
          </button>
          {setView && (
            <button
              onClick={() => setView("saved")}
              className="text-xs text-[#8D5CF6] hover:text-[#a78bfa] font-semibold transition px-2 py-1 cursor-pointer"
            >
              View Library →
            </button>
          )}
        </div>
      </div>

      {/* Outputs List or Empty State */}
      {filteredOutputs.length === 0 ? (
        <div className="bg-[#0F1117]/60 border border-dashed border-[#242833] rounded-2xl p-8 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-[#151821] border border-[#242833] flex items-center justify-center mx-auto text-[#64748B]">
            <FaBookmark size={20} />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <h3 className="text-sm font-bold text-white">No saved AI outputs found</h3>
            <p className="text-xs text-[#9AA1B2]">
              Save generated code snippets, prompt templates, or architectural RFCs from AI Chat and Command Center.
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
          >
            + Create First Snippet
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {filteredOutputs.slice(0, 4).map((item) => (
            <div
              key={item.id}
              onClick={() => setPreviewItem(item)}
              className="bg-[#0F1117]/80 hover:bg-[#151821] border border-[#242833] hover:border-[#8D5CF6]/50 rounded-2xl p-4 flex flex-col justify-between transition-all group cursor-pointer relative"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className={`px-2 py-0.5 rounded-full border text-[10px] font-mono font-bold ${
                    item.category === "Coding" ? "bg-violet-500/10 text-violet-400 border-violet-500/20" :
                    item.category === "Writing" ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" :
                    "bg-amber-500/10 text-amber-400 border-amber-500/20"
                  }`}>
                    {item.category}
                  </span>
                  <span className="text-[10px] text-[#64748B] font-mono">{item.created_at}</span>
                </div>

                <h3 className="text-xs font-bold text-white group-hover:text-violet-300 transition-colors line-clamp-2">
                  {item.title}
                </h3>

                <p className="text-[11px] text-[#9AA1B2] mt-1.5 line-clamp-2 leading-relaxed font-sans">
                  {item.summary || item.content.slice(0, 80)}
                </p>
              </div>

              <div className="pt-3 mt-3 border-t border-[#1C202B] flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={(e) => handleCopy(item, e)}
                    className="p-1.5 rounded-lg bg-[#151821] hover:bg-[#1E2330] text-[#9AA1B2] hover:text-white transition cursor-pointer"
                    title="Copy content"
                  >
                    {copiedId === item.id ? <FaCheck className="text-emerald-400" size={10} /> : <FaCopy size={10} />}
                  </button>
                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="p-1.5 rounded-lg bg-[#151821] hover:bg-rose-500/20 text-[#64748B] hover:text-rose-400 transition cursor-pointer"
                    title="Delete item"
                  >
                    <FaTrash size={10} />
                  </button>
                </div>
                <span className="text-xs font-bold text-[#8D5CF6] group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                  View <FaExternalLinkAlt size={8} />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div 
            className="w-full max-w-2xl bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl text-xs space-y-4 max-h-[85vh] flex flex-col glow-violet"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#242833]">
              <div className="space-y-0.5">
                <span className="text-[10px] uppercase font-bold text-violet-400 font-mono">
                  {previewItem.category} Output
                </span>
                <h3 className="text-base font-bold text-white">{previewItem.title}</h3>
              </div>
              <button
                onClick={() => setPreviewItem(null)}
                className="text-[#64748B] hover:text-white p-1 rounded-lg transition"
              >
                <FaTimes size={14} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto bg-[#08090D] border border-[#242833] rounded-2xl p-4 custom-scrollbar">
              <pre className="font-mono text-xs text-[#F5F7FA] whitespace-pre-wrap leading-relaxed">
                {previewItem.content}
              </pre>
            </div>

            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-1.5 flex-wrap">
                {previewItem.tags?.map((t, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded-md bg-[#151821] border border-[#242833] text-[10px] text-[#9AA1B2] font-mono">
                    #{t}
                  </span>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => handleCopy(previewItem, e)}
                  className="flex items-center gap-1.5 px-4 py-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
                >
                  {copiedId === previewItem.id ? <FaCheck size={11} /> : <FaCopy size={11} />}
                  <span>{copiedId === previewItem.id ? "Copied!" : "Copy Snippet"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add New Output Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <form 
            onSubmit={handleAddSubmit}
            className="w-full max-w-lg bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl text-xs space-y-4 flex flex-col glow-violet"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#242833]">
              <h3 className="text-sm font-bold text-white">Save AI Output or Snippet</h3>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="text-[#64748B] hover:text-white p-1 rounded-lg transition"
              >
                <FaTimes size={14} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Async Redis Session Middleware"
                  required
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl px-3 py-2 text-white outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl px-3 py-2 text-white outline-none cursor-pointer"
                >
                  <option value="Coding">Coding</option>
                  <option value="Writing">Writing</option>
                  <option value="Study">Study</option>
                  <option value="Research">Research</option>
                  <option value="Productivity">Productivity</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Snippet / Content</label>
                <textarea
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="Paste code, markdown spec, or prompt here..."
                  rows={6}
                  required
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl p-3 text-white font-mono outline-none resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#242833]">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-3 py-2 text-xs text-[#9AA1B2] hover:text-white transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
              >
                Save Output
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
