import React from 'react';
import { FaCheckCircle, FaSpinner, FaClock, FaRocket } from 'react-icons/fa';

export default function DeploymentWorkflow({ workflow = [] }) {
  const defaultSteps = [
    { step: 1, name: 'Preparing project', status: 'COMPLETED' },
    { step: 2, name: 'Installing dependencies', status: 'COMPLETED' },
    { step: 3, name: 'Building application', status: 'COMPLETED' },
    { step: 4, name: 'Running final tests', status: 'COMPLETED' },
    { step: 5, name: 'Building Docker image', status: 'COMPLETED' },
    { step: 6, name: 'Deploying backend to Render', status: 'COMPLETED' },
    { step: 7, name: 'Deploying frontend to Vercel', status: 'COMPLETED' },
    { step: 8, name: 'Configuring PostgreSQL database', status: 'COMPLETED' },
    { step: 9, name: 'Running live health checks', status: 'COMPLETED' }
  ];

  const stepsList = workflow && workflow.length > 0 ? workflow : defaultSteps;

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-3 flex items-center gap-2">
        <FaRocket className="text-emerald-400" /> Production Deployment Event Tracker
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
        {stepsList.map((st) => {
          const isDone = st.status?.toUpperCase() === 'COMPLETED';
          const isRunning = st.status?.toUpperCase() === 'RUNNING';

          return (
            <div
              key={st.step}
              className={`p-3 rounded-xl border flex items-center gap-3 text-xs ${
                isRunning
                  ? 'bg-indigo-950/60 border-cyan-400 shadow-lg shadow-cyan-500/10'
                  : isDone
                  ? 'bg-slate-900 border-slate-800'
                  : 'bg-slate-950/60 border-slate-800/60 opacity-60'
              }`}
            >
              {isDone ? (
                <FaCheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              ) : isRunning ? (
                <FaSpinner className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />
              ) : (
                <FaClock className="w-4 h-4 text-slate-600 shrink-0" />
              )}
              <span className={`font-mono text-xs ${isDone ? 'text-slate-200' : isRunning ? 'text-cyan-300 font-bold' : 'text-slate-500'}`}>
                {st.step}. {st.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
