import React, { useState, useEffect } from 'react';
import { FaDna, FaSpinner, FaSearch, FaProjectDiagram } from 'react-icons/fa';
import { fetchDnaGraph, analyzeDnaImpact } from '../services/intelligence';

export default function DnaGraphPage({ projectId = 'aiforge-demo' }) {
  const [graph, setGraph] = useState(null);
  const [impactQuery, setImpactQuery] = useState('payment');
  const [impactResult, setImpactResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGraph();
  }, [projectId]);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const res = await fetchDnaGraph(projectId);
      setGraph(res.graph);
    } catch (err) {
      console.warn('Failed to load DNA graph:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleImpactSearch = async (e) => {
    e.preventDefault();
    if (!impactQuery.trim()) return;
    try {
      const res = await analyzeDnaImpact(projectId, impactQuery);
      setImpactResult(res);
    } catch (err) {
      alert(`Impact analysis failed: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6">
      {/* Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex items-center gap-4">
        <div className="p-3 bg-cyan-600/20 border border-cyan-500/40 rounded-xl text-cyan-400">
          <FaDna className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            AI Engineering DNA — Project Intelligence Graph
          </h1>
          <p className="text-xs text-slate-400">
            Live dependency graph linking Requirement → Feature → API → Service → Database → Tests → Deployment.
          </p>
        </div>
      </div>

      {/* Impact Search */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
          Trace Dependency Impact ("If I change X, what will break?")
        </label>
        <form onSubmit={handleImpactSearch} className="flex gap-3">
          <input
            type="text"
            value={impactQuery}
            onChange={(e) => setImpactQuery(e.target.value)}
            placeholder="e.g. payment, auth, orders_table..."
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-slate-100 font-mono outline-none focus:border-cyan-500 transition"
          />
          <button
            type="submit"
            className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded-xl shadow-lg transition flex items-center gap-2"
          >
            <FaSearch className="w-3 h-3" /> Analyze Impact
          </button>
        </form>

        {impactResult && (
          <div className="mt-4 p-4 bg-slate-900/80 border border-cyan-500/30 rounded-xl text-xs font-mono space-y-2">
            <div className="font-bold text-cyan-300">
              Impact Analysis for '{impactResult.target_component}': {impactResult.affected_count} Components Affected
            </div>
            <p className="text-slate-300">{impactResult.risk_assessment}</p>
          </div>
        )}
      </div>

      {/* Graph Nodes Grid */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 font-sans">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <FaProjectDiagram className="text-cyan-400" />
          Application DNA Nodes & Relationships ({graph?.nodes?.length || 0} Nodes)
        </h3>

        {loading ? (
          <div className="flex items-center justify-center p-8 text-slate-400">
            <FaSpinner className="w-5 h-5 animate-spin text-cyan-400 mr-2" /> Loading DNA graph…
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {(graph?.nodes || []).map((node) => (
              <div key={node.id} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1 font-mono text-xs">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-white">{node.label}</span>
                  <span className="px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 rounded text-[10px]">
                    {node.type}
                  </span>
                </div>
                {node.file_path && <div className="text-[11px] text-slate-400 truncate">{node.file_path}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
