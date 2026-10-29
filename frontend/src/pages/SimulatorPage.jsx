import React, { useState } from 'react';
import { FaMagic, FaSpinner, FaExclamationTriangle, FaCheckCircle, FaTimesCircle, FaHourglassHalf, FaFileCode } from 'react-icons/fa';
import { runSimulation } from '../services/intelligence';

export default function SimulatorPage({ projectId = 'aiforge-demo' }) {
  const [query, setQuery] = useState('What happens if I switch PostgreSQL to MongoDB?');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await runSimulation(projectId, query);
      setResult(res.simulation);
    } catch (err) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6">
      {/* Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex items-center gap-4">
        <div className="p-3 bg-purple-600/20 border border-purple-500/40 rounded-xl text-purple-400">
          <FaMagic className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            What-If Engineering Simulator
            <span className="text-xs px-2.5 py-0.5 bg-purple-400/10 border border-purple-400/30 text-purple-300 rounded-full font-mono">
              PRE-CHANGE IMPACT ANALYSIS
            </span>
          </h1>
          <p className="text-xs text-slate-400">
            Simulate architectural, code, database, API, test, and risk impact before modifying code.
          </p>
        </div>
      </div>

      {/* Simulator Form */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <form onSubmit={handleSimulate} className="space-y-3">
          <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
            Ask What-If Question
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What happens if I switch PostgreSQL to MongoDB?"
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 font-mono outline-none focus:border-purple-500 transition"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold rounded-xl shadow-lg transition flex items-center gap-2 disabled:opacity-50 shrink-0"
            >
              {loading ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaMagic className="w-4 h-4" />}
              Run Simulation
            </button>
          </div>
        </form>
      </div>

      {/* Simulation Result Card */}
      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl font-mono text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Files Affected</span>
              <span className="text-xl font-bold text-cyan-400">{result.files_affected}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl font-mono text-center">
              <span className="text-[10px] text-slate-500 uppercase block">APIs Affected</span>
              <span className="text-xl font-bold text-purple-400">{result.apis_affected}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl font-mono text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Tests Affected</span>
              <span className="text-xl font-bold text-amber-400">{result.tests_affected}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl font-mono text-center">
              <span className="text-[10px] text-slate-500 uppercase block">Estimated Effort</span>
              <span className="text-xl font-bold text-emerald-400">{result.estimated_work_hours} hrs</span>
            </div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 font-sans">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                {result.recommendation === 'ACCEPT' ? (
                  <FaCheckCircle className="w-6 h-6 text-emerald-400" />
                ) : (
                  <FaTimesCircle className="w-6 h-6 text-rose-400" />
                )}
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                    Recommendation: {result.recommendation}
                  </h3>
                  <p className="text-xs text-slate-400">Risk Level: <strong className="text-amber-400 font-mono">{result.risk_level}</strong></p>
                </div>
              </div>
            </div>

            <p className="text-xs text-slate-300 font-mono bg-slate-900 p-4 rounded-xl border border-slate-800 leading-relaxed">
              {result.reason}
            </p>

            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Affected System Components</h4>
              <div className="space-y-2">
                {(result.affected_components || []).map((comp, idx) => (
                  <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl text-xs font-mono flex justify-between items-center">
                    <span className="font-bold text-white">{comp.component}</span>
                    <span className="text-slate-400">{comp.impact}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
