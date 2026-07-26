import React, { useState, useEffect } from 'react';
import { FaBrain, FaCheckCircle, FaProjectDiagram, FaTachometerAlt, FaFlask, FaSlidersH, FaServer } from 'react-icons/fa';

export default function ModelDashboard() {
  const [models, setModels] = useState([]);
  const [selectedTask, setSelectedTask] = useState('backend');
  const [routeResult, setRouteResult] = useState(null);
  const [consensusResult, setConsensusResult] = useState(null);
  const [benchmarks, setBenchmarks] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchModels = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/models');
      if (res.ok) {
        const data = await res.json();
        setModels(data.models || []);
      }
    } catch {
      // Fallback
      setModels([
        { id: 'qwen2.5-coder', name: 'Qwen 2.5 Coder 14B', provider: 'Ollama', status: 'online', capabilities: { backend: 10, frontend: 10, testing: 9 } },
        { id: 'deepseek-coder', name: 'DeepSeek Coder V2', provider: 'Ollama', status: 'online', capabilities: { architecture: 10, database: 10, security: 10 } },
        { id: 'llama3.1', name: 'Llama 3.1 8B Instruct', provider: 'Ollama', status: 'online', capabilities: { planning: 10, documentation: 10 } }
      ]);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleTestRoute = async (taskName) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/models/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_name: taskName })
      });
      if (res.ok) {
        const data = await res.json();
        setRouteResult(data);
      }
    } catch (err) {
      console.error('Route error:', err);
    }
  };

  const handleRunConsensus = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/models/consensus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: 'Design Microservices Architecture for Social Media', task_name: 'architecture' })
      });
      if (res.ok) {
        const data = await res.json();
        setConsensusResult(data);
      }
    } catch (err) {
      console.error('Consensus error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/models/benchmark', {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setBenchmarks(data.benchmark_results || {});
      }
    } catch (err) {
      console.error('Benchmark error:', err);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6 text-slate-100 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <FaBrain className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold tracking-wide text-white uppercase">
            Multi-LLM Intelligence, Model Routing & Consensus Engine
          </h3>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleRunBenchmark}
            className="bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5"
          >
            <FaTachometerAlt /> Benchmark LLMs
          </button>
          <button
            onClick={handleRunConsensus}
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 shadow"
          >
            <FaFlask /> Run Consensus
          </button>
        </div>
      </div>

      {/* Installed Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {models.map((m) => (
          <div key={m.id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white truncate">{m.name || m.id}</span>
              <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-semibold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                <FaCheckCircle className="w-2.5 h-2.5" /> ONLINE
              </span>
            </div>
            <p className="text-slate-400 text-[11px]">Provider: <strong className="text-slate-200">{m.provider || 'Ollama'}</strong></p>

            <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-400 space-y-1">
              {Object.entries(m.capabilities || {}).slice(0, 3).map(([cap, score]) => (
                <div key={cap} className="flex justify-between">
                  <span className="capitalize">{cap}:</span>
                  <span className="text-indigo-400 font-bold">{score}/10</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Interactive Router & Consensus Tester */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Router Test Box */}
        <div className="lg:col-span-6 bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
            <FaSlidersH className="text-indigo-400" /> Test Intelligent Task Router
          </h4>

          <div className="flex gap-2">
            <select
              value={selectedTask}
              onChange={(e) => {
                setSelectedTask(e.target.value);
                handleTestRoute(e.target.value);
              }}
              className="bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500 flex-1"
            >
              <option value="planning">Planner (Requirements)</option>
              <option value="architecture">Architect (System Design)</option>
              <option value="backend">Backend Agent (FastAPI)</option>
              <option value="frontend">Frontend Agent (React)</option>
              <option value="database">Database Agent (Schema)</option>
              <option value="security">Security Audit</option>
              <option value="documentation">Documentation Agent</option>
            </select>
            <button
              onClick={() => handleTestRoute(selectedTask)}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              Route Task
            </button>
          </div>

          {routeResult && (
            <div className="p-3 bg-slate-900 border border-slate-800/80 rounded-lg space-y-1.5">
              <div className="flex justify-between items-center text-[11px] font-bold">
                <span className="text-indigo-300">Target Task: {routeResult.task}</span>
                <span className="text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800 text-[10px]">
                  Rating: {routeResult.score}/10
                </span>
              </div>
              <p className="text-white text-xs font-bold">Selected Model: <span className="text-indigo-400">{routeResult.model_name || routeResult.selected_model}</span></p>
              <p className="text-slate-400 text-[11px] italic">Routing Reason: {routeResult.reason}</p>
            </div>
          )}
        </div>

        {/* Consensus Result Box */}
        <div className="lg:col-span-6 bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 font-mono text-xs">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
            <FaProjectDiagram className="text-emerald-400" /> Multi-Model Consensus Engine
          </h4>

          {consensusResult ? (
            <div className="p-3 bg-slate-900 border border-slate-800/80 rounded-lg space-y-2">
              <div className="flex justify-between items-center text-[11px] font-bold">
                <span className="text-emerald-400">Consensus Winner: {consensusResult.winner_model}</span>
                <span className="text-indigo-300 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800 text-[10px]">
                  Confidence: {consensusResult.confidence_score}%
                </span>
              </div>
              <p className="text-slate-300 text-[11px] leading-relaxed">{consensusResult.best_response}</p>
              <p className="text-slate-500 text-[10px]">Evaluated Models: {consensusResult.evaluated_models_count} candidates</p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center min-h-[120px] text-slate-500 text-xs italic text-center">
              Click 'Run Consensus' above to evaluate candidate models in parallel for critical tasks.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
