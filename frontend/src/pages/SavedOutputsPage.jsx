import React, { useState, useEffect, useMemo } from "react";
import { 
  FaBookmark, FaSearch, FaCopy, FaCheck, FaTrash, FaPlus, 
  FaCode, FaFileAlt, FaBrain, FaExternalLinkAlt, FaTimes, FaDownload 
} from "react-icons/fa";
import { getSavedOutputs, deleteSavedOutputItem, saveOutputItem } from "../utils/workspaceStorage";

export default function SavedOutputsPage({ setView }) {
  const [outputs, setOutputs] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
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

  const handleDownload = (item, e) => {
    if (e) e.stopPropagation();
    const blob = new Blob([item.content || ""], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${item.title.toLowerCase().replace(/[^a-z0-9]/g, "_")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = (id, e) => {
    if (e) e.stopPropagation();
    deleteSavedOutputItem(id);
    refreshOutputs();
    if (previewItem?.id === id) setPreviewItem(null);
  };

  const handleAddSubmit = (e) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;

    saveOutputItem({
      title: newTitle.trim(),
      category: newCategory,
      type: newCategory === "Coding" ? "code" : newCategory === "Writing" ? "architecture" : "prompt",
      summary: newContent.slice(0, 120) + "...",
      content: newContent.trim(),
      tags: [newCategory, "Verified"]
    });

    setNewTitle("");
    setNewContent("");
    setShowAddModal(false);
    refreshOutputs();
  };

  const categories = ["All", "Coding", "Writing", "Study", "Research", "Productivity"];

  const filteredOutputs = useMemo(() => {
    return outputs.filter(item => {
      const matchesCat = selectedCategory === "All" || item.category === selectedCategory;
      const q = searchQuery.trim().toLowerCase();
      const matchesQuery = !q || 
        item.title.toLowerCase().includes(q) || 
        item.content.toLowerCase().includes(q) ||
        (item.tags && item.tags.some(t => t.toLowerCase().includes(q)));
      return matchesCat && matchesQuery;
    });
  }, [outputs, selectedCategory, searchQuery]);

  return (
    <div className="min-h-full p-6 md:p-8 space-y-6 text-[#F5F7FA] font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#242833]">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-amber-500/20 text-amber-400">
              <FaBookmark size={14} />
            </span>
            <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight">
              Saved AI Outputs & Blueprints
            </h1>
          </div>
          <p className="text-xs text-[#9AA1B2] mt-1">
            Store, export, and organize generated code snippets, prompt templates, and architecture RFCs
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[#8D5CF6] to-[#6366F1] hover:from-[#7c4ee4] hover:to-[#4f46e5] text-white rounded-xl text-xs font-bold transition shadow-lg shadow-violet-500/25 active:scale-95 cursor-pointer self-start md:self-auto"
        >
          <FaPlus size={11} />
          <span>Save New Snippet</span>
        </button>
      </div>

      {/* Search & Categories */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" size={12} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search saved outputs, code, or tags..."
            className="w-full bg-[#0F1117] border border-[#242833] focus:border-[#8D5CF6] rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-[#64748B] outline-none"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 custom-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-xl text-xs font-semibold transition-all shrink-0 cursor-pointer ${
                selectedCategory === cat
                  ? "bg-[#8D5CF6] text-white shadow-md shadow-violet-500/20"
                  : "bg-[#151821] hover:bg-[#1E2330] text-[#9AA1B2] hover:text-white border border-[#242833]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Outputs Grid or Empty State */}
      {filteredOutputs.length === 0 ? (
        <div className="bg-[#0F1117]/60 border border-dashed border-[#242833] rounded-2xl p-12 text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-[#151821] border border-[#242833] flex items-center justify-center mx-auto text-[#64748B]">
            <FaBookmark size={24} />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <h3 className="text-base font-bold text-white">No saved outputs found</h3>
            <p className="text-xs text-[#9AA1B2]">
              {searchQuery ? `No saved items match "${searchQuery}"` : "Save your favorite generated code snippets, prompts, and architecture designs."}
            </p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-5 py-2.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
          >
            + Create First Snippet
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredOutputs.map((item) => (
            <div
              key={item.id}
              onClick={() => setPreviewItem(item)}
              className="bg-[#0F1117]/90 hover:bg-[#151821] border border-[#242833] hover:border-[#8D5CF6]/50 rounded-2xl p-5 flex flex-col justify-between transition-all group shadow-lg cursor-pointer"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className={`px-2.5 py-0.5 rounded-full border text-[10px] font-mono font-bold ${
                    item.category === "Coding" ? "bg-violet-500/10 text-violet-400 border-violet-500/20" :
                    item.category === "Writing" ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" :
                    "bg-amber-500/10 text-amber-400 border-amber-500/20"
                  }`}>
                    {item.category}
                  </span>
                  <span className="text-[10px] text-[#64748B] font-mono">{item.created_at}</span>
                </div>

                <h3 className="text-sm font-bold text-white group-hover:text-violet-300 transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-[#9AA1B2] mt-1.5 line-clamp-3 leading-relaxed">
                  {item.summary || item.content.slice(0, 100)}
                </p>

                <div className="flex items-center gap-1.5 flex-wrap mt-3">
                  {item.tags?.map((t, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-[#08090D] border border-[#242833] text-[10px] font-mono text-[#9AA1B2] rounded-md"
                    >
                      #{t}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-[#1C202B] flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={(e) => handleCopy(item, e)}
                    className="p-2 rounded-xl bg-[#08090D] hover:bg-[#1E2330] border border-[#242833] text-[#9AA1B2] hover:text-white transition cursor-pointer"
                    title="Copy snippet"
                  >
                    {copiedId === item.id ? <FaCheck className="text-emerald-400" size={11} /> : <FaCopy size={11} />}
                  </button>
                  <button
                    onClick={(e) => handleDownload(item, e)}
                    className="p-2 rounded-xl bg-[#08090D] hover:bg-[#1E2330] border border-[#242833] text-[#9AA1B2] hover:text-white transition cursor-pointer"
                    title="Download snippet"
                  >
                    <FaDownload size={11} />
                  </button>
                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="p-2 rounded-xl bg-[#08090D] hover:bg-rose-500/20 border border-[#242833] text-[#64748B] hover:text-rose-400 transition cursor-pointer"
                    title="Delete snippet"
                  >
                    <FaTrash size={11} />
                  </button>
                </div>

                <span className="text-xs font-bold text-[#8D5CF6] group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                  Preview <FaExternalLinkAlt size={8} />
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
            className="w-full max-w-3xl bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl text-xs space-y-4 max-h-[85vh] flex flex-col glow-violet"
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
                  onClick={(e) => handleDownload(previewItem, e)}
                  className="px-3 py-2 bg-[#151821] hover:bg-[#1E2330] text-white rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5"
                >
                  <FaDownload size={10} />
                  <span>Download</span>
                </button>
                <button
                  onClick={(e) => handleCopy(previewItem, e)}
                  className="flex items-center gap-1.5 px-4 py-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
                >
                  {copiedId === previewItem.id ? <FaCheck size={11} /> : <FaCopy size={11} />}
                  <span>{copiedId === previewItem.id ? "Copied!" : "Copy Content"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Snippet Modal */}
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
