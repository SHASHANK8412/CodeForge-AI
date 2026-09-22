import React, { useState, useEffect } from 'react';
import {
  FaBrain, FaSearch, FaCheckCircle, FaLightbulb,
  FaShieldAlt, FaQuestionCircle, FaTimes, FaSpinner, FaDatabase, FaLayerGroup, FaExclamationTriangle
} from 'react-icons/fa';
import { fetchProjectMemory, searchProjectMemory, explainDecision } from '../../services/memory';

export default function ProjectMemoryDashboard({ projectId = 'default_project' }) {
  const [data, setData] = useState({ memories: [], decisions: [] });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [explanation, setExplanation] = useState(null);
  const [explainingTopic, setExplainingTopic] = useState(null);

  useEffect(() => {
    loadMemory();
  }, [projectId]);

  const loadMemory = async () => {
    setLoading(true);
    try {
      const res = await fetchProjectMemory(projectId);
      setData(res);
    } catch (err) {
      console.warn('Failed to load project memory:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const res = await searchProjectMemory(projectId, searchQuery);
      setSearchResults(res.results || []);
    } catch (err) {
      console.error('Memory search error:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleExplain = async (topic) => {
    setExplainingTopic(topic);
    try {
      const res = await explainDecision(projectId, topic);
      setExplanation(res);
    } catch (err) {
      console.error('Decision explanation error:', err);
    } finally {
      setExplainingTopic(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl flex items-center justify-center space-x-3 text-slate-400">
        <FaSpinner className="w-5 h-5 animate-spin text-cyan-400" />
        <span className="text-sm font-medium">Loading Project Memory & Context…</span>
      </div>
    );
  }

  const memories = searchResults !== null ? searchResults : (data.memories || []);
  const decisions = data.decisions || [];

  const reqMemories = memories.filter((m) => m.memory_type === 'REQUIREMENT');
  const archMemories = memories.filter((m) => m.memory_type === 'ARCHITECTURE' || m.memory_type === 'TECHNOLOGY');
  const issueMemories = memories.filter((m) => m.memory_type === 'ERROR' || m.memory_type === 'FIX');

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans space-y-6">
      {/* Header & Search */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FaBrain className="text-cyan-400 w-5 h-5" />
            Project Memory & Context Engine
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Persistent agent choices, architectural decisions, and requirement memory
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex items-center gap-2">
          <div className="relative">
            <input
              type="text"
              placeholder="Search memory..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-1.5 pl-9 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-48 sm:w-64"
            />
            <FaSearch className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="px-3.5 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-semibold transition flex items-center gap-1.5"
          >
            {searching ? <FaSpinner className="w-3 h-3 animate-spin" /> : 'Search'}
          </button>
          {searchResults !== null && (
            <button
              type="button"
              onClick={() => { setSearchQuery(''); setSearchResults(null); }}
              className="p-1.5 bg-slate-800 text-slate-400 hover:text-white rounded-xl text-xs"
            >
              <FaTimes />
            </button>
          )}
        </form>
      </div>

      {/* Decision Explanation Modal / Alert */}
      {explanation && (
        <div className="rounded-xl border border-cyan-500/40 bg-cyan-500/10 p-4 relative space-y-2">
          <button
            onClick={() => setExplanation(null)}
            className="absolute top-3 right-3 text-slate-400 hover:text-white"
          >
            <FaTimes />
          </button>
          <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1.5">
            <FaLightbulb className="text-amber-400 w-4 h-4" />
            Decision Explainability: Why did AIForge choose {explanation.topic}?
          </h4>
          <p className="text-xs text-slate-200 leading-relaxed font-mono bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
            {explanation.explanation}
          </p>
          <div className="flex gap-4 text-[10px] text-slate-400 font-mono">
            <span>Agent: {explanation.agent || 'Architect'}</span>
            <span>Decision: {explanation.decision}</span>
          </div>
        </div>
      )}

      {/* Decision Cards */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <FaShieldAlt className="text-emerald-400" />
          Key Architectural Decisions ({decisions.length})
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {decisions.length > 0 ? (
            decisions.map((dec) => (
              <div key={dec.id} className="bg-slate-900/70 border border-slate-800 rounded-xl p-3.5 space-y-2">
                <div className="flex items-start justify-between">
                  <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <FaCheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    {dec.decision}
                  </span>
                  <button
                    onClick={() => handleExplain(dec.decision.split(' ')[1] || dec.decision)}
                    disabled={explainingTopic === (dec.decision.split(' ')[1] || dec.decision)}
                    className="text-[10px] text-cyan-400 hover:underline flex items-center gap-1 font-mono shrink-0"
                  >
                    <FaQuestionCircle /> Why?
                  </button>
                </div>
                <p className="text-[11px] text-slate-400 italic line-clamp-2">{dec.reason}</p>
                <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between pt-1 border-t border-slate-800/60">
                  <span>Source: {dec.agent}</span>
                  <span className="text-amber-400/90 font-semibold">{dec.importance}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-2 text-xs text-slate-500 italic p-3 text-center bg-slate-900/30 rounded-xl border border-slate-800/50">
              No decisions recorded yet for this project.
            </div>
          )}
        </div>
      </div>

      {/* Memory Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        {/* Requirements */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 space-y-2">
          <h4 className="text-xs font-bold text-slate-300 flex items-center gap-2">
            <FaLayerGroup className="text-cyan-400" />
            Requirements ({reqMemories.length})
          </h4>
          <ul className="space-y-1.5 text-[11px] text-slate-400">
            {reqMemories.slice(0, 4).map((m) => (
              <li key={m.id} className="line-clamp-1 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
                {m.key}: {typeof m.value === 'string' ? m.value : JSON.stringify(m.value)}
              </li>
            ))}
            {reqMemories.length === 0 && <li className="italic text-slate-600">No stored requirements</li>}
          </ul>
        </div>

        {/* Architecture & Tech Specs */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 space-y-2">
          <h4 className="text-xs font-bold text-slate-300 flex items-center gap-2">
            <FaDatabase className="text-indigo-400" />
            Architecture Specs ({archMemories.length})
          </h4>
          <ul className="space-y-1.5 text-[11px] text-slate-400">
            {archMemories.slice(0, 4).map((m) => (
              <li key={m.id} className="line-clamp-1 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                {m.key}: {typeof m.value === 'string' ? m.value : JSON.stringify(m.value)}
              </li>
            ))}
            {archMemories.length === 0 && <li className="italic text-slate-600">No stored architecture items</li>}
          </ul>
        </div>

        {/* Known Issues & Fixes */}
        <div className="bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 space-y-2">
          <h4 className="text-xs font-bold text-slate-300 flex items-center gap-2">
            <FaExclamationTriangle className="text-amber-400" />
            Known Issues & Fixes ({issueMemories.length})
          </h4>
          <ul className="space-y-1.5 text-[11px] text-slate-400">
            {issueMemories.slice(0, 4).map((m) => (
              <li key={m.id} className="line-clamp-1 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                {m.key}: {typeof m.value === 'string' ? m.value : JSON.stringify(m.value)}
              </li>
            ))}
            {issueMemories.length === 0 && <li className="italic text-slate-600">0 stored issues</li>}
          </ul>
        </div>
      </div>
    </div>
  );
}
