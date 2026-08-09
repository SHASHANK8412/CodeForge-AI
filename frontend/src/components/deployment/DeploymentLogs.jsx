import React, { useRef, useEffect } from 'react';
import { FaTerminal, FaTrash } from 'react-icons/fa';

export default function DeploymentLogs({ logs = [] }) {
  const logEndRef = useRef(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 shadow-xl font-mono text-xs text-slate-300 flex flex-col h-[280px]">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center gap-2 text-slate-200 font-bold uppercase tracking-wider text-[11px] font-sans">
          <FaTerminal className="text-cyan-400 w-3.5 h-3.5" /> Deployment Output Log Stream
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1.5 pr-2 font-mono text-[11px] leading-relaxed">
        {logs && logs.length > 0 ? (
          logs.map((logLine, idx) => (
            <div key={idx} className="hover:bg-slate-900/50 p-1 rounded transition text-slate-300">
              {logLine}
            </div>
          ))
        ) : (
          <div className="text-slate-600 italic py-4">$ Deployment log stream ready...</div>
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
