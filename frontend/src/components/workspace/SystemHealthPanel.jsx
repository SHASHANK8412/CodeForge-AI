import { BACKEND_URL } from '../../config/backend';
import React, { useState, useEffect } from 'react';
import {
  FaHeartbeat,
  FaCheckCircle,
  FaExclamationTriangle,
  FaServer,
  FaDatabase,
  FaTerminal,
  FaTachometerAlt,
  FaShieldAlt,
  FaWrench,
  FaUndo
} from 'react-icons/fa';
import axios from 'axios';

const API_BASE = `${BACKEND_URL}`;

export default function SystemHealthPanel({ generationId = 'TodoApp', onClose }) {
  const [activeTab, setActiveTab] = useState('health'); // health, metrics, errors, logs
  const [healthData, setHealthData] = useState({
    frontend_status: 'HEALTHY',
    backend_status: 'HEALTHY',
    database_status: 'HEALTHY',
    metrics: { request_count: 120, error_count: 0, error_rate_percent: 0.0, avg_latency_ms: 45.2, p95_latency_ms: 110.0 },
    active_incidents: []
  });
  const [logs, setLogs] = useState([]);
  const [errorClusters, setErrorClusters] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchObservability();
    const interval = setInterval(fetchObservability, 4000);
    return () => clearInterval(interval);
  }, [generationId]);

  const fetchObservability = async () => {
    try {
      const hRes = await axios.get(`${API_BASE}/api/projects/${generationId}/observability/health`);
      if (hRes.data) setHealthData(hRes.data);

      const mRes = await axios.get(`${API_BASE}/api/projects/${generationId}/observability/metrics`);
      if (mRes.data?.error_clusters) setErrorClusters(mRes.data.error_clusters);

      const lRes = await axios.get(`${API_BASE}/api/projects/${generationId}/observability/logs`);
      if (lRes.data?.logs) setLogs(lRes.data.logs);
    } catch (err) {
      console.error('Fetch observability error:', err);
    }
  };

  const handleDiagnose = async (incId) => {
    try {
      const res = await axios.post(`${API_BASE}/api/projects/${generationId}/incidents/${incId}/diagnose`);
      alert(`Diagnosis Complete!\nRoot Cause: ${res.data.root_cause}\nCorrelated Git Commit: ${res.data.git_commit}`);
      fetchObservability();
    } catch (err) {
      console.error('Diagnose error:', err);
    }
  };

  const handleRepair = async (incId) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/projects/${generationId}/incidents/${incId}/repair`);
      alert(`Remediation Complete! Status: ${res.data.status}`);
      fetchObservability();
    } catch (err) {
      console.error('Repair error:', err);
    } finally {
      setLoading(false);
    }
  };

  const isHealthy = healthData.backend_status === 'HEALTHY' && healthData.frontend_status === 'HEALTHY';

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-[#090d16] border border-slate-800 rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl font-sans text-slate-100 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <FaHeartbeat className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Observability & Autonomous Incident Response
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Project: <strong className="text-white">{generationId}</strong> | Real-Time Telemetry & SRE Engine
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-xs font-mono text-slate-400 hover:text-white bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700 transition"
          >
            ✕ Close
          </button>
        </div>

        {/* Top Health & Latency Dashboard Banner */}
        <div className="grid grid-cols-6 gap-2.5 p-4 bg-slate-950 border-b border-slate-800 text-xs font-mono">
          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Frontend</div>
            <div className={`text-sm font-bold mt-0.5 ${healthData.frontend_status === 'HEALTHY' ? 'text-emerald-400' : 'text-rose-400'}`}>
              ● {healthData.frontend_status}
            </div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Backend API</div>
            <div className={`text-sm font-bold mt-0.5 ${healthData.backend_status === 'HEALTHY' ? 'text-emerald-400' : 'text-rose-400'}`}>
              ● {healthData.backend_status}
            </div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Error Rate</div>
            <div className="text-sm font-bold text-cyan-400 mt-0.5">{healthData.metrics?.error_rate_percent || 0.0}%</div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Avg Latency</div>
            <div className="text-sm font-bold text-indigo-400 mt-0.5">{healthData.metrics?.avg_latency_ms || 0}ms</div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">P95 Latency</div>
            <div className="text-sm font-bold text-amber-400 mt-0.5">{healthData.metrics?.p95_latency_ms || 0}ms</div>
          </div>

          <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Active Incidents</div>
            <div className={`text-sm font-bold mt-0.5 ${healthData.active_incidents?.length > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {healthData.active_incidents?.length || 0}
            </div>
          </div>
        </div>

        {/* Tab Headers */}
        <div className="flex items-center gap-2 px-6 bg-slate-950 border-b border-slate-800 text-xs font-mono">
          <button
            onClick={() => setActiveTab('health')}
            className={`py-2.5 px-3 border-b-2 font-bold transition-colors ${
              activeTab === 'health' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            System Health & Incidents
          </button>
          <button
            onClick={() => setActiveTab('errors')}
            className={`py-2.5 px-3 border-b-2 font-bold transition-colors ${
              activeTab === 'errors' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Error Clusters ({errorClusters.length})
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`py-2.5 px-3 border-b-2 font-bold transition-colors ${
              activeTab === 'logs' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Redacted Log Stream
          </button>
        </div>

        {/* Tab Content Body */}
        <div className="flex-1 p-6 overflow-y-auto custom-scrollbar space-y-6">
          {activeTab === 'health' && (
            <div className="space-y-5">
              {/* Active Incidents Section */}
              <div className="space-y-3 font-mono">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <FaExclamationTriangle className="text-amber-400" /> Active Incident Timeline
                </h3>

                {healthData.active_incidents && healthData.active_incidents.length > 0 ? (
                  healthData.active_incidents.map((inc, i) => (
                    <div key={i} className="p-4 bg-slate-900 border border-rose-500/40 rounded-xl space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            {inc.severity}
                          </span>
                          <span className="font-bold text-white text-xs">{inc.incident_id} ({inc.service})</span>
                        </div>
                        <span className="text-xs text-amber-400 font-bold">Status: {inc.status}</span>
                      </div>

                      <div className="text-xs text-slate-300">
                        <strong>Symptoms:</strong> {inc.symptoms?.join(', ')}
                      </div>

                      {inc.root_cause && (
                        <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-xs text-cyan-300">
                          <strong>Root Cause Diagnosis:</strong> {inc.root_cause} (Correlated Git: <code>{inc.git_commit}</code>)
                        </div>
                      )}

                      <div className="flex items-center gap-3 pt-1">
                        <button
                          onClick={() => handleDiagnose(inc.incident_id)}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-bold"
                        >
                          Diagnose Root Cause
                        </button>
                        <button
                          onClick={() => handleRepair(inc.incident_id)}
                          disabled={loading}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold flex items-center gap-1"
                        >
                          <FaWrench className="w-3 h-3" /> Autonomous Remediation
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center p-6 bg-slate-900/40 border border-slate-800 rounded-xl text-xs text-slate-400">
                    🟢 No active incidents detected. Application is operating within normal parameters.
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'errors' && (
            <div className="space-y-3 font-mono text-xs">
              <h3 className="font-bold uppercase text-slate-400 text-xs">Categorized Error Clusters</h3>
              {errorClusters.length > 0 ? (
                errorClusters.map((c, i) => (
                  <div key={i} className="p-3 bg-slate-900 rounded-lg border border-slate-800 flex items-center justify-between">
                    <div>
                      <div className="font-bold text-rose-400">{c.category} ({c.occurrences} occurrences)</div>
                      <div className="text-slate-300 text-[11px] mt-0.5">{c.sample_error}</div>
                    </div>
                    <div className="text-slate-400 text-[10px]">Endpoints: {c.affected_endpoints?.join(', ')}</div>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 italic text-center p-4">No error clusters recorded.</div>
              )}
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 space-y-1.5 max-h-80 overflow-y-auto">
              {logs.length > 0 ? (
                logs.map((l, i) => (
                  <div key={i} className="flex items-center gap-3 py-0.5 border-b border-slate-900/60">
                    <span className="text-slate-500 text-[10px]">{l.formatted_time}</span>
                    <span className={`font-bold text-[10px] px-1.5 py-0.2 rounded ${l.level === 'ERROR' ? 'bg-rose-900/40 text-rose-400' : 'bg-slate-800 text-cyan-400'}`}>
                      {l.level}
                    </span>
                    <span className="text-slate-400 text-[10px]">[{l.service}]</span>
                    <span className="text-slate-200">{l.message}</span>
                  </div>
                ))
              ) : (
                <div className="text-slate-500 italic">No log entries available.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
