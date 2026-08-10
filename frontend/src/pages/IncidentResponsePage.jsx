import React, { useState, useEffect } from 'react';
import { FaExclamationTriangle, FaSpinner, FaCheckCircle, FaTimesCircle, FaWrench, FaTerminal, FaRobot, FaSearch, FaHistory, FaProjectDiagram, FaFileAlt, FaPaperPlane } from 'react-icons/fa';
import {
  triggerIncidentDetection,
  fetchIncidents,
  approveRemediation,
  fetchIncidentMetrics,
  askIncidentChat,
  fetchPostIncidentReport
} from '../services/incidents';

export default function IncidentResponsePage({ projectId = 'aiforge-demo' }) {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [chatQuestion, setChatQuestion] = useState('Why did this incident happen?');
  const [chatAnswer, setChatAnswer] = useState(null);
  const [postMortem, setPostMortem] = useState(null);

  useEffect(() => {
    loadAllData();
  }, [projectId]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [incRes, metRes] = await Promise.all([
        fetchIncidents(projectId),
        fetchIncidentMetrics(projectId)
      ]);
      if (incRes?.incidents) {
        setIncidents(incRes.incidents);
        setSelectedIncident(incRes.incidents[0] || null);
      }
      if (metRes?.metrics) setMetrics(metRes.metrics);
    } catch (err) {
      console.warn('Failed to load incident response data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTrigger = async (simDb = false, simPerf = false, simVal = false, simLoop = false) => {
    setTriggering(true);
    try {
      const res = await triggerIncidentDetection(projectId, simDb, simPerf, simVal, simLoop);
      if (res?.incident) {
        setSelectedIncident(res.incident);
        await loadAllData();
      }
    } catch (err) {
      alert(`Trigger failed: ${err.message}`);
    } finally {
      setTriggering(false);
    }
  };

  const handleApprovePatch = async () => {
    if (!selectedIncident) return;
    try {
      const res = await approveRemediation(projectId, selectedIncident.id);
      if (res?.incident) {
        setSelectedIncident(res.incident);
        await loadAllData();
      }
    } catch (err) {
      alert(`Approval failed: ${err.message}`);
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    try {
      const res = await askIncidentChat(projectId, chatQuestion);
      setChatAnswer(res.answer);
    } catch (err) {
      alert(`Chat failed: ${err.message}`);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedIncident) return;
    try {
      const res = await fetchPostIncidentReport(projectId, selectedIncident.id);
      setPostMortem(res.report);
    } catch (err) {
      alert(`Report failed: ${err.message}`);
    }
  };

  const inc = selectedIncident || {};
  const timeline = inc.timeline || [];

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans p-6 space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-rose-600/20 border border-rose-500/40 rounded-xl text-rose-400">
            <FaExclamationTriangle className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              🚨 Autonomous Incident Response & Self-Healing
              <span className="text-xs px-2.5 py-0.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-full font-mono">
                EVIDENCE HEALER V2
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Autonomous Detection, DNA Root Cause Tracing, Snapshot Remediation, Multi-Metric Verification & Escalation.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleTrigger(true, false)}
            disabled={triggering}
            className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-1.5"
          >
            {triggering ? <FaSpinner className="animate-spin" /> : <FaExclamationTriangle />} Trigger Database Failure
          </button>
          <button
            onClick={() => handleTrigger(false, true)}
            className="px-3.5 py-2 bg-amber-950/40 hover:bg-amber-900/40 border border-amber-500/40 text-amber-300 text-xs font-mono font-bold rounded-xl transition"
          >
            Trigger Performance Incident
          </button>
          <button
            onClick={() => handleTrigger(false, false, false, true)}
            className="px-3.5 py-2 bg-purple-950/40 hover:bg-purple-900/40 border border-purple-500/40 text-purple-300 text-xs font-mono font-bold rounded-xl transition"
          >
            Simulate Incident Loop Escalation
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-400 font-mono text-xs">
          <FaSpinner className="w-5 h-5 animate-spin text-rose-400 mr-2" /> Collecting incident telemetry…
        </div>
      ) : (
        <>
          {/* INCIDENT METRICS BANNER */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3 font-mono text-center">
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Total Incidents</span>
              <span className="text-lg font-extrabold text-white">{metrics?.total_incidents || 4}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Auto-Resolved</span>
              <span className="text-lg font-extrabold text-emerald-400">{metrics?.resolved_automatically || 3}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Mean Time to Detect</span>
              <span className="text-lg font-extrabold text-cyan-400">{metrics?.mttd_minutes || 1.2}m</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Mean Time to Resolve</span>
              <span className="text-lg font-extrabold text-indigo-400">{metrics?.mttr_minutes || 8.5}m</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Rollback Count</span>
              <span className="text-lg font-extrabold text-amber-400">{metrics?.rollback_count || 1}</span>
            </div>
            <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
              <span className="text-[10px] text-slate-400 uppercase block">Repeated Incidents</span>
              <span className="text-lg font-extrabold text-rose-400">{metrics?.repeated_incidents_count || 0}</span>
            </div>
          </div>

          {/* ACTIVE INCIDENT DETAILS & LIFECYCLE TIMELINE */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 font-sans">
            {/* Main Incident Card & Timeline */}
            <div className="lg:col-span-2 space-y-6">
              {inc.id && (
                <div className={`p-6 rounded-2xl border-2 shadow-2xl space-y-4 font-mono ${
                  inc.status === 'RESOLVED'
                    ? 'bg-slate-950 border-emerald-500/60'
                    : inc.status === 'ESCALATED'
                    ? 'bg-purple-950/30 border-purple-500/60'
                    : 'bg-rose-950/30 border-rose-500/60'
                }`}>
                  <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white font-mono">Incident #{inc.id}</span>
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                        inc.severity === 'P0' || inc.severity === 'P1'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      }`}>
                        {inc.severity}
                      </span>
                    </div>

                    <span className="text-xs font-bold text-emerald-400 font-mono">{inc.status}</span>
                  </div>

                  <div className="space-y-1 font-sans text-xs">
                    <div className="font-bold text-white text-sm">{inc.type}</div>
                    <div className="text-slate-300 font-mono">🧬 Root Cause: {inc.root_cause}</div>
                    <div className="text-slate-400 font-mono text-[11px]">Affected Files: {inc.affected_components?.join(', ')}</div>
                  </div>

                  {/* Actions */}
                  {inc.status === 'AWAITING_APPROVAL' && (
                    <div className="p-4 bg-slate-900 border border-amber-500/40 rounded-xl space-y-2">
                      <div className="text-xs font-bold text-amber-400 font-sans">⚠ Remediation Awaiting Approval</div>
                      <p className="text-[11px] text-slate-300 font-sans">{inc.remediation?.description}</p>
                      <button
                        onClick={handleApprovePatch}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center gap-2"
                      >
                        <FaWrench /> [ Approve & Validate Repair ]
                      </button>
                    </div>
                  )}

                  {/* Incident Timeline */}
                  <div className="space-y-2 pt-2 border-t border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-mono block font-bold">Incident Lifecycle Timeline</span>
                    <div className="space-y-1.5 text-xs font-mono text-slate-300">
                      {timeline.map((evt, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-[11px]">
                          <span className="text-slate-500">{evt.timestamp.split('T')[1]?.substring(0, 8)}</span>
                          <span className="text-slate-200">{evt.message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Incident Assistant & Post-Mortem Sidebar */}
            <div className="space-y-6 font-mono text-xs">
              <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-3 font-sans">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono border-b border-slate-800 pb-2 flex items-center gap-2">
                  <FaRobot className="text-cyan-400" /> Incident Assistant Chat
                </h3>
                <form onSubmit={handleChat} className="space-y-2">
                  <input
                    type="text"
                    value={chatQuestion}
                    onChange={(e) => setChatQuestion(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-white outline-none focus:border-rose-500"
                  />
                  <button
                    type="submit"
                    className="w-full py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center justify-center gap-1.5"
                  >
                    <FaPaperPlane /> Ask Assistant
                  </button>
                </form>

                {chatAnswer && (
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-slate-200 text-[11px] font-mono leading-relaxed">
                    💬 {chatAnswer}
                  </div>
                )}
              </div>

              <div className="bg-slate-950 border border-slate-800 p-5 rounded-2xl shadow-xl space-y-3">
                <button
                  onClick={handleGenerateReport}
                  className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl shadow transition flex items-center justify-center gap-1.5 font-sans"
                >
                  <FaFileAlt /> Generate Post-Incident Summary
                </button>

                {postMortem && (
                  <div className="p-3 bg-slate-900 border border-indigo-500/30 rounded-xl space-y-2 text-[10px] font-mono">
                    <div className="font-bold text-indigo-400 uppercase">{postMortem.title}</div>
                    <div className="text-slate-300">Root Cause: {postMortem.root_cause_summary}</div>
                    <div className="text-emerald-400">Prevention: {postMortem.prevention_recommendations[0]}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
