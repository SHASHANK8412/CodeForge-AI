import React, { useState, useEffect, useMemo } from "react";
import { 
  FaBrain, FaPlus, FaSearch, FaFilter, FaStar, FaRegStar, 
  FaEdit, FaTrash, FaCopy, FaCheck, FaProjectDiagram, FaUser, 
  FaFolder, FaTimes, FaShieldAlt, FaLayerGroup, FaHistory, FaCheckCircle, FaExclamationTriangle
} from "react-icons/fa";
import { 
  fetchMemories, 
  createMemory, 
  updateMemory, 
  deleteMemory, 
  clearProjectMemory, 
  clearAllMemory 
} from "../services/aiMemoryApi";

export default function MemoryPage({ setView, activeProjectId = "aiforge-fooddelivery-ai" }) {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Controls
  const [scopeFilter, setScopeFilter] = useState("ALL"); // ALL, PERSONAL, PROJECT
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [projectFilter, setProjectFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("recent"); // recent, most_used, importance, title

  // Modals & Popups
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Form State
  const [formTitle, setFormTitle] = useState("");
  const [formContent, setFormContent] = useState("");
  const [formScope, setFormScope] = useState("PERSONAL");
  const [formProjectId, setFormProjectId] = useState(activeProjectId || "aiforge-fooddelivery-ai");
  const [formCategory, setFormCategory] = useState("Preferences");
  const [formImportance, setFormImportance] = useState("HIGH");
  const [formTags, setFormTags] = useState("");
  const [formPinned, setFormPinned] = useState(false);

  const categories = [
    "All", "Preferences", "Tech Stack", "Architecture", 
    "Requirements", "Conversation", "Tasks", "Rules & Constraints"
  ];

  const loadMemoriesData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMemories({
        scope: scopeFilter === "ALL" ? undefined : scopeFilter,
        projectId: projectFilter === "ALL" ? undefined : projectFilter,
        category: categoryFilter,
        search: searchQuery,
        sortBy
      });
      setMemories(data || []);
    } catch (err) {
      console.error("Failed to load memories:", err);
      setError("Failed to synchronize memories. Showing local cached items.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemoriesData();
    const handleUpdate = () => loadMemoriesData();
    window.addEventListener("aiforge:memory-updated", handleUpdate);
    return () => window.removeEventListener("aiforge:memory-updated", handleUpdate);
  }, [scopeFilter, categoryFilter, projectFilter, searchQuery, sortBy]);

  const openCreateModal = () => {
    setEditingItem(null);
    setFormTitle("");
    setFormContent("");
    setFormScope(scopeFilter === "PROJECT" ? "PROJECT" : "PERSONAL");
    setFormProjectId(activeProjectId || "aiforge-fooddelivery-ai");
    setFormCategory("Preferences");
    setFormImportance("HIGH");
    setFormTags("");
    setFormPinned(false);
    setShowModal(true);
  };

  const openEditModal = (item, e) => {
    if (e) e.stopPropagation();
    setEditingItem(item);
    setFormTitle(item.title);
    setFormContent(item.content);
    setFormScope(item.scope);
    setFormProjectId(item.project_id || activeProjectId || "aiforge-fooddelivery-ai");
    setFormCategory(item.category);
    setFormImportance(item.importance);
    setFormTags((item.tags || []).join(", "));
    setFormPinned(item.pinned || false);
    setShowModal(true);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!formTitle.trim() || !formContent.trim()) return;

    const tagsArray = formTags.split(",").map(t => t.trim()).filter(Boolean);

    if (editingItem) {
      await updateMemory(editingItem.id, {
        title: formTitle.trim(),
        content: formContent.trim(),
        scope: formScope,
        project_id: formScope === "PROJECT" ? formProjectId : null,
        category: formCategory,
        importance: formImportance,
        tags: tagsArray,
        pinned: formPinned
      });
    } else {
      await createMemory({
        title: formTitle.trim(),
        content: formContent.trim(),
        scope: formScope,
        project_id: formScope === "PROJECT" ? formProjectId : null,
        category: formCategory,
        importance: formImportance,
        tags: tagsArray,
        pinned: formPinned,
        source: "User"
      });
    }

    setShowModal(false);
    loadMemoriesData();
  };

  const handleDelete = async (memoryId, e) => {
    if (e) e.stopPropagation();
    if (!window.confirm("Forget this memory permanently?")) return;
    await deleteMemory(memoryId);
    loadMemoriesData();
  };

  const handleTogglePin = async (item, e) => {
    if (e) e.stopPropagation();
    await updateMemory(item.id, { pinned: !item.pinned });
    loadMemoriesData();
  };

  const handleCopy = (item, e) => {
    if (e) e.stopPropagation();
    navigator.clipboard.writeText(`${item.title}: ${item.content}`);
    setCopiedId(item.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClearAll = async () => {
    if (projectFilter !== "ALL") {
      await clearProjectMemory(projectFilter);
    } else {
      await clearAllMemory();
    }
    setShowClearConfirm(false);
    loadMemoriesData();
  };

  // Stats calculation
  const stats = useMemo(() => {
    const total = memories.length;
    const personalCount = memories.filter(m => m.scope === "PERSONAL").length;
    const projectCount = memories.filter(m => m.scope === "PROJECT").length;
    const totalRecalls = memories.reduce((acc, m) => acc + (m.usage_count || 0), 0);
    return { total, personalCount, projectCount, totalRecalls };
  }, [memories]);

  return (
    <div className="min-h-full p-4 sm:p-6 lg:p-8 space-y-6 text-[#F5F7FA] font-sans max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#242833]">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-[#8D5CF6] to-[#6366F1] text-white shadow-lg shadow-violet-500/25">
              <FaBrain size={16} />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
                AI Memory & Knowledge Center
              </h1>
              <span className="text-[10px] text-[#8D5CF6] font-mono uppercase tracking-widest font-bold">
                PERSISTENT CONTEXT & SMART RECALL
              </span>
            </div>
          </div>
          <p className="text-xs text-[#9AA1B2] mt-1.5 max-w-2xl">
            AIForge remembers your technical preferences, project constraints, and architectural decisions so your AI assistant gets smarter and more personalized over time.
          </p>
        </div>

        <div className="flex items-center gap-2.5 self-start md:self-auto">
          <button
            onClick={() => setShowClearConfirm(true)}
            className="px-3 py-2 bg-[#151821] hover:bg-rose-500/20 text-[#64748B] hover:text-rose-400 border border-[#242833] rounded-xl text-xs font-semibold transition cursor-pointer"
            title="Clear Stored Memories"
          >
            Clear Memory
          </button>

          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[#8D5CF6] to-[#6366F1] hover:from-[#7c4ee4] hover:to-[#4f46e5] text-white rounded-xl text-xs font-bold transition shadow-lg shadow-violet-500/25 hover:scale-[1.02] active:scale-95 cursor-pointer"
          >
            <FaPlus size={11} />
            <span>Remember This</span>
          </button>
        </div>
      </div>

      {/* Stats Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider">Total Memories</div>
          <div className="text-xl font-bold text-white">{stats.total}</div>
          <div className="text-[10px] text-[#9AA1B2]">Stored in Knowledge Graph</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider">Personal Preferences</div>
          <div className="text-xl font-bold text-violet-400">{stats.personalCount}</div>
          <div className="text-[10px] text-[#9AA1B2]">Coding Style & Tools</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider">Project Memories</div>
          <div className="text-xl font-bold text-cyan-400">{stats.projectCount}</div>
          <div className="text-[10px] text-[#9AA1B2]">Isolated Project Context</div>
        </div>

        <div className="p-4 bg-[#0F1117]/90 border border-[#242833] rounded-2xl space-y-1">
          <div className="text-[10px] font-mono text-[#64748B] uppercase tracking-wider">Smart Recalls</div>
          <div className="text-xl font-bold text-emerald-400">{stats.totalRecalls}</div>
          <div className="text-[10px] text-[#9AA1B2]">Context Injections in Chat</div>
        </div>
      </div>

      {/* Scope Switcher Tabs */}
      <div className="flex items-center gap-2 border-b border-[#242833] pb-3">
        {[
          { id: "ALL", label: "All Memories", icon: <FaBrain size={12} /> },
          { id: "PERSONAL", label: "Personal Memory", icon: <FaUser size={12} /> },
          { id: "PROJECT", label: "Project Memory", icon: <FaFolder size={12} /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setScopeFilter(tab.id)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              scopeFilter === tab.id
                ? "bg-[#8D5CF6] text-white shadow-md shadow-violet-500/20"
                : "text-[#9AA1B2] hover:text-white hover:bg-[#151821]"
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Filter and Search Toolbar */}
      <div className="bg-[#0F1117]/80 border border-[#242833] rounded-2xl p-3.5 flex flex-col lg:flex-row lg:items-center justify-between gap-3 shadow-md">
        {/* Search Bar */}
        <div className="relative w-full lg:w-72">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" size={11} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memories, tags, or concepts..."
            className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-[#64748B] outline-none"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0 custom-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all shrink-0 cursor-pointer ${
                categoryFilter === cat
                  ? "bg-[#151821] text-violet-300 border border-[#8D5CF6]/50 shadow-sm"
                  : "text-[#9AA1B2] hover:text-white hover:bg-[#151821]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Sort and Project selector */}
        <div className="flex items-center gap-2 shrink-0">
          <select
            value={projectFilter}
            onChange={(e) => setProjectFilter(e.target.value)}
            className="bg-[#08090D] border border-[#242833] rounded-xl px-2.5 py-1.5 text-xs text-[#9AA1B2] outline-none cursor-pointer"
          >
            <option value="ALL">All Projects</option>
            <option value="aiforge-fooddelivery-ai">FoodDelivery AI</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-[#08090D] border border-[#242833] rounded-xl px-2.5 py-1.5 text-xs text-[#9AA1B2] outline-none cursor-pointer"
          >
            <option value="recent">Recently Added</option>
            <option value="most_used">Most Recalled</option>
            <option value="importance">Importance</option>
            <option value="title">Title (A-Z)</option>
          </select>
        </div>
      </div>

      {/* Main Memory Cards Grid or Empty State */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-[#0F1117] border border-[#242833] rounded-2xl p-5 h-48 animate-pulse" />
          ))}
        </div>
      ) : memories.length === 0 ? (
        <div className="bg-[#0F1117]/60 border border-dashed border-[#242833] rounded-3xl p-12 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-[#151821] border border-[#242833] flex items-center justify-center mx-auto text-[#64748B]">
            <FaBrain size={24} className="text-violet-400" />
          </div>
          <div className="space-y-1.5 max-w-md mx-auto">
            <h3 className="text-base font-bold text-white">No memories stored yet</h3>
            <p className="text-xs text-[#9AA1B2]">
              {searchQuery
                ? `No memories match query "${searchQuery}"`
                : "Teach AIForge your preferred stack, coding style, or project architecture decisions so it remembers them forever."}
            </p>
          </div>
          <button
            onClick={openCreateModal}
            className="px-5 py-2.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow-md shadow-violet-500/25 cursor-pointer"
          >
            + Remember Something Now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {memories.map((item) => (
            <div
              key={item.id}
              className="bg-[#0F1117]/90 hover:bg-[#151821] border border-[#242833] hover:border-[#8D5CF6]/50 rounded-2xl p-5 flex flex-col justify-between transition-all group shadow-lg relative"
            >
              <div>
                {/* Header: Scope, Category, Importance & Pin */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono border ${
                      item.scope === "PERSONAL"
                        ? "bg-violet-500/10 text-violet-400 border-violet-500/20"
                        : "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                    }`}>
                      {item.scope}
                    </span>

                    <span className="px-2 py-0.5 rounded-full bg-[#151821] border border-[#242833] text-[10px] font-semibold text-[#9AA1B2]">
                      {item.category}
                    </span>

                    <span className={`text-[9px] font-bold font-mono px-1.5 py-0.5 rounded ${
                      item.importance === "CRITICAL" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                      item.importance === "HIGH" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                      "bg-slate-800 text-slate-400"
                    }`}>
                      {item.importance}
                    </span>
                  </div>

                  <button
                    onClick={(e) => handleTogglePin(item, e)}
                    className="text-[#64748B] hover:text-amber-400 transition cursor-pointer p-1"
                    title={item.pinned ? "Pinned memory" : "Pin memory"}
                  >
                    {item.pinned ? <FaStar className="text-amber-400" size={13} /> : <FaRegStar size={13} />}
                  </button>
                </div>

                {/* Title and Content */}
                <h3 className="text-sm font-bold text-white group-hover:text-violet-300 transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-[#9AA1B2] mt-2 leading-relaxed whitespace-pre-wrap line-clamp-4">
                  {item.content}
                </p>

                {/* Project association tag (if project scope) */}
                {item.project_id && (
                  <div className="mt-3 flex items-center gap-1.5 text-[10px] font-mono text-cyan-300 bg-cyan-500/10 border border-cyan-500/20 rounded-md px-2 py-0.5 w-fit">
                    <FaFolder size={9} />
                    <span>{item.project_id}</span>
                  </div>
                )}

                {/* Tags */}
                {item.tags && item.tags.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap mt-3">
                    {item.tags.map((tag, idx) => (
                      <span key={idx} className="text-[10px] font-mono text-[#64748B] bg-[#08090D] border border-[#242833] rounded px-1.5 py-0.5">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Card Footer: Metadata & Actions */}
              <div className="pt-4 mt-4 border-t border-[#1C202B] flex items-center justify-between gap-2">
                <div className="space-y-0.5 text-[10px] font-mono text-[#64748B]">
                  <div>Source: <span className="text-[#9AA1B2]">{item.source}</span></div>
                  <div>Used: <span className="text-emerald-400 font-bold">{item.usage_count || 0}x</span> • {item.last_used_at || "Never"}</div>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={(e) => handleCopy(item, e)}
                    className="p-1.5 rounded-lg bg-[#08090D] hover:bg-[#1E2330] border border-[#242833] text-[#9AA1B2] hover:text-white transition cursor-pointer"
                    title="Copy memory"
                  >
                    {copiedId === item.id ? <FaCheck className="text-emerald-400" size={10} /> : <FaCopy size={10} />}
                  </button>

                  <button
                    onClick={(e) => openEditModal(item, e)}
                    className="p-1.5 rounded-lg bg-[#08090D] hover:bg-[#1E2330] border border-[#242833] text-[#9AA1B2] hover:text-white transition cursor-pointer"
                    title="Edit memory"
                  >
                    <FaEdit size={10} />
                  </button>

                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="p-1.5 rounded-lg bg-[#08090D] hover:bg-rose-500/20 border border-[#242833] text-[#64748B] hover:text-rose-400 transition cursor-pointer"
                    title="Forget memory"
                  >
                    <FaTrash size={10} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Memory Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <form
            onSubmit={handleFormSubmit}
            className="w-full max-w-lg bg-[#0F1117] border border-[#242833] rounded-3xl p-6 shadow-2xl text-xs space-y-4 flex flex-col glow-violet"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#242833]">
              <div className="flex items-center gap-2">
                <FaBrain className="text-[#8D5CF6]" size={14} />
                <h3 className="text-sm font-bold text-white">
                  {editingItem ? "Edit AI Memory" : "Remember New Information"}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="text-[#64748B] hover:text-white p-1 rounded-lg transition"
              >
                <FaTimes size={13} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Memory Title</label>
                <input
                  type="text"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  placeholder="e.g. Always Use Tailwind CSS & TypeScript"
                  required
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl px-3 py-2 text-white outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Memory Scope</label>
                  <select
                    value={formScope}
                    onChange={(e) => setFormScope(e.target.value)}
                    className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl px-3 py-2 text-white outline-none cursor-pointer"
                  >
                    <option value="PERSONAL">Personal (Global across all projects)</option>
                    <option value="PROJECT">Project (Scoped to specific project)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Category</label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl px-3 py-2 text-white outline-none cursor-pointer"
                  >
                    {categories.filter(c => c !== "All").map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              {formScope === "PROJECT" && (
                <div>
                  <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Target Project</label>
                  <input
                    type="text"
                    value={formProjectId}
                    onChange={(e) => setFormProjectId(e.target.value)}
                    placeholder="e.g. aiforge-fooddelivery-ai"
                    required
                    className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl px-3 py-2 text-white outline-none"
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Importance</label>
                  <select
                    value={formImportance}
                    onChange={(e) => setFormImportance(e.target.value)}
                    className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl px-3 py-2 text-white outline-none cursor-pointer"
                  >
                    <option value="CRITICAL">Critical (Always prioritized)</option>
                    <option value="HIGH">High (Primary recall)</option>
                    <option value="MEDIUM">Medium (Normal)</option>
                    <option value="LOW">Low (Background reference)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Tags (Comma separated)</label>
                  <input
                    type="text"
                    value={formTags}
                    onChange={(e) => setFormTags(e.target.value)}
                    placeholder="FastAPI, React, Clean Code"
                    className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl px-3 py-2 text-white outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#9AA1B2] mb-1">Memory Content / Detail</label>
                <textarea
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  placeholder="Describe the exact convention, rule, architecture choice, or preference for the AI to remember..."
                  rows={4}
                  required
                  className="w-full bg-[#08090D] border border-[#242833] focus:border-[#8D5CF6] rounded-xl p-3 text-white outline-none resize-none leading-relaxed"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="formPinned"
                  checked={formPinned}
                  onChange={(e) => setFormPinned(e.target.checked)}
                  className="rounded bg-[#08090D] border-[#242833] text-[#8D5CF6] cursor-pointer"
                />
                <label htmlFor="formPinned" className="text-xs text-[#9AA1B2] cursor-pointer select-none">
                  Pin memory (always included in high-priority context recall)
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#242833]">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-3.5 py-2 text-xs text-[#9AA1B2] hover:text-white transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
              >
                {editingItem ? "Save Changes" : "Remember"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Clear Memory Confirmation Modal */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div 
            className="w-full max-w-md bg-[#0F1117] border border-rose-500/30 rounded-3xl p-6 shadow-2xl text-xs space-y-4 flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 text-rose-400">
              <FaExclamationTriangle size={20} />
              <h3 className="text-sm font-bold text-white">
                {projectFilter !== "ALL" ? `Clear Memories for ${projectFilter}?` : "Clear All AI Memories?"}
              </h3>
            </div>

            <p className="text-xs text-[#9AA1B2] leading-relaxed">
              This action will permanently delete all stored memory context. The AI assistant will forget all saved preferences and architectural knowledge. This cannot be undone.
            </p>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#242833]">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="px-3.5 py-2 text-xs text-[#9AA1B2] hover:text-white transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleClearAll}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold transition shadow cursor-pointer"
              >
                Yes, Clear Memories
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
