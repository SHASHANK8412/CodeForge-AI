import React, { useState, useEffect } from 'react';
import { FaGavel, FaSpinner, FaTrophy, FaLayerGroup, FaCheckCircle } from 'react-icons/fa';
import { fetchDebateVerdict, startDebate } from '../services/intelligence';

export default function DebateArenaPage({ generationId = 'aiforge-demo' }) {
  const [verdict, setVerdict] = useState(null);
  const [prompt, setPrompt] = useState('High-concurrency Task Platform Architecture');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDebate();
  }, [generationId]);

  const loadDebate = async () => {
    setLoading(true);
    try {
      const res = await fetchDebateVerdict(generationId);
      setVerdict(res.verdict);
    } catch (err) {
      console.warn('Failed to load debate verdict:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunDebate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await startDebate(generationId, prompt);
      setVerdict(res.verdict);
    } catch (err) {
      alert(`Debate failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const proposals = verdict?.proposals || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6">
      {/* Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-amber-600/20 border border-amber-500/40 rounded-xl text-amber-400">
            <FaGavel className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              Multi-Agent Architectural Debate Arena
            </h1>
            <p className="text-xs text-slate-400">
              3 Architect Agents present competing technical proposals evaluated by an autonomous Judge Agent.
            </p>
          </div>
        </div>

        <form onSubmit={handleRunDebate} className="flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-white outline-none focus:border-amber-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5 shrink-0"
          >
            {loading ? <FaSpinner className="w-3.5 h-3.5 animate-spin" /> : <FaGavel className="w-3.5 h-3.5" />}
            Start Debate
          </button>
        </form>
      </div>

      {/* Winning Verdict Card */}
      {verdict && (
        <div className="bg-gradient-to-r from-amber-950/60 to-slate-950 border-2 border-amber-500/60 rounded-2xl p-6 shadow-2xl space-y-3 font-sans">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FaTrophy className="w-6 h-6 text-yellow-400" />
              <div>
                <span className="text-[11px] font-mono font-bold text-amber-400 uppercase">
                  🏆 JUDGE AGENT VERDICT — {verdict.winning_architect} WINS
                </span>
                <h2 className="text-lg font-bold text-white mt-0.5">{verdict.selected_architecture}</h2>
              </div>
            </div>
            <span className="text-2xl font-extrabold text-amber-400 font-mono">{verdict.overall_score}/100</span>
          </div>
          <p className="text-xs text-slate-300 font-mono bg-slate-950/80 p-3 rounded-xl border border-slate-800">
            Reason: {verdict.reason}
          </p>
        </div>
      )}

      {/* Proposals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-sans">
        {proposals.map((p, idx) => (
          <div
            key={idx}
            className={`p-6 rounded-2xl border transition space-y-4 ${
              verdict?.winning_architect === p.architect_id
                ? 'bg-slate-950 border-amber-500 shadow-xl'
                : 'bg-slate-950/60 border-slate-800'
            }`}
          >
            <div className="flex justify-between items-start font-mono">
              <div>
                <span className="text-xs font-bold text-amber-400 block">{p.architect_id}</span>
                <h3 className="text-sm font-bold text-white mt-1">{p.architecture_name}</h3>
              </div>
              <span className="text-sm font-bold text-slate-400">{p.score}/100</span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <span className="text-slate-400 uppercase text-[10px] block">PROS</span>
              <ul className="space-y-1 text-emerald-300">
                {(p.pros || []).map((pro, i) => <li key={i}>✓ {pro}</li>)}
              </ul>
              <span className="text-slate-400 uppercase text-[10px] block pt-2">CONS</span>
              <ul className="space-y-1 text-rose-300">
                {(p.cons || []).map((con, i) => <li key={i}>✗ {con}</li>)}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
