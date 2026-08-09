import React, { useState, useEffect } from 'react';
import { FaPlug, FaCheckCircle, FaTimesCircle, FaSync, FaShieldAlt, FaServer, FaTerminal, FaDatabase, FaDocker, FaGithub, FaAws, FaSlack, FaJira } from 'react-icons/fa';

export default function McpDashboard() {
  const [dashboard, setDashboard] = useState({
    total_servers: 12,
    connected_servers: 11,
    health_score_pct: 91.7,
    servers: {
      github: { name: 'github', status: 'connected', latency_ms: 145, last_sync: 'recent', tools_available: 4 },
      filesystem: { name: 'filesystem', status: 'connected', latency_ms: 12, last_sync: 'recent', tools_available: 3 },
      postgres: { name: 'postgres', status: 'connected', latency_ms: 24, last_sync: 'recent', tools_available: 2 },
      docker: { name: 'docker', status: 'connected', latency_ms: 35, last_sync: 'recent', tools_available: 2 },
      browser: { name: 'browser', status: 'connected', latency_ms: 180, last_sync: 'recent', tools_available: 1 },
      terminal: { name: 'terminal', status: 'connected', latency_ms: 8, last_sync: 'recent', tools_available: 1 },
      slack: { name: 'slack', status: 'offline', latency_ms: 0, last_sync: 'offline', tools_available: 1 },
      jira: { name: 'jira', status: 'connected', latency_ms: 195, last_sync: 'recent', tools_available: 1 }
    }
  });

  const [loading, setLoading] = useState(false);

  const fetchMcpData = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/mcp/dashboard');
      if (res.ok) {
        const data = await res.json();
        if (data.mcp_dashboard) setDashboard(data.mcp_dashboard);
      }
    } catch (err) {
      console.log('Using default MCP dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMcpData();
  }, []);

  const handleRefresh = async () => {
    fetchMcpData();
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FaPlug className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="text-sm font-bold tracking-wide text-white uppercase">
              Model Context Protocol (MCP) Ecosystem (Day 45)
            </h3>
            <p className="text-[11px] text-slate-400">Universal dynamic tool discovery, permission authorization & fallback engine</p>
          </div>
        </div>

        <button
          onClick={handleRefresh}
          disabled={loading}
          className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-xs px-3.5 py-2 rounded-lg transition cursor-pointer flex items-center gap-1.5 shadow w-fit"
        >
          <FaSync className={loading ? 'animate-spin' : ''} />
          {loading ? 'Syncing MCP Servers...' : 'Sync MCP Servers'}
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5 font-mono text-xs text-center">
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Total Servers</span>
          <span className="text-2xl font-extrabold text-white">{dashboard.total_servers}</span>
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] text-emerald-400 uppercase font-bold block mb-1">Connected</span>
          <span className="text-2xl font-extrabold text-emerald-400">{dashboard.connected_servers}</span>
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] text-cyan-400 uppercase font-bold block mb-1">Health Score</span>
          <span className="text-2xl font-extrabold text-cyan-400">{dashboard.health_score_pct}%</span>
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] text-amber-400 uppercase font-bold block mb-1">Permissions</span>
          <span className="text-xs font-extrabold text-amber-400 block mt-1">READ / WRITE / EXEC / ADMIN</span>
        </div>
      </div>

      {/* MCP Servers Grid */}
      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs">
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide mb-3 flex items-center gap-1.5">
          <FaServer className="text-cyan-400" /> Connected MCP Server Matrix
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          {Object.entries(dashboard.servers || {}).map(([name, s], idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border flex flex-col justify-between text-[11px] ${
                s.status === 'connected'
                  ? 'bg-slate-900 border-slate-800 text-slate-200'
                  : 'bg-rose-950/30 border-rose-900/60 text-rose-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-bold text-white uppercase">{name}</span>
                {s.status === 'connected' ? (
                  <FaCheckCircle className="text-emerald-400" />
                ) : (
                  <FaTimesCircle className="text-rose-400" />
                )}
              </div>

              <div className="space-y-0.5 text-[10px] text-slate-400">
                <p>Status: <strong className={s.status === 'connected' ? 'text-emerald-400' : 'text-rose-400'}>{s.status.toUpperCase()}</strong></p>
                <p>Latency: <strong className="text-white">{s.latency_ms}ms</strong></p>
                <p>Tools: <strong className="text-cyan-300">{s.tools_available || 3} capabilities</strong></p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
