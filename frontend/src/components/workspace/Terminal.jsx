import React, { useState, useRef, useEffect } from 'react';
import { FaTerminal, FaTrash, FaChevronUp, FaChevronDown, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

export default function Terminal({ outputText = '', isRunning = false, exitCode = 0, isOpen = true, onToggle }) {
  const [logs, setLogs] = useState(outputText ? outputText.split('\n') : []);
  const termEndRef = useRef(null);

  useEffect(() => {
    if (outputText) {
      setLogs(outputText.split('\n'));
    }
  }, [outputText]);

  useEffect(() => {
    if (isOpen && termEndRef.current) {
      termEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isOpen]);

  const handleClear = () => {
    setLogs([]);
  };

  return (
    <div className="bg-slate-950 border-t border-slate-800/80 font-mono text-xs text-slate-300 flex flex-col shrink-0 min-h-0 min-w-0 overflow-hidden h-full">
      {/* Header Bar */}
      <div className="px-3 py-1.5 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/80 font-sans text-xs select-none shrink-0 h-9">
        <div className="flex items-center gap-3">
          <button
            onClick={onToggle}
            className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-white hover:text-cyan-400 transition"
          >
            <FaTerminal className="text-cyan-400 w-3.5 h-3.5" /> Terminal
            {isOpen ? <FaChevronDown className="w-3 h-3 text-slate-500" /> : <FaChevronUp className="w-3 h-3 text-slate-500" />}
          </button>

          {exitCode === 0 ? (
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
              <FaCheckCircle className="w-2.5 h-2.5" /> Exit Code: 0
            </span>
          ) : (
            <span className="text-[10px] font-mono text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 flex items-center gap-1">
              <FaTimesCircle className="w-2.5 h-2.5" /> Exit Code: {exitCode}
            </span>
          )}
        </div>

        <button
          onClick={handleClear}
          className="px-2 py-0.5 bg-slate-950 hover:bg-slate-800 text-slate-400 hover:text-white rounded border border-slate-800 transition flex items-center gap-1 text-[10px]"
        >
          <FaTrash className="w-2.5 h-2.5" /> Clear
        </button>
      </div>

      {/* Terminal Lines Pane */}
      {isOpen && (
        <div className="p-3 flex-1 min-h-0 overflow-y-auto font-mono text-[11px] leading-relaxed space-y-1 bg-[#070b13] custom-scrollbar">
          {logs && logs.length > 0 ? (
            logs.map((line, idx) => (
              <div key={idx} className="text-slate-300">
                {line}
              </div>
            ))
          ) : (
            <div className="text-slate-600 italic">$ AIForge Terminal Ready... Click "Run" or "Test" to execute.</div>
          )}
          <div ref={termEndRef} />
        </div>
      )}
    </div>
  );
}
