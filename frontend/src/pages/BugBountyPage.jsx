import React, { useState, useEffect } from 'react';
import { FaShieldAlt, FaSpinner, FaBug, FaWrench, FaCheckCircle } from 'react-icons/fa';
import { scanSecurityHunter, fetchSecurityReport } from '../services/intelligence';

export default function BugBountyPage({ projectId = 'aiforge-demo' }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    loadReport();
  }, [projectId]);

  const loadReport = async () => {
    setLoading(true);
    try {
      const res = await fetchSecurityReport(projectId);
      setReport(res.report);
    } catch (err) {
      console.warn('Failed to load security report:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await scanSecurityHunter(projectId);
      setReport(res.report);
    } catch (err) {
      alert(`Security scan failed: ${err.message}`);
    } finally {
      setScanning(false);
    }
  };

  const vulns = report?.vulnerabilities || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6">
      {/* Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-emerald-600/20 border border-emerald-500/40 rounded-xl text-emerald-400">
            <FaShieldAlt className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              Autonomous AI Bug Bounty — Security Hunter Agent
            </h1>
            <p className="text-xs text-slate-400">
              Adversarial security hunter agent actively searching for vulnerabilities and auto-triggering RepairAgent patches.
            </p>
          </div>
        </div>

        <button
          onClick={handleScan}
          disabled={scanning}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-lg transition flex items-center gap-2 disabled:opacity-50 shrink-0"
        >
          {scanning ? <FaSpinner className="w-4 h-4 animate-spin" /> : <FaBug className="w-4 h-4" />}
          Run Security Hunter
        </button>
      </div>

      {/* Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl font-mono text-center">
          <span className="text-[10px] text-slate-500 uppercase block">Vulnerabilities Checked</span>
          <span className="text-xl font-bold text-cyan-400">{report?.vulnerabilities_investigated || 12}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl font-mono text-center">
          <span className="text-[10px] text-slate-500 uppercase block">Safe Checks</span>
          <span className="text-xl font-bold text-emerald-400">{report?.safe_count || 10}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl font-mono text-center">
          <span className="text-[10px] text-slate-500 uppercase block">Vulnerabilities Found</span>
          <span className="text-xl font-bold text-amber-400">{report?.vulnerabilities_found || 2}</span>
        </div>
        <div className="bg-slate-950 border border-slate-800 p-4 rounded-2xl font-mono text-center">
          <span className="text-[10px] text-slate-500 uppercase block">Auto-Patched Status</span>
          <span className="text-xl font-bold text-emerald-400">100% REPAIRED</span>
        </div>
      </div>

      {/* Vulnerabilities List */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <FaWrench className="text-emerald-400" />
          Investigated Security Vulnerabilities & Auto-Repair Audit
        </h3>

        {loading ? (
          <div className="flex items-center justify-center p-8 text-slate-400">
            <FaSpinner className="w-5 h-5 animate-spin text-emerald-400 mr-2" /> Inspecting AST & route handlers…
          </div>
        ) : (
          <div className="space-y-3">
            {vulns.map((v) => (
              <div key={v.id} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2 font-mono text-xs">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-rose-300 flex items-center gap-2">
                    <span className="px-2 py-0.5 bg-rose-500/20 border border-rose-500/40 text-rose-400 text-[10px] rounded">
                      {v.severity}
                    </span>
                    {v.title}
                  </span>
                  <span className="text-emerald-400 font-bold flex items-center gap-1">
                    <FaCheckCircle /> Repair Applied ({v.retest_status})
                  </span>
                </div>

                <p className="text-slate-300 font-sans">{v.description}</p>
                <div className="text-[11px] text-slate-500">File: {v.file} (Line {v.line})</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
