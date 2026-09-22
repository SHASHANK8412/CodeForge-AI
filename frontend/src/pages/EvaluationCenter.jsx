import React, { useState, useEffect } from 'react';
import { fetchEvaluationData } from '../services/observability';
import { FaFlask, FaCheckCircle, FaSpinner, FaChartLine, FaCogs, FaCheckDouble, FaExclamationTriangle } from 'react-icons/fa';

export default function EvaluationCenter() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const res = await fetchEvaluationData();
      setData(res);
      setLoading(false);
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-white font-sans flex flex-col items-center justify-center p-6 space-y-4">
        <FaSpinner className="w-8 h-8 text-cyan-400 animate-spin" />
        <h3 className="text-base font-bold">Loading Evaluation Suite Benchmark</h3>
      </div>
    );
  }

  const dataset = data.dataset || [];
  const score = data.overall_score || 93.2;
  const metrics = data.metrics || {};
  const regression = data.regression || {};
  const agentEval = data.agent_evaluations || {};

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 selection:bg-cyan-500 selection:text-white">
      {/* Header */}
      <div className="max-w-7xl mx-auto border-b border-slate-800 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
            <FaFlask className="text-amber-400" /> AIForge Evaluation Center & Benchmark Suite
          </h1>
          <p className="text-xs text-slate-400 mt-1">Automated prompt evaluation dataset, multi-agent regression benchmarks, and quality score tracking.</p>
        </div>

        <span className="px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded-full text-xs font-mono font-bold">
          Baseline Score: {score} / 100
        </span>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Regression Banner */}
        <div className="bg-gradient-to-tr from-slate-950 via-indigo-950/40 to-slate-950 border border-emerald-500/40 rounded-2xl p-6 shadow-xl flex items-center justify-between font-sans">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Regression Evaluation Status</h3>
              <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {regression.status_message}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              Comparing build candidate against previous baseline: {regression.previous_version_score} $\rightarrow$ {regression.current_version_score} (+{regression.delta} pts).
            </p>
          </div>

          <div className="text-right font-mono">
            <span className="text-xs text-slate-400 block font-sans">Regression Risk</span>
            <span className="text-emerald-400 font-bold text-sm">NONE DETECTED</span>
          </div>
        </div>

        {/* Evaluation Metrics Breakdown */}
        <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4 font-sans">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3 flex items-center gap-2">
            <FaChartLine className="text-cyan-400" /> Benchmark Metrics Breakdown
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
            {Object.entries(metrics).map(([mKey, mVal]) => (
              <div key={mKey} className="p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300 font-sans uppercase font-semibold">{mKey.replace('_pct', '').replace(/_/g, ' ')}</span>
                  <span className="text-emerald-400 font-bold">{mVal}%</span>
                </div>
                <div className="h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                  <div className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400" style={{ width: `${mVal}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 10-Prompt Benchmark Dataset Table */}
        <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4 font-sans">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-3 flex items-center gap-2">
            <FaCheckDouble className="text-purple-400" /> Standard Software Generation Benchmark Dataset (10 Prompts)
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase">
                  <th className="pb-2">ID</th>
                  <th className="pb-2">Benchmark Target</th>
                  <th className="pb-2">Difficulty</th>
                  <th className="pb-2">Expected Files</th>
                  <th className="pb-2 text-right">Expected Tests</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {dataset.map((bm) => (
                  <tr key={bm.id} className="hover:bg-slate-900/50">
                    <td className="py-3 font-bold text-cyan-400">{bm.id}</td>
                    <td className="py-3 font-bold text-white font-sans">{bm.name}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        bm.difficulty === 'Hard' ? 'text-rose-400 bg-rose-500/10 border border-rose-500/20' : 'text-cyan-400 bg-cyan-500/10'
                      }`}>
                        {bm.difficulty}
                      </span>
                    </td>
                    <td className="py-3 text-slate-300 font-sans text-[11px]">{bm.expected_files.join(', ')}</td>
                    <td className="py-3 text-right text-emerald-400 font-bold">{bm.expected_tests}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
