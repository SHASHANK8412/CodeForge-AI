import React, { useState, useEffect } from 'react';
import { FaRocket, FaCheckCircle, FaExclamationTriangle, FaTimesCircle, FaSpinner, FaShieldAlt, FaVial, FaTachometerAlt, FaProjectDiagram, FaDatabase, FaFileAlt, FaLock, FaSyncAlt, FaWrench, FaHistory, FaDownload } from 'react-icons/fa';
import {
  fetchReadinessReport,
  runReadinessGate,
  approveDeployment,
  rejectDeployment,
  autofixReadinessBlockers,
  fetchReadinessHistory,
  fetchReadinessDiff,
  exportReadinessReport
} from '../services/readiness';

export default function ProductionReadinessPage({ projectId = 'aiforge-demo' }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [repairing, setRepairing] = useState(false);
  const [history, setHistory] = useState([]);
  const [diff, setDiff] = useState(null);
  const [approving, setApproving] = useState(false);

  useEffect(() => {
    loadAllData();
  }, [projectId]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [repRes, histRes] = await Promise.all([
        fetchReadinessReport(projectId),
        fetchReadinessHistory(projectId)
      ]);
      if (repRes?.report) setReport(repRes.report);
      if (histRes?.history?.snapshots) setHistory(histRes.history.snapshots);
    } catch (err) {
      console.warn('Failed to load readiness data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunGate = async (simulateSecurityBlock = false) => {
    setEvaluating(true);
    try {
      const res = await runReadinessGate(projectId, simulateSecurityBlock);
      if (res?.report) setReport(res.report);
      await loadAllData();
    } catch (err) {
      alert(`Gate evaluation failed: ${err.message}`);
    } finally {
      setEvaluating(false);
    }
  };

  const handleApprove = async () => {
    setApproving(true);
    try {
      const res = await approveDeployment(projectId);
      if (res?.approved) {
        alert('🚀 Production deployment approved & dispatched!');
        await loadAllData();
      } else {
        alert('🚫 Cannot approve deployment — Readiness Gate is BLOCKED!');
      }
    } catch (err) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setApproving(false);
    }
  };

  const handleAutofix = async () => {
    setRepairing(true);
    try {
      const res = await autofixReadinessBlockers(projectId);
      if (res?.report) setReport(res.report);
    } catch (err) {
      alert(`Auto-fix failed: ${err.message}`);
    } finally {
      setRepairing(false);
    }
  };

  const handleExport = async () => {
    try {
      const res = await exportReadinessReport(projectId);
      if (res?.json) {
        const blob = new Blob([res.json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `aiforge_readiness_report_${projectId}.json`;
        a.click();
      }
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    }
  };

  const checks = report?.checks || [];
  const cto = report?.cto_review || {};
  const isBlocked = report?.status === 'BLOCKED';

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-emerald-600/20 border border-emerald-500/40 rounded-xl text-emerald-400">
            <FaRocket className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              🚀 Autonomous Production Readiness Gate
              <span className="text-xs px-2.5 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full font-mono">
                EVIDENCE GATEWAY V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Evidence-based deployment policy consuming Security, Testing, Playwright, Performance & DNA.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleRunGate(false)}
            disabled={evaluating}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-1.5 shadow"
          >
            {evaluating ? <FaSpinner className="animate-spin" /> : <FaSyncAlt />} Evaluate Gate
          </button>
          <button
            onClick={() => handleRunGate(true)}
            className="px-3.5 py-2 bg-rose-950/40 hover:bg-rose-900/40 border border-rose-500/40 text-rose-300 text-xs font-mono font-bold rounded-xl transition"
          >
            Simulate Security Vulnerability Block
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 text-xs font-bold rounded-xl transition flex items-center gap-1.5"
          >
            <FaDownload /> Export Report
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-400 font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-emerald-400 mr-2" /> Evaluating engineering evidence…
        </div>
      ) : (
        <>
          {/* READINESS BANNER & OVERALL SCORE */}
          <div className={`p-8 rounded-2xl border-2 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-6 ${
            isBlocked
              ? 'bg-rose-950/30 border-rose-500/60'
              : report?.status === 'READY_WITH_WARNINGS'
              ? 'bg-amber-950/30 border-amber-500/60'
              : 'bg-emerald-950/30 border-emerald-500/60'
          }`}>
            <div className="space-y-2 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-3">
                <span className="text-4xl font-black font-mono tracking-tight text-white">
                  {report?.overall_score || 96} / 100
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold font-mono tracking-wide ${
                  isBlocked
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                }`}>
                  {report?.status}
                </span>
              </div>
              <h2 className="text-lg font-bold text-white flex items-center justify-center md:justify-start gap-2">
                {isBlocked ? (
                  <span className="text-rose-400 flex items-center gap-2">
                    <FaTimesCircle className="w-5 h-5" /> 🚫 DEPLOYMENT BLOCKED
                  </span>
                ) : (
                  <span className="text-emerald-400 flex items-center gap-2">
                    <FaCheckCircle className="w-5 h-5" /> 🟢 READY FOR PRODUCTION DEPLOYMENT
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-300 max-w-xl font-sans">{cto.executive_summary}</p>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              {isBlocked ? (
                <button
                  onClick={handleAutofix}
                  disabled={repairing}
                  className="px-6 py-3 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-xl transition flex items-center gap-2"
                >
                  {repairing ? <FaSpinner className="animate-spin" /> : <FaWrench />} [ Fix Automatically ]
                </button>
              ) : (
                <button
                  onClick={handleApprove}
                  disabled={approving || report?.approval_status === 'APPROVED'}
                  className={`px-6 py-3 font-bold text-xs rounded-xl shadow-xl transition flex items-center gap-2 ${
                    report?.approval_status === 'APPROVED'
                      ? 'bg-emerald-800/40 text-emerald-300 border border-emerald-500/40 cursor-default'
                      : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                  }`}
                >
                  <FaRocket /> {report?.approval_status === 'APPROVED' ? 'Approved & Dispatched' : 'Approve & Deploy to Production'}
                </button>
              )}
            </div>
          </div>

          {/* CHECKS MATRIX GRID */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 font-sans">
            {checks.map((c) => (
              <div key={c.id} className={`p-4 rounded-2xl border transition space-y-2.5 ${
                c.status === 'FAIL'
                  ? 'bg-rose-950/40 border-rose-500/50'
                  : c.status === 'WARN'
                  ? 'bg-amber-950/20 border-amber-500/40'
                  : 'bg-slate-950/70 border-slate-800'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                    {c.category}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold font-mono ${
                    c.status === 'PASS'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : c.status === 'WARN'
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                  }`}>
                    {c.status} ({c.score}%)
                  </span>
                </div>

                <h4 className="text-xs font-bold text-white font-sans">{c.name}</h4>
                <p className="text-[11px] text-slate-300 font-mono leading-relaxed">{c.evidence}</p>

                {c.recommendation && (
                  <div className="text-[10px] text-amber-300/90 font-mono pt-1 border-t border-slate-800">
                    💡 {c.recommendation}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
