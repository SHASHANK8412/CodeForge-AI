import React from 'react';
import { FaLayerGroup, FaArrowLeft, FaCode, FaShieldAlt, FaRocket, FaCheckCircle } from 'react-icons/fa';

export default function DeploymentHeader({
  projectName = 'FoodDelivery AI',
  generationId = 'aiforge-demo',
  onNavigate
}) {
  const pipeline = [
    { name: 'Idea', done: true },
    { name: 'Planning', done: true },
    { name: 'Development', done: true },
    { name: 'Review', done: true },
    { name: 'Testing', done: true },
    { name: 'Quality', done: true },
    { name: 'Deployment', active: true },
    { name: 'Live Application', done: false }
  ];

  return (
    <header className="bg-[#090d16] border-b border-slate-800/80 px-4 sm:px-6 py-3 font-sans shrink-0 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand & Title */}
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <FaLayerGroup className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-extrabold text-white tracking-tight">{projectName}</h2>
              <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">
                <FaCheckCircle className="w-2.5 h-2.5" /> Quality Passed
              </span>
            </div>
            <div className="text-[11px] font-mono text-slate-400">Deployment Center • ID: {generationId}</div>
          </div>
        </div>

        {/* Center Stage Navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate && onNavigate('build')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition"
          >
            <FaArrowLeft className="w-3 h-3 text-cyan-400" /> Build
          </button>

          <button
            onClick={() => onNavigate && onNavigate('code')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition"
          >
            <FaCode className="w-3 h-3 text-emerald-400" /> Code Workspace
          </button>

          <button
            onClick={() => onNavigate && onNavigate('metrics')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition"
          >
            <FaShieldAlt className="w-3 h-3 text-amber-400" /> Quality Center
          </button>

          <button
            onClick={() => onNavigate && onNavigate('plugins')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-indigo-600/20"
          >
            <FaRocket className="w-3 h-3" /> Deployment Center
          </button>
        </div>
      </div>

      {/* Top Workflow Stage Pipeline Bar */}
      <div className="max-w-7xl mx-auto mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono overflow-x-auto">
        {pipeline.map((p, idx) => (
          <React.Fragment key={idx}>
            <span
              className={`flex items-center gap-1 shrink-0 ${
                p.active
                  ? 'text-cyan-400 font-bold bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20'
                  : p.done
                  ? 'text-emerald-400'
                  : 'text-slate-500'
              }`}
            >
              {p.done && <FaCheckCircle className="w-2.5 h-2.5" />}
              {p.name}
            </span>
            {idx < pipeline.length - 1 && <span className="text-slate-700">→</span>}
          </React.Fragment>
        ))}
      </div>
    </header>
  );
}
