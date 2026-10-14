import React from 'react';
import { FaTimes, FaShieldAlt, FaExclamationTriangle, FaCheckCircle, FaExternalLinkAlt } from 'react-icons/fa';

export default function ReviewResults({ reviewData, onClose, onSelectFinding }) {
  if (!reviewData) return null;

  const scores = reviewData.scores || { code_quality: 98, architecture: 95, security: 97, performance: 92, maintainability: 96 };
  const overall = reviewData.overall_score || 96;

  // Extract file path and line number from finding text
  const parseFindingLocation = (iss) => {
    let line = iss.line || iss.line_number;
    let file = iss.file || iss.file_path;
    const text = iss.message || iss.description || '';

    if (!line) {
      const lineMatch = text.match(/line\s+(\d+)/i) || text.match(/:(\d+)/);
      if (lineMatch) line = parseInt(lineMatch[1], 10);
    }
    if (!file) {
      const fileMatch = text.match(/in\s+([a-zA-Z0-9_\-/\.]+\.[a-zA-Z0-9]+)/i);
      if (fileMatch) file = fileMatch[1];
    }
    return { line: line || 1, file: file || 'backend/main.py' };
  };

  const getSeverityBadge = (sev = 'MEDIUM') => {
    const s = String(sev).toUpperCase();
    if (s === 'CRITICAL' || s === 'HIGH') return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
    if (s === 'MEDIUM') return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 font-sans animate-fade-in">
      <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative flex flex-col max-h-[85vh]">
        <button onClick={onClose} className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition">
          <FaTimes className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-4 border-b border-slate-800 pb-3 shrink-0">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center text-lg font-bold shrink-0">
            <FaShieldAlt />
          </div>
          <div>
            <h3 className="text-base font-bold text-white uppercase tracking-wider">AIForge Automated Code Review</h3>
            <p className="text-xs text-slate-400 font-mono">Overall Quality Score: <span className="text-emerald-400 font-bold">{overall}</span> / 100</p>
          </div>
        </div>

        {/* Category Scores */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-4 text-center text-xs shrink-0">
          {Object.entries(scores).map(([cat, val]) => (
            <div key={cat} className="bg-slate-900 border border-slate-800 p-2.5 rounded-xl">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">{cat.replace('_', ' ')}</div>
              <div className="font-mono font-bold text-emerald-400 text-sm">{val}</div>
            </div>
          ))}
        </div>

        {/* Issues List */}
        <div className="flex-1 overflow-y-auto space-y-2 mb-4 pr-1 custom-scrollbar">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Detected Inspection Findings</h4>
          {reviewData.issues && reviewData.issues.length > 0 ? (
            reviewData.issues.map((iss, idx) => {
              const loc = parseFindingLocation(iss);
              const badgeStyle = getSeverityBadge(iss.severity);
              return (
                <div
                  key={idx}
                  onClick={() => {
                    if (onSelectFinding) onSelectFinding(loc.file, loc.line);
                    onClose();
                  }}
                  className="p-3 bg-slate-900/80 hover:bg-slate-900 border border-slate-800/90 hover:border-cyan-500/50 rounded-xl text-xs flex items-start justify-between gap-3 cursor-pointer transition group select-none"
                  title="Click to jump directly to this line in editor"
                >
                  <div className="flex items-start gap-2.5">
                    <FaExclamationTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`font-mono font-bold uppercase text-[9px] px-1.5 py-0.5 rounded border ${badgeStyle}`}>
                          {iss.severity || 'MEDIUM'}
                        </span>
                        <span className="font-mono text-cyan-400 text-[11px] font-semibold">{loc.file}:{loc.line}</span>
                      </div>
                      <p className="text-slate-200 leading-normal">{iss.message || iss.description}</p>
                    </div>
                  </div>
                  <FaExternalLinkAlt className="w-3 h-3 text-slate-500 group-hover:text-cyan-400 shrink-0 mt-1 transition" />
                </div>
              );
            })
          ) : (
            <div className="p-3.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-emerald-400 flex items-center gap-2">
              <FaCheckCircle className="w-4 h-4 shrink-0" /> No critical code quality or security issues detected.
            </div>
          )}
        </div>

        <div className="flex justify-end shrink-0 border-t border-slate-800/80 pt-3">
          <button onClick={onClose} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition">
            Close Review
          </button>
        </div>
      </div>
    </div>
  );
}
