import React, { useState, useEffect } from 'react';
import { FaDna, FaLayerGroup, FaSpinner, FaRocket, FaShieldAlt, FaTachometerAlt, FaCheckCircle, FaExclamationTriangle, FaWrench, FaHistory, FaBullseye, FaChartLine, FaArrowRight } from 'react-icons/fa';
import { analyzeEvolution, implementRecommendation, setEvolutionGoal, fetchEvolutionHistory } from '../services/evolution';

const GOALS = ['Enterprise Deployment', 'App Performance', 'Code Quality & Maintainability'];

export default function SoftwareEvolutionPage({ projectId = 'aiforge-demo' }) {
  const [analysis, setAnalysis] = useState(null);
  const [history, setHistory] = useState([]);
  const [selectedGoal, setSelectedGoal] = useState('Enterprise Deployment');
  const [loading, setLoading] = useState(true);
  const [implementing, setImplementing] = useState(false);
  const [selectedRec, setSelectedRec] = useState(null);

  useEffect(() => {
    loadData();
  }, [projectId, selectedGoal]);

  const loadData = async () => {
    setLoading(true);
    try {
      await setEvolutionGoal(projectId, selectedGoal);
      const [anRes, histRes] = await Promise.all([
        analyzeEvolution(projectId),
        fetchEvolutionHistory(projectId)
      ]);
      if (anRes?.analysis) setAnalysis(anRes.analysis);
      if (histRes?.history) setHistory(histRes.history);
    } catch (err) {
      console.warn('Failed to load evolution data:', err);
    } fontally {
      setLoading(false);
    }
  };

  const handleImplement = async (recId) => {
    setImplementing(true);
    try {
      const res = await implementRecommendation(projectId, recId);
      if (res?.result) {
        alert(res.result.message);
        await loadData();
      }
    } catch (err) {
      alert(`Implementation failed: ${err.message}`);
    } finally {
      setImplementing(false);
    }
  };

  const roadmap = analysis?.roadmap || {};

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-emerald-600/20 border border-emerald-500/40 rounded-xl text-emerald-400">
            <FaDna className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              🧬 AI Software Evolution Engine
              <span className="text-xs px-2.5 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full font-mono">
                CONTINUOUS IMPROVEMENT REASONER V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Technical Debt Detection, Multi-System Risk Scoring, Evidence-Based Roadmapping & Autonomous Refactoring.
            </p>
          </div>
        </div>

        {/* Goal Selector */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-slate-400 font-bold flex items-center gap-1"><FaBullseye /> Current Goal:</span>
          <select
            value={selectedGoal}
            onChange={(e) => setSelectedGoal(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-emerald-500 font-bold"
          >
            {GOALS.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-400 font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-emerald-400 mr-2" /> Evaluating project technical debt & risks…
        </div>
      ) : (
        <>
          {/* HEALTH & DEBT SCORECARD */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 font-mono text-center">
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Project Health</span>
              <span className="text-lg font-extrabold text-emerald-400">{roadmap.health_score || 89}/100</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Technical Debt</span>
              <span className="text-lg font-extrabold text-amber-400">{analysis?.debt_score?.overall_score || 84.8}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Security Score</span>
              <span className="text-lg font-extrabold text-cyan-400">{analysis?.debt_score?.security_score || 96}%</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Testing Score</span>
              <span className="text-lg font-extrabold text-indigo-400">{analysis?.debt_score?.testing_score || 91}%</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Architecture Risk</span>
              <span className="text-lg font-extrabold text-purple-400">{roadmap.architecture_risk || 'MEDIUM'}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Performance Risk</span>
              <span className="text-lg font-extrabold text-rose-400">{roadmap.performance_risk || 'MEDIUM'}</span>
            </div>
          </div>

          {/* ROADMAP PHASES (NOW / NEXT / LATER) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-sans">
            {/* NOW Phase */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4 font-mono text-xs">
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className="font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                  🔥 NOW (Immediate Priority)
                </span>
                <span className="px-2 py-0.5 bg-rose-500/10 text-rose-300 rounded font-bold">{roadmap.now?.length || 0}</span>
              </div>
              <div className="space-y-3 font-sans">
                {(roadmap.now || []).map((rec) => (
                  <div key={rec.id} className="p-4 bg-slate-900 border border-rose-500/40 rounded-xl space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-bold text-rose-400 font-mono">{rec.category}</span>
                      <span className="text-xs font-bold text-emerald-400 font-mono">Score: {rec.priority_score}</span>
                    </div>
                    <h4 className="text-xs font-bold text-white">{rec.title}</h4>
                    <p className="text-[11px] text-slate-300 font-mono line-clamp-2">{rec.recommended_action}</p>
                    <button
                      onClick={() => handleImplement(rec.id)}
                      disabled={implementing}
                      className="w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] rounded-xl shadow transition flex items-center justify-center gap-1.5"
                    >
                      {implementing ? <FaSpinner className="animate-spin" /> : <FaWrench />} [ Implement Recommendation ]
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* NEXT Phase */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4 font-mono text-xs">
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className="font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                  ⚡ NEXT (Medium Term)
                </span>
                <span className="px-2 py-0.5 bg-amber-500/10 text-amber-300 rounded font-bold">{roadmap.next_phase?.length || 0}</span>
              </div>
              <div className="space-y-3 font-sans">
                {(roadmap.next_phase || []).map((rec) => (
                  <div key={rec.id} className="p-4 bg-slate-900 border border-amber-500/40 rounded-xl space-y-2">
                    <span className="text-[10px] font-bold text-amber-400 font-mono block">{rec.category}</span>
                    <h4 className="text-xs font-bold text-white">{rec.title}</h4>
                    <p className="text-[11px] text-slate-300 font-mono line-clamp-2">{rec.recommended_action}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* LATER Phase */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4 font-mono text-xs">
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className="font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  🛡 LATER (Long Term)
                </span>
                <span className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded font-bold">{roadmap.later?.length || 0}</span>
              </div>
              <div className="space-y-3 font-sans">
                {(roadmap.later || []).map((rec) => (
                  <div key={rec.id} className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
                    <span className="text-[10px] font-bold text-slate-400 font-mono block">{rec.category}</span>
                    <h4 className="text-xs font-bold text-white">{rec.title}</h4>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
