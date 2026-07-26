import React, { useState, useEffect } from 'react';
import { FaPlug, FaTerminal, FaFolder, FaGitAlt, FaDatabase, FaDocker, FaGlobe, FaCode, FaCheckCircle, FaTimesCircle, FaPlay, FaHistory } from 'react-icons/fa';

export default function PluginDashboard() {
  const [plugins, setPlugins] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedPlugin, setSelectedPlugin] = useState('filesystem');
  const [testAction, setTestAction] = useState('list');
  const [execResult, setExecResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchPlugins = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/plugins');
      if (res.ok) {
        const data = await res.json();
        setPlugins(data.plugins || []);
      }
    } catch {
      setPlugins([
        { id: 'filesystem', name: 'Filesystem Tool', version: '1.0.0', enabled: true, permissions: ['read_files', 'write_files'], execution_count: 12 },
        { id: 'terminal', name: 'Terminal Execution', version: '1.0.0', enabled: true, permissions: ['execute_commands'], execution_count: 5 },
        { id: 'git', name: 'Git Repository Tool', version: '1.0.0', enabled: true, permissions: ['git_ops'], execution_count: 8 },
        { id: 'postgres', name: 'PostgreSQL Tool', version: '1.0.0', enabled: true, permissions: ['db_ops'], execution_count: 4 }
      ]);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/plugins/logs');
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch {
      setLogs([
        { tool_name: 'filesystem', status: 'success', execution_time_seconds: 0.002, params: { action: 'list' }, timestamp: Date.now() / 1000 }
      ]);
    }
  };

  useEffect(() => {
    fetchPlugins();
    fetchLogs();
  }, []);

  const togglePlugin = async (pluginId, currentEnabled) => {
    const endpoint = currentEnabled ? 'disable' : 'enable';
    try {
      await fetch(`http://127.0.0.1:8000/api/plugins/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plugin_id: pluginId })
      });
      fetchPlugins();
    } catch (err) {
      console.error('Toggle plugin error:', err);
    }
  };

  const handleExecuteTool = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/plugins/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plugin_id: selectedPlugin,
          params: { action: testAction, path: '.' }
        })
      });
      if (res.ok) {
        const data = await res.json();
        setExecResult(data);
        fetchLogs();
        fetchPlugins();
      }
    } catch (err) {
      console.error('Tool execution error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FaPlug className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold tracking-wide text-white uppercase">
            Autonomous Plugin & Tool Execution Framework
          </h3>
        </div>

        <button
          onClick={handleExecuteTool}
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-3.5 py-2 rounded-lg transition cursor-pointer flex items-center gap-1.5 shadow"
        >
          <FaPlay className="w-3 h-3" /> Test Tool Execution
        </button>
      </div>

      {/* Plugin Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        {plugins.map((p) => (
          <div key={p.id} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 flex flex-col justify-between font-mono text-xs">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-bold text-white truncate">{p.name || p.id}</span>
                <button
                  onClick={() => togglePlugin(p.id, p.enabled)}
                  className={`px-2 py-0.5 rounded text-[10px] font-semibold cursor-pointer border ${
                    p.enabled
                      ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  {p.enabled ? 'ENABLED' : 'DISABLED'}
                </button>
              </div>
              <p className="text-slate-400 text-[11px]">Version: <span className="text-slate-200">{p.version}</span></p>
            </div>

            <div className="pt-2 border-t border-slate-800 flex justify-between text-[10px] text-slate-400 mt-3">
              <span>Executions: <strong className="text-indigo-400">{p.execution_count}</strong></span>
              <span className="truncate max-w-[120px]">{p.permissions?.join(', ')}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Tool Tester & Execution Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Tool Execution Tester */}
        <div className="lg:col-span-5 bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
            <FaTerminal className="text-indigo-400" /> Interactive Tool Executor
          </h4>

          <div className="space-y-2">
            <label className="text-[11px] text-slate-400">Select Plugin Tool:</label>
            <select
              value={selectedPlugin}
              onChange={(e) => setSelectedPlugin(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              {plugins.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.id})</option>
              ))}
            </select>

            <button
              onClick={handleExecuteTool}
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5"
            >
              <FaPlay className="w-3 h-3" /> Execute Selected Plugin Tool
            </button>
          </div>

          {execResult && (
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1 text-[11px]">
              <div className="flex justify-between font-bold">
                <span className="text-emerald-400">Status: {execResult.status}</span>
                <span className="text-slate-400">{execResult.execution_time_seconds}s</span>
              </div>
              <pre className="text-slate-300 text-[10px] overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(execResult.result || execResult, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Execution Logs */}
        <div className="lg:col-span-7 bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
            <FaHistory className="text-emerald-400" /> Tool Execution Telemetry Logs
          </h4>

          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {logs.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-xs italic">No execution logs recorded yet.</div>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="p-2.5 bg-slate-900 border border-slate-800/80 rounded-lg flex items-center justify-between text-[11px]">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-indigo-300">{log.tool_name}</span>
                    <span className="text-slate-500 text-[10px]">{JSON.stringify(log.params)}</span>
                  </div>
                  <span className="text-emerald-400 font-bold">{log.execution_time_seconds}s</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
