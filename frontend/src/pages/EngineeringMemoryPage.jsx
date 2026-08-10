import React, { useState, useEffect } from 'react';
import { FaBrain, FaSearch, FaProjectDiagram, FaSpinner, FaLayerGroup, FaHistory, FaCheckCircle, FaExclamationCircle, FaShieldAlt, FaTachometerAlt, FaSyncAlt, FaTags, FaPlus } from 'react-icons/fa';
import {
  fetchMemories,
  searchMemories,
  fetchKnowledgeGraph,
  fetchMemoryDashboard,
  consolidateMemories,
  createMemory
} from '../services/memory';

export default function EngineeringMemoryPage({ projectId = 'aiforge-demo' }) {
  const [memories, setMemories] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'graph'
  const [selectedMemory, setSelectedMemory] = useState(null);

  // New Memory Modal
  const [showAdd, setShowAdd] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newType, setNewType] = useState('ARCHITECTURE_DECISION');

  useEffect(() => {
    loadAllData();
  }, [projectId]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [memRes, dashRes, graphRes] = await Promise.all([
        fetchMemories(projectId),
        fetchMemoryDashboard(projectId),
        fetchKnowledgeGraph(projectId)
      ]);
      if (memRes?.memories) {
        setMemories(memRes.memories);
        setSelectedMemory(memRes.memories[0] || null);
      }
      if (dashRes?.dashboard) setDashboard(dashRes.dashboard);
      if (graphRes?.graph) setGraph(graphRes.graph);
    } catch (err) {
      console.warn('Failed to load memory data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      await loadAllData();
      return;
    }
    try {
      const res = await searchMemories(projectId, searchQuery);
      if (res?.memories) setMemories(res.memories);
    } catch (err) {
      alert(`Search failed: ${err.message}`);
    }
  };

  const handleConsolidate = async () => {
    try {
      const res = await consolidateMemories(projectId);
      if (res?.memories) {
        setMemories(res.memories);
        await loadAllData();
      }
    } catch (err) {
      alert(`Consolidation failed: ${err.message}`);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const res = await createMemory(projectId, newTitle, newContent, newType);
      if (res?.memory) {
        setShowAdd(false);
        setNewTitle('');
        setNewContent('');
        await loadAllData();
      }
    } catch (err) {
      alert(`Failed to save memory: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-600/20 border border-purple-500/40 rounded-xl text-purple-400">
            <FaBrain className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              🧠 Long-Term Engineering Memory & Knowledge Graph
              <span className="text-xs px-2.5 py-0.5 bg-purple-500/10 border border-purple-500/30 text-purple-400 rounded-full font-mono">
                INSTITUTIONAL REASONER V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Cross-generation decision memory, incident lessons, importance scoring & secret masking.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode(viewMode === 'list' ? 'graph' : 'list')}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5 shadow"
          >
            <FaProjectDiagram /> {viewMode === 'list' ? 'Knowledge Graph View' : 'Memory List View'}
          </button>
          <button
            onClick={handleConsolidate}
            className="px-3.5 py-2 bg-purple-950/40 hover:bg-purple-900/40 border border-purple-500/40 text-purple-300 text-xs font-mono font-bold rounded-xl transition flex items-center gap-1.5"
          >
            <FaSyncAlt /> Consolidate Memories
          </button>
          <button
            onClick={() => setShowAdd(true)}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-1.5"
          >
            <FaPlus /> Remember Decision
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-400 font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-purple-400 mr-2" /> Indexing engineering memory graph…
        </div>
      ) : (
        <>
          {/* MEMORY QUALITY DASHBOARD STATS */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 font-mono text-center">
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Total Memories</span>
              <span className="text-lg font-extrabold text-white">{dashboard?.total_memories || memories.length}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Active</span>
              <span className="text-lg font-extrabold text-emerald-400">{dashboard?.active_count || memories.length}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Critical</span>
              <span className="text-lg font-extrabold text-purple-400">{dashboard?.critical_count || 1}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">High Importance</span>
              <span className="text-lg font-extrabold text-cyan-400">{dashboard?.high_count || 2}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Superseded</span>
              <span className="text-lg font-extrabold text-amber-400">{dashboard?.superseded_count || 0}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Archived</span>
              <span className="text-lg font-extrabold text-slate-500">{dashboard?.archived_count || 0}</span>
            </div>
          </div>

          {/* SEARCH BAR */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              placeholder="Search engineering memories (e.g. PostgreSQL, Redis, Auth, Latency)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-mono text-white outline-none focus:border-purple-500 shadow"
            />
            <button
              type="submit"
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-bold text-xs rounded-xl shadow transition flex items-center gap-1.5"
            >
              <FaSearch /> Search
            </button>
          </form>

          {/* MAIN VIEW: LIST OR GRAPH */}
          {viewMode === 'graph' ? (
            <div className="bg-slate-950 border border-slate-800 p-6 rounded-2xl shadow-xl space-y-4 font-mono text-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-purple-400 border-b border-slate-800 pb-2 flex items-center gap-2">
                <FaProjectDiagram /> Knowledge Graph Visualizer ({graph?.nodes?.length || 0} Nodes, {graph?.edges?.length || 0} Edges)
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {(graph?.nodes || []).map((n) => (
                  <div key={n.id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
                    <span className="text-[9px] text-purple-400 block uppercase font-bold">{n.type}</span>
                    <span className="text-white font-sans text-xs font-bold">{n.label}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-sans">
              {/* Memory List */}
              <div className="lg:col-span-2 space-y-3 font-mono text-xs">
                {memories.map((m) => (
                  <div
                    key={m.id}
                    onClick={() => setSelectedMemory(m)}
                    className={`p-4 rounded-2xl border transition cursor-pointer space-y-2 ${
                      selectedMemory?.id === m.id
                        ? 'bg-slate-950 border-purple-500/60 shadow-xl'
                        : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase text-purple-400">{m.type}</span>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                        m.importance === 'CRITICAL' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40' : 'bg-cyan-500/20 text-cyan-300'
                      }`}>
                        {m.importance}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white font-sans">{m.title}</h4>
                    <p className="text-slate-300 text-xs font-mono leading-relaxed line-clamp-2">{m.content}</p>

                    <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-800/80">
                      <span>Source: {m.source}</span>
                      <span>Version: v{m.version}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Memory Detail Drawer */}
              <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4 font-mono text-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-2">
                  Memory Detail Inspector
                </h3>

                {selectedMemory ? (
                  <div className="space-y-3 font-sans">
                    <div>
                      <span className="text-[10px] text-purple-400 font-mono block uppercase">{selectedMemory.type}</span>
                      <h3 className="text-base font-bold text-white">{selectedMemory.title}</h3>
                    </div>

                    <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 text-xs font-mono text-slate-200 leading-relaxed">
                      {selectedMemory.content}
                    </div>

                    <div className="text-xs space-y-1 text-slate-400 font-mono">
                      <div>Importance: {selectedMemory.importance}</div>
                      <div>Confidence: {selectedMemory.confidence}</div>
                      <div>Source: {selectedMemory.source}</div>
                      <div>Status: {selectedMemory.status}</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-500">Select a memory to inspect details.</div>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
