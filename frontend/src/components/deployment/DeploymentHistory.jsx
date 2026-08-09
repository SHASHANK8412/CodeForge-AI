import React from 'react';
import { FaHistory, FaCheckCircle } from 'react-icons/fa';

export default function DeploymentHistory({ history = [] }) {
  const defaultHistory = [
    { version: 'v3', environment: 'Production', status: 'LIVE', timestamp: new Date().toLocaleTimeString(), provider: 'Vercel + Render', commit_id: 'c703c42' },
    { version: 'v2', environment: 'Staging', status: 'LIVE', timestamp: 'Aug 9, 11:20', provider: 'Docker', commit_id: '544c073' },
    { version: 'v1', environment: 'Development', status: 'LIVE', timestamp: 'Aug 9, 09:15', provider: 'Render', commit_id: '9dfa75d' }
  ];

  const items = history && history.length > 0 ? history : defaultHistory;

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-3 flex items-center gap-2">
        <FaHistory className="text-cyan-400" /> Deployment History Audit Log
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-sans">
          <thead>
            <tr className="border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase">
              <th className="pb-2">Version</th>
              <th className="pb-2">Environment</th>
              <th className="pb-2">Provider</th>
              <th className="pb-2">Commit</th>
              <th className="pb-2">Status</th>
              <th className="pb-2 text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {items.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-900/50">
                <td className="py-3 font-bold text-cyan-400">{row.version}</td>
                <td className="py-3 text-slate-300 font-sans">{row.environment}</td>
                <td className="py-3 text-slate-300 font-sans">{row.provider}</td>
                <td className="py-3 text-slate-400 text-[11px]">{row.commit_id}</td>
                <td className="py-3">
                  <span className="text-emerald-400 text-[10px] font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1 w-fit">
                    <FaCheckCircle className="w-2.5 h-2.5" /> {row.status}
                  </span>
                </td>
                <td className="py-3 text-right text-slate-400 text-[11px]">{row.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
