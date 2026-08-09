import React, { useState, useRef, useEffect } from 'react';
import { FaTerminal, FaTrash, FaPause, FaPlay } from 'react-icons/fa';

export default function AgentLogs({ logs = [] }) {
  const [logList, setLogList] = useState(logs);
  const [autoScroll, setAutoScroll] = useState(true);
  const logEndRef = useRef(null);

  useEffect(() => {
    setLogList(logs);
  }, [logs]);

  useEffect(() => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logList, autoScroll]);

  const handleClear = () => {
    setLogList([]);
  };

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-5 shadow-xl font-mono text-xs text-slate-300 flex flex-col h-[320px]">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center gap-2 text-slate-200 font-bold uppercase tracking-wider text-[11px]">
          <FaTerminal className="text-cyan-400 w-3.5 h-3.5" /> Agent Activity Stream
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-2.5 py-1 rounded text-[11px] font-sans flex items-center gap-1 border transition ${
              autoScroll ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300' : 'bg-slate-900 border-slate-800 text-slate-400'
            }`}
          >
            {autoScroll ? <FaPause className="w-2.5 h-2.5" /> : <FaPlay className="w-2.5 h-2.5" />}
            <span>{autoScroll ? 'Pause Auto-scroll' : 'Resume Auto-scroll'}</span>
          </button>

          <button
            onClick={handleClear}
            className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white rounded text-[11px] font-sans flex items-center gap-1 transition"
          >
            <FaTrash className="w-2.5 h-2.5" /> Clear Logs
          </button>
        </div>
      </div>

      {/* Terminal Output Window */}
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-2 font-mono text-[11px] leading-relaxed">
        {logList && logList.length > 0 ? (
          logList.map((logLine, idx) => (
            <div key={idx} className="hover:bg-slate-900/50 p-1 rounded transition text-slate-300">
              {logLine}
            </div>
          ))
        ) : (
          <div className="text-slate-600 italic py-4">No active logs recorded yet...</div>
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
