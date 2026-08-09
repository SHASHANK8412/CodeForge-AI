import React from 'react';
import { FaCheckCircle, FaCloud, FaDocker, FaServer, FaCogs } from 'react-icons/fa';

export default function ProviderSelector({ providers = [], selectedProvider, onSelectProvider }) {
  const getIcon = (id) => {
    switch (id) {
      case 'vercel': return <FaCloud className="text-cyan-400" />;
      case 'render': return <FaServer className="text-purple-400" />;
      case 'docker': return <FaDocker className="text-blue-400" />;
      default: return <FaCogs className="text-amber-400" />;
    }
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-3">
        Deployment Target Providers
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {providers.map((prov) => {
          const isSelected = selectedProvider === prov.id || prov.selected;
          return (
            <div
              key={prov.id}
              onClick={() => onSelectProvider && onSelectProvider(prov.id)}
              className={`p-4 rounded-xl border cursor-pointer transition select-none flex flex-col justify-between ${
                isSelected
                  ? 'bg-indigo-950/60 border-cyan-400 shadow-lg shadow-cyan-500/10'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-base">
                    {getIcon(prov.id)}
                  </div>
                  {isSelected && <FaCheckCircle className="text-cyan-400 w-4 h-4" />}
                </div>
                <h4 className="text-sm font-bold text-white mb-0.5">{prov.name}</h4>
                <div className="text-[11px] font-mono text-cyan-400">{prov.category}</div>
                <p className="text-xs text-slate-400 mt-1">{prov.stack}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
                <span className="text-[10px] font-mono text-emerald-400 font-bold">{prov.status}</span>
                <span className={`px-2 py-1 rounded text-[11px] font-bold ${isSelected ? 'bg-cyan-500 text-slate-950' : 'bg-slate-800 text-slate-300'}`}>
                  {isSelected ? 'Selected' : 'Select'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
