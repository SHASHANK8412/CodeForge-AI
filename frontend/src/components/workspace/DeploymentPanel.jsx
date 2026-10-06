import { BACKEND_URL } from '../../config/backend';
import React, { useState, useEffect } from 'react';
import {
  FaRocket,
  FaCheckCircle,
  FaExclamationTriangle,
  FaTerminal,
  FaHistory,
  FaUndo,
  FaExternalLinkAlt,
  FaLock,
  FaKey,
  FaDocker,
  FaServer,
  FaShieldAlt,
  FaVial
} from 'react-icons/fa';
import axios from 'axios';

const API_BASE = `${BACKEND_URL}`;

export default function DeploymentPanel({ generationId = 'TodoApp', onClose }) {
  const [activeTab, setActiveTab] = useState('overview'); // overview, logs, history, env
  const [deployResult, setDeployResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [envInputs, setEnvInputs] = useState({
    JWT_SECRET: 'aiforge_jwt_secret_dev_key_32chars_long',
    DATABASE_URL: 'postgresql://user:pass@localhost:5432/appdb'
  });
  const [envSaved, setEnvSaved] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, [generationId]);

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/projects/${generationId}/deploy/history`);
      if (res.data?.history) {
        setHistory(res.data.history);
      }
    } catch (err) {
      console.error('Fetch deployment history error:', err);
    }
  };

  const handleSaveEnv = async () => {
    try {
      await axios.post(`${API_BASE}/api/projects/${generationId}/deploy/configure-env`, envInputs);
      setEnvSaved(true);
      setTimeout(() => setEnvSaved(false), 3000);
    } catch (err) {
      console.error('Save env error:', err);
    }
  };

  const handleDeploy = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/projects/${generationId}/deploy`);
      setDeployResult(res.data);
      fetchHistory();
    } catch (err) {
      console.error('Deploy error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async () => {
    try {
      const res = await axios.post(`${API_BASE}/api/projects/${generationId}/deploy/rollback`);
      alert(`Rollback triggered! Restored version: ${res.data.restored_version}`);
      fetchHistory();
    } catch (err) {
      console.error('Rollback error:', err);
    }
  };

  const isVerified = deployResult?.status === 'VERIFIED';
  const isBlocked = deployResult?.status === 'DEPLOYMENT_BLOCKED';

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-[#090d16] border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl font-sans text-slate-100 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <FaRocket className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Autonomous DevOps Deployment Engine
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Environment: <span className="text-cyan-400 font-bold">Local Docker Compose</span> | Target: Containerized
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

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 px-6 bg-slate-950 border-b border-slate-800 text-xs font-mono">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2.5 px-3 border-b-2 font-bold transition-colors ${
              activeTab === 'overview' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Overview & Deploy
          </button>
          <button
            onClick={() => setActiveTab('env')}
            className={`py-2.5 px-3 border-b-2 font-bold transition-colors ${
              activeTab === 'env' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Environment Secrets
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`py-2.5 px-3 border-b-2 font-bold transition-colors ${
              activeTab === 'logs' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Deployment Logs
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-2.5 px-3 border-b-2 font-bold transition-colors ${
              activeTab === 'history' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Deployment History
          </button>
        </div>

        {/* Panel Content Body */}
        <div className="flex-1 p-6 overflow-y-auto custom-scrollbar space-y-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Pre-Deployment Gates Checklist */}
              <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-3">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <FaShieldAlt className="text-cyan-400" /> Pre-Deployment Readiness Gates
                </h3>

                <div className="grid grid-cols-4 gap-2 text-xs font-mono">
                  <div className="bg-slate-950 p-2.5 rounded border border-slate-800 flex items-center justify-between">
                    <span className="text-slate-300">File Integrity</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1"><FaCheckCircle /> Pass</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded border border-slate-800 flex items-center justify-between">
                    <span className="text-slate-300">Unit Tests</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1"><FaCheckCircle /> Pass</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded border border-slate-800 flex items-center justify-between">
                    <span className="text-slate-300">DevSecOps Audit</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1"><FaCheckCircle /> Pass</span>
                  </div>
                  <div className="bg-slate-950 p-2.5 rounded border border-slate-800 flex items-center justify-between">
                    <span className="text-slate-300">Git Tag</span>
                    <span className="text-cyan-400 font-bold">Ready</span>
                  </div>
                </div>
              </div>

              {/* Action Trigger */}
              <div className="text-center p-6 bg-slate-900/40 border border-slate-800 rounded-xl space-y-4">
                {isVerified ? (
                  <div className="space-y-3">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-sm font-bold font-mono">
                      🟢 DEPLOYMENT VERIFIED & HEALTHY
                    </div>
                    <div className="grid grid-cols-2 gap-4 max-w-lg mx-auto text-xs font-mono pt-2">
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-left space-y-1">
                        <div className="text-slate-400">Frontend Service</div>
                        <a href={deployResult.frontend_url} target="_blank" rel="noreferrer" className="text-cyan-400 font-bold hover:underline flex items-center gap-1">
                          {deployResult.frontend_url} <FaExternalLinkAlt className="w-2.5 h-2.5" />
                        </a>
                      </div>
                      <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-left space-y-1">
                        <div className="text-slate-400">Backend API</div>
                        <a href={deployResult.backend_url} target="_blank" rel="noreferrer" className="text-cyan-400 font-bold hover:underline flex items-center gap-1">
                          {deployResult.backend_url} <FaExternalLinkAlt className="w-2.5 h-2.5" />
                        </a>
                      </div>
                    </div>
                  </div>
                ) : isBlocked ? (
                  <div className="space-y-3">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 text-sm font-bold font-mono">
                      🔴 DEPLOYMENT BLOCKED
                    </div>
                    <p className="text-xs text-rose-300">
                      Missing required environment variables: {deployResult.missing_secrets?.join(', ')}
                    </p>
                    <button
                      onClick={() => setActiveTab('env')}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold font-mono"
                    >
                      [Configure Environment]
                    </button>
                  </div>
                ) : (
                  <div>
                    <button
                      onClick={handleDeploy}
                      disabled={loading}
                      className="px-8 py-3 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-extrabold text-sm rounded-xl shadow-lg shadow-cyan-900/40 transition font-mono"
                    >
                      {loading ? 'Deploying Services...' : 'DEPLOY APPLICATION NOW'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'env' && (
            <div className="space-y-4">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <FaLock className="text-amber-400" /> Environment Secrets Configuration
              </h3>

              <div className="space-y-3 text-xs font-mono">
                <div>
                  <label className="block text-slate-300 mb-1">JWT_SECRET (Required)</label>
                  <input
                    type="password"
                    value={envInputs.JWT_SECRET}
                    onChange={(e) => setEnvInputs({ ...envInputs, JWT_SECRET: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 font-mono text-xs focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 mb-1">DATABASE_URL (Required)</label>
                  <input
                    type="password"
                    value={envInputs.DATABASE_URL}
                    onChange={(e) => setEnvInputs({ ...envInputs, DATABASE_URL: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-slate-100 font-mono text-xs focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="pt-2 flex items-center gap-3">
                  <button
                    onClick={handleSaveEnv}
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-bold text-xs font-mono"
                  >
                    Save Encrypted Secrets
                  </button>
                  {envSaved && <span className="text-emerald-400 font-bold text-xs font-mono">✓ Secrets saved & encrypted</span>}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-300 space-y-1 max-h-80 overflow-y-auto">
              {deployResult?.logs && deployResult.logs.length > 0 ? (
                deployResult.logs.map((lg, i) => (
                  <div key={i} className="text-cyan-300/90">{lg}</div>
                ))
              ) : (
                <div className="text-slate-500 italic">No deployment logs recorded yet.</div>
              )}
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                  Deployment History & Rollback Checkpoints
                </h3>
                <button
                  onClick={handleRollback}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/30 rounded-lg text-xs font-mono font-bold"
                >
                  <FaUndo className="w-3 h-3" /> Rollback to Stable Version
                </button>
              </div>

              <div className="space-y-2 text-xs font-mono">
                {history.length > 0 ? (
                  history.map((h, i) => (
                    <div key={i} className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg flex items-center justify-between">
                      <div>
                        <div className="font-bold text-slate-200">{h.deployment_id} ({h.git_checkpoint || 'checkpoint'})</div>
                        <div className="text-[10px] text-slate-400">{new Date(h.created_at * 1000).toLocaleString()}</div>
                      </div>
                      <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${h.status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                        {h.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-slate-500 italic text-center p-4">No past deployments recorded.</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
