import React from 'react';
import { FaLayerGroup, FaServer, FaDiagramProject, FaRobot, FaMicrochip, FaArrowDown, FaMemory } from 'react-icons/fa6';

export default function Architecture() {
  const agents = [
    'Planner', 'Architect', 'Frontend', 'Backend',
    'Database', 'Reviewer', 'Testing', 'Documentation'
  ];

  return (
    <section id="architecture" className="py-20 bg-[#090d16] font-sans border-t border-slate-800/60 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs uppercase tracking-widest font-mono text-cyan-400 font-bold mb-2">
            Technical System Architecture
          </h2>
          <p className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
            Built as a Multi-Agent Engineering System
          </p>
          <p className="text-slate-300 text-base sm:text-lg">
            Decoupled micro-architecture designed for deterministic orchestration, local LLM execution, and empirical code validation.
          </p>
        </div>

        {/* System Architecture Flow Visualizer */}
        <div className="max-w-4xl mx-auto space-y-4 font-mono text-xs">
          {/* Layer 1: React Frontend */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4 border-l-4 border-l-cyan-400">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20 text-lg">
                ⚛️
              </div>
              <div>
                <h4 className="text-sm font-bold text-white font-sans">React + Vite Single Page Application</h4>
                <p className="text-xs text-slate-400 font-sans">Real-time SSE event streaming, IDE code editor, evaluation dashboard</p>
              </div>
            </div>
            <span className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-cyan-400 text-[11px]">HTTP REST / SSE Stream</span>
          </div>

          <div className="flex justify-center text-slate-600">
            <FaArrowDown className="w-4 h-4 animate-bounce text-cyan-400" />
          </div>

          {/* Layer 2: FastAPI Backend */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4 border-l-4 border-l-indigo-500">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20 text-lg">
                ⚡
              </div>
              <div>
                <h4 className="text-sm font-bold text-white font-sans">FastAPI Async Core Backend</h4>
                <p className="text-xs text-slate-400 font-sans">Centralized ProjectState, REST APIs, WebSocket streaming, Export Gate validation</p>
              </div>
            </div>
            <span className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-indigo-400 text-[11px]">Python 3.11 Async Engine</span>
          </div>

          <div className="flex justify-center text-slate-600">
            <FaArrowDown className="w-4 h-4 text-indigo-400" />
          </div>

          {/* Layer 3: LangGraph Orchestrator */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4 border-l-4 border-l-purple-500">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20">
                <FaDiagramProject className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white font-sans">LangGraph Parallel State Orchestrator</h4>
                <p className="text-xs text-slate-400 font-sans">Parallel graph nodes, self-correction repair loop, state checkpoints</p>
              </div>
            </div>
            <span className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-purple-400 text-[11px]">Deterministic State Graph</span>
          </div>

          <div className="flex justify-center text-slate-600">
            <FaArrowDown className="w-4 h-4 text-purple-400" />
          </div>

          {/* Layer 4: 8-Agent Engineering Team */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-xl border-l-4 border-l-pink-500">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-pink-500/10 text-pink-400 flex items-center justify-center border border-pink-500/20">
                <FaRobot className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white font-sans">Specialized Multi-Agent System</h4>
                <p className="text-xs text-slate-400 font-sans">8 domain-specific agents executing structured prompt blueprints</p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {agents.map((agentName, idx) => (
                <div key={idx} className="p-2.5 bg-slate-900/90 border border-slate-800 rounded-lg text-center font-bold text-slate-200 text-xs hover:border-pink-500/40 transition">
                  {agentName} Agent
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-center text-slate-600">
            <FaArrowDown className="w-4 h-4 text-emerald-400" />
          </div>

          {/* Layer 5: Ollama + Local Models */}
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4 border-l-4 border-l-emerald-400">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
                <FaMicrochip className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white font-sans">Ollama Local Inference Engine</h4>
                <p className="text-xs text-slate-400 font-sans">Qwen 2.5 / Qwen 2.5 Coder (14B) running locally with zero data leaks</p>
              </div>
            </div>
            <span className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-emerald-400 text-[11px]">Local Private LLM</span>
          </div>
        </div>
      </div>
    </section>
  );
}
