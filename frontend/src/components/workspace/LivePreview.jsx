import { BACKEND_URL } from '../../config/backend';
import React, { useState, useEffect } from 'react';
import {
  FaPlay,
  FaStop,
  FaRedo,
  FaExternalLinkAlt,
  FaCheckCircle,
  FaExclamationTriangle,
  FaTerminal,
  FaNetworkWired,
  FaVial,
  FaListUl,
  FaShieldAlt,
  FaServer,
  FaDatabase
} from 'react-icons/fa';
import axios from 'axios';

const API_BASE = `${BACKEND_URL}`;

export default function LivePreview({ generationId = 'TodoApp', onClose }) {
  const [activeTab, setActiveTab] = useState('console'); // console, network, tests, logs
  const [statusState, setStatusState] = useState({
    status: 'STOPPED',
    frontend_url: 'http://localhost:5173',
    backend_url: `${BACKEND_URL}`,
    frontend_status: 'STOPPED',
    backend_status: 'STOPPED',
    database_status: 'CONNECTED',
    health_status: 'HEALTHY',
    quality_score: 96.0,
    logs: []
  });
  const [logsData, setLogsData] = useState({ stdout: [], stderr: [] });
  const [networkLogs, setNetworkLogs] = useState([
    { method: 'GET', url: '/health', status: 200, latency: '12ms' },
    { method: 'POST', url: '/api/auth/login', status: 200, latency: '45ms' },
    { method: 'GET', url: '/api/core', status: 200, latency: '28ms' }
  ]);
  const [e2eResults, setE2eResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [generationId]);

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/projects/${generationId}/preview/status`);
      if (res.data) {
        setStatusState(res.data);
      }
      const logsRes = await axios.get(`${API_BASE}/api/projects/${generationId}/preview/logs`);
      if (logsRes.data) {
        setLogsData({
          stdout: logsRes.data.backend?.stdout || [],
          stderr: logsRes.data.backend?.stderr || []
        });
      }
    } catch (err) {
      console.error('Failed to fetch preview status:', err);
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/projects/${generationId}/preview/start`);
      setStatusState(res.data);
    } catch (err) {
      console.error('Start error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      await axios.post(`${API_BASE}/api/projects/${generationId}/preview/stop`);
      setStatusState((prev) => ({ ...prev, status: 'STOPPED', frontend_status: 'STOPPED', backend_status: 'STOPPED' }));
    } catch (err) {
      console.error('Stop error:', err);
    }
  };

  const handleRunE2E = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/projects/${generationId}/e2e`);
      setE2eResults(res.data);
      setActiveTab('tests');
    } catch (err) {
      console.error('E2E error:', err);
    } finally {
      setLoading(false);
    }
  };

  const isRunning = statusState.status === 'RUNNING' || statusState.status === 'VERIFIED';

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 font-sans border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            className="text-xs font-mono text-slate-400 hover:text-white bg-slate-800 px-2.5 py-1 rounded transition-colors"
          >
            ← Back
          </button>
          <span className="font-bold text-sm tracking-wide text-cyan-400 flex items-center gap-2">
            AIForge Preview Engine
          </span>
          <span
            className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full flex items-center gap-1 ${
              isRunning ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
            }`}
          >
            ● {statusState.status}
          </span>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {!isRunning ? (
            <button
              onClick={handleStart}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold font-mono transition-colors shadow-lg shadow-emerald-900/30"
            >
              <FaPlay className="w-2.5 h-2.5" /> Run
            </button>
          ) : (
            <button
              onClick={handleStop}
              className="flex items-center gap-1.5 px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-bold font-mono transition-colors"
            >
              <FaStop className="w-2.5 h-2.5" /> Stop
            </button>
          )}

          <button
            onClick={handleStart}
            disabled={loading}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-mono"
            title="Restart Application"
          >
            <FaRedo className="w-2.5 h-2.5" /> Restart
          </button>

          <button
            onClick={handleRunE2E}
            disabled={loading}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-300 border border-cyan-500/30 rounded text-xs font-mono font-bold"
          >
            <FaVial className="w-2.5 h-2.5" /> Run E2E
          </button>

          {statusState.frontend_url && (
            <a
              href={statusState.frontend_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-mono"
              title="Open in Browser"
            >
              <FaExternalLinkAlt className="w-2.5 h-2.5" /> Open
            </a>
          )}
        </div>
      </div>

      {/* Status Indicators Dashboard */}
      <div className="grid grid-cols-5 gap-2 p-2 bg-slate-950 border-b border-slate-800/80 text-[11px] font-mono">
        <div className="bg-slate-900/90 p-2 rounded border border-slate-800 flex items-center justify-between">
          <span className="text-slate-400 flex items-center gap-1"><FaServer className="text-indigo-400" /> Frontend</span>
          <span className={statusState.frontend_status === 'RUNNING' ? 'text-emerald-400 font-bold' : 'text-slate-500'}>
            {statusState.frontend_status}
          </span>
        </div>

        <div className="bg-slate-900/90 p-2 rounded border border-slate-800 flex items-center justify-between">
          <span className="text-slate-400 flex items-center gap-1"><FaServer className="text-cyan-400" /> Backend</span>
          <span className={statusState.backend_status === 'RUNNING' ? 'text-emerald-400 font-bold' : 'text-slate-500'}>
            {statusState.backend_status}
          </span>
        </div>

        <div className="bg-slate-900/90 p-2 rounded border border-slate-800 flex items-center justify-between">
          <span className="text-slate-400 flex items-center gap-1"><FaDatabase className="text-amber-400" /> Database</span>
          <span className="text-emerald-400 font-bold">{statusState.database_status}</span>
        </div>

        <div className="bg-slate-900/90 p-2 rounded border border-slate-800 flex items-center justify-between">
          <span className="text-slate-400 flex items-center gap-1"><FaCheckCircle className="text-emerald-400" /> Health</span>
          <span className={statusState.health_status === 'HEALTHY' ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
            {statusState.health_status}
          </span>
        </div>

        <div className="bg-slate-900/90 p-2 rounded border border-slate-800 flex items-center justify-between">
          <span className="text-slate-400 flex items-center gap-1"><FaShieldAlt className="text-purple-400" /> Overall</span>
          <span className="text-emerald-400 font-extrabold">{statusState.status === 'VERIFIED' ? '🟢 VERIFIED' : 'RUNNING'}</span>
        </div>
      </div>

      {/* Main Preview Workspace Frame */}
      <div className="flex-1 bg-slate-900/50 relative flex flex-col justify-center items-center overflow-hidden">
        {isRunning && statusState.frontend_url ? (
          <iframe
            src={statusState.frontend_url}
            title="AIForge Live Application Preview"
            className="w-full h-full border-none bg-white"
          />
        ) : (
          <div className="text-center p-8 space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-between justify-center mx-auto text-cyan-400 text-xl font-bold">
              ▶
            </div>
            <h3 className="text-lg font-bold text-slate-200">Application Off-Air</h3>
            <p className="text-xs text-slate-400 max-w-md">
              Click <strong className="text-emerald-400">Run</strong> to compile, bind ports, start services, and render the live application preview inside AIForge.
            </p>
          </div>
        )}
      </div>

      {/* Bottom Panel Tabs */}
      <div className="h-44 bg-slate-950 border-t border-slate-800 flex flex-col font-mono text-xs">
        {/* Tab Headers */}
        <div className="flex items-center gap-1 px-2 bg-slate-900 border-b border-slate-800 text-[11px]">
          <button
            onClick={() => setActiveTab('console')}
            className={`px-3 py-1.5 font-bold flex items-center gap-1.5 border-b-2 transition-colors ${
              activeTab === 'console' ? 'border-cyan-400 text-cyan-400 bg-slate-950/60' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FaTerminal className="w-3 h-3" /> Console Logs
          </button>

          <button
            onClick={() => setActiveTab('network')}
            className={`px-3 py-1.5 font-bold flex items-center gap-1.5 border-b-2 transition-colors ${
              activeTab === 'network' ? 'border-cyan-400 text-cyan-400 bg-slate-950/60' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FaNetworkWired className="w-3 h-3" /> Network
          </button>

          <button
            onClick={() => setActiveTab('tests')}
            className={`px-3 py-1.5 font-bold flex items-center gap-1.5 border-b-2 transition-colors ${
              activeTab === 'tests' ? 'border-cyan-400 text-cyan-400 bg-slate-950/60' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FaVial className="w-3 h-3" /> E2E Tests
          </button>

          <button
            onClick={() => setActiveTab('logs')}
            className={`px-3 py-1.5 font-bold flex items-center gap-1.5 border-b-2 transition-colors ${
              activeTab === 'logs' ? 'border-cyan-400 text-cyan-400 bg-slate-950/60' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FaListUl className="w-3 h-3" /> Lifecycle
          </button>
        </div>

        {/* Tab Content */}
        <div className="flex-1 p-2.5 overflow-y-auto custom-scrollbar text-[11px] leading-relaxed">
          {activeTab === 'console' && (
            <div className="space-y-1 font-mono text-slate-300">
              {logsData.stdout.length > 0 ? (
                logsData.stdout.map((l, i) => (
                  <div key={i} className="text-emerald-400/90">{l}</div>
                ))
              ) : (
                <div className="text-slate-500 italic">No console logs outputted yet.</div>
              )}
              {logsData.stderr.map((err, i) => (
                <div key={`err-${i}`} className="text-rose-400 flex items-center justify-between bg-rose-950/30 px-2 py-0.5 rounded border border-rose-900/40">
                  <span>{err}</span>
                  <button className="text-[9px] bg-rose-900/80 text-white px-2 py-0.5 rounded font-bold hover:bg-rose-800">
                    [Diagnose]
                  </button>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'network' && (
            <div className="space-y-1 font-mono">
              <div className="grid grid-cols-4 font-bold text-slate-500 border-b border-slate-800 pb-1 text-[10px] uppercase">
                <span>Method</span>
                <span>Endpoint</span>
                <span>Status</span>
                <span>Latency</span>
              </div>
              {networkLogs.map((req, i) => (
                <div key={i} className="grid grid-cols-4 text-slate-300 py-0.5 hover:bg-slate-900/60 rounded">
                  <span className="font-bold text-indigo-400">{req.method}</span>
                  <span className="text-slate-200">{req.url}</span>
                  <span className={req.status === 200 ? 'text-emerald-400' : 'text-rose-400'}>{req.status}</span>
                  <span className="text-slate-400">{req.latency}</span>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'tests' && (
            <div className="space-y-1.5">
              {e2eResults ? (
                <div>
                  <div className="flex items-center justify-between mb-2 pb-1 border-b border-slate-800 font-bold">
                    <span>E2E Interaction Results</span>
                    <span className="text-emerald-400">{e2eResults.passed}/{e2eResults.total} PASSED</span>
                  </div>
                  {e2eResults.cases.map((c, idx) => (
                    <div key={idx} className="flex items-center justify-between px-2 py-1 bg-slate-900/80 rounded border border-slate-800/80 mb-1">
                      <span className="font-medium text-slate-200">{c.name}</span>
                      <span className={c.passed ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                        {c.passed ? '✓ PASS' : '❌ FAIL'} ({c.duration_ms}ms)
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-slate-500 italic">Click <strong className="text-cyan-400 font-mono">Run E2E</strong> to execute interaction tests against the running app.</div>
              )}
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="space-y-1 font-mono text-slate-400">
              {statusState.logs && statusState.logs.length > 0 ? (
                statusState.logs.map((lg, i) => (
                  <div key={i} className="text-cyan-300/90">{lg}</div>
                ))
              ) : (
                <div className="text-slate-500 italic">No lifecycle logs recorded.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
