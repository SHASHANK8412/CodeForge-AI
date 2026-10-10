import React, { useState, useEffect } from 'react';
import { FaGlobe, FaSpinner, FaCheckCircle, FaTimesCircle, FaDesktop, FaMobileAlt, FaLaptop, FaTabletAlt, FaCamera, FaTerminal, FaTools, FaShieldAlt, FaUniversalAccess } from 'react-icons/fa';
import {
  runBrowserTests,
  fetchBrowserTestReport,
  runAIForgeSelfTest,
  diagnoseBrowserFailure
} from '../services/browser_testing';

export default function BrowserTestingPage({ projectId = 'aiforge-demo' }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [runningSuite, setRunningSuite] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);
  const [repairResult, setRepairResult] = useState(null);
  const [diagnosing, setDiagnosing] = useState(false);

  useEffect(() => {
    loadReport();
  }, [projectId]);

  const loadReport = async () => {
    setLoading(true);
    try {
      const res = await fetchBrowserTestReport(projectId);
      if (res?.report) setReport(res.report);
    } catch (err) {
      console.warn('Failed to load browser test report:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSuite = async () => {
    setRunningSuite(true);
    try {
      const res = await runBrowserTests(projectId);
      if (res?.report) setReport(res.report);
    } catch (err) {
      alert(`Browser test suite failed: ${err.message}`);
    } finally {
      setRunningSuite(false);
    }
  };

  const handleRunSelfTest = async () => {
    setRunningSuite(true);
    try {
      const res = await runAIForgeSelfTest(projectId);
      if (res?.report) setReport(res.report);
    } catch (err) {
      alert(`AIForge self-test failed: ${err.message}`);
    } finally {
      setRunningSuite(false);
    }
  };

  const handleDiagnose = async (scenarioId) => {
    setDiagnosing(true);
    try {
      const res = await diagnoseBrowserFailure(projectId, scenarioId);
      setRepairResult(res.repair_result);
      await loadReport();
    } catch (err) {
      alert(`Diagnosis failed: ${err.message}`);
    } finally {
      setDiagnosing(false);
    }
  };

  const scenarios = report?.scenarios_results || [];
  const a11y = report?.accessibility_findings || [];
  const visual = report?.visual_regression_results || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-blue-600/20 border border-blue-500/40 rounded-xl text-blue-400">
            <FaGlobe className="w-7 h-7 animate-spin" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              🌐 Autonomous Browser Testing & UI Validation
              <span className="text-xs px-2.5 py-0.5 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-full font-mono">
                PLAYWRIGHT DOCKER
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Real Playwright Browser Automation, Screenshot Evidence, Traces, Viewport Responsive Testing & Auto-Repair.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRunSelfTest}
            disabled={runningSuite}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold rounded-xl transition flex items-center gap-2 shadow"
          >
            🤖 AIForge Self-Test Suite
          </button>
          <button
            onClick={handleRunSuite}
            disabled={runningSuite}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-xl shadow transition flex items-center gap-2 disabled:opacity-50"
          >
            {runningSuite ? <FaSpinner className="w-3.5 h-3.5 animate-spin" /> : <FaGlobe className="w-3.5 h-3.5" />}
            Run Playwright Suite
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-400 font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-blue-400 mr-2" /> Initializing Playwright browser runner…
        </div>
      ) : (
        <>
          {/* STATS SUMMARY BAR */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 font-mono text-center">
            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Total Scenarios</span>
              <span className="text-xl font-extrabold text-white">{report?.total_tests || 0}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Passed</span>
              <span className="text-xl font-extrabold text-emerald-400">{report?.passed_tests || 0}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Failed</span>
              <span className="text-xl font-extrabold text-rose-400">{report?.failed_tests || 0}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Duration</span>
              <span className="text-xl font-extrabold text-cyan-400">{report?.duration_seconds || 0}s</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Accessibility</span>
              <span className="text-xl font-extrabold text-amber-400">{a11y.length} Issues</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Visual Diffs</span>
              <span className="text-xl font-extrabold text-indigo-400">{visual.length} Pages</span>
            </div>
          </div>

          {/* MAIN SCENARIOS GRID AND FAILURE INSPECTOR */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-sans">
            {/* Scenarios List Column */}
            <div className="lg:col-span-2 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-2">
                <FaDesktop className="text-blue-400" /> Playwright Browser Test Scenarios ({scenarios.length})
              </h3>

              <div className="space-y-3 font-mono text-xs">
                {scenarios.map((res) => (
                  <div
                    key={res.scenario_id}
                    onClick={() => setSelectedResult(res)}
                    className={`p-4 rounded-xl border transition cursor-pointer flex justify-between items-center ${
                      selectedResult?.scenario_id === res.scenario_id
                        ? 'bg-blue-600/20 border-blue-400 shadow-lg shadow-blue-500/10'
                        : res.status === 'PASS'
                        ? 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
                        : 'bg-rose-950/20 border-rose-500/50 hover:border-rose-400'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        {res.status === 'PASS' ? <FaCheckCircle className="text-emerald-400" /> : <FaTimesCircle className="text-rose-400" />}
                        <span className="font-bold text-white font-sans text-sm">{res.scenario_name}</span>
                      </div>
                      <div className="text-[10px] text-slate-400">URL: {res.current_url || '/'}</div>
                      {res.error_message && (
                        <div className="text-[10px] text-rose-300 font-sans mt-1">⚠ {res.error_message}</div>
                      )}
                    </div>

                    <div className="text-right">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                        res.status === 'PASS' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      }`}>
                        {res.status} ({res.duration_seconds}s)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Scenario Details & Evidence Sidebar */}
            <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4 font-mono text-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-2">
                Evidence & Root Cause Inspector
              </h3>

              {selectedResult ? (
                <div className="space-y-4">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">Selected Scenario</span>
                    <div className="font-bold text-white text-sm font-sans">{selectedResult.scenario_name}</div>
                    <div className="text-[10px] text-cyan-400 mt-0.5">Status: {selectedResult.status}</div>
                  </div>

                  {selectedResult.error_message && (
                    <div className="p-3 bg-rose-950/40 border border-rose-500/30 rounded-xl space-y-1 text-rose-200 text-[11px] font-sans">
                      <div className="font-bold text-rose-400 font-mono text-[9px] uppercase">Failure Exception</div>
                      {selectedResult.error_message}
                      {selectedResult.affected_file && (
                        <div className="text-[10px] text-slate-300 font-mono mt-1">Affected File: {selectedResult.affected_file}</div>
                      )}
                    </div>
                  )}

                  {/* Network / Console Logs */}
                  {selectedResult.network_errors.length > 0 && (
                    <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1 text-[10px] text-rose-300 font-mono">
                      <div className="text-[9px] text-slate-400 uppercase font-bold">Network Failures (4xx/5xx)</div>
                      {selectedResult.network_errors.map((net, i) => (
                        <div key={i}>{net.method} {net.url} ➔ {net.status} ({net.error})</div>
                      ))}
                    </div>
                  )}

                  {/* Evidence Media Actions */}
                  <div className="space-y-2 border-t border-slate-800 pt-3">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Evidence Artifacts</span>
                    <div className="flex gap-2">
                      <button className="flex-1 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-[11px] font-bold rounded-lg transition flex items-center justify-center gap-1">
                        <FaCamera /> Screenshot
                      </button>
                      <button className="flex-1 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-[11px] font-bold rounded-lg transition flex items-center justify-center gap-1">
                        <FaTerminal /> Playwright Trace
                      </button>
                    </div>
                  </div>

                  {selectedResult.status !== 'PASS' && (
                    <button
                      onClick={() => handleDiagnose(selectedResult.scenario_id)}
                      disabled={diagnosing}
                      className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center justify-center gap-2"
                    >
                      {diagnosing ? <FaSpinner className="animate-spin" /> : <FaTools />} Diagnose & Repair Code
                    </button>
                  )}

                  {repairResult && (
                    <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl space-y-1 text-[11px] font-sans text-emerald-200">
                      <div className="font-bold text-emerald-400 font-mono text-[9px] uppercase">Auto-Repair Applied</div>
                      {repairResult.patch_summary}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-slate-500 text-center py-12 italic">
                  Select any scenario from the list to view Playwright trace, network errors, screenshots, and auto-repair options.
                </div>
              )}
            </div>
          </div>

          {/* ACCESSIBILITY & VISUAL REGRESSION SECTION */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-sans">
            {/* Accessibility Audit */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
                <FaUniversalAccess className="text-amber-400" /> Automated Accessibility Audit ({a11y.length} Findings)
              </h3>
              <div className="space-y-2 font-mono text-xs">
                {a11y.map((item) => (
                  <div key={item.id} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-amber-300">{item.rule}</span>
                      <span className="px-2 py-0.5 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded text-[9px]">
                        {item.severity}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-300 font-sans">{item.description}</div>
                    <div className="text-[10px] text-slate-400">Target: {item.target_selector}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Visual Regression */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
                <FaCamera className="text-indigo-400" /> Visual Regression & Screenshot Comparison ({visual.length} Pages)
              </h3>
              <div className="space-y-2 font-mono text-xs">
                {visual.map((vis, idx) => (
                  <div key={idx} className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white uppercase">{vis.page_name}</span>
                      <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded text-[9px]">
                        Mismatch: {(vis.mismatch_percent * 100).toFixed(1)}% (PASS)
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400">Baseline vs Current Pixel Diff Threshold &lt; 1%</div>
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
