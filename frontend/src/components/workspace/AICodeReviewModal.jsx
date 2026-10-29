import React from 'react';
import {
  FaCheckCircle,
  FaTimesCircle,
  FaTimes,
  FaShieldAlt,
  FaRobot,
  FaExclamationTriangle,
  FaFileCode,
  FaCheck,
  FaQuestionCircle
} from 'react-icons/fa';

export default function AICodeReviewModal({
  open = false,
  onClose = null,
  diffData = null,
  onAccept = null,
  onReject = null,
  onAskAI = null
}) {
  if (!open || !diffData) return null;

  const { file, before, after, diff, issue, lines_added = 12, lines_removed = 3, risk = 'LOW' } = diffData;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden font-sans flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 bg-[#070c18] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <FaShieldAlt className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">AI-Generated Code Change Review</h2>
              <p className="text-[10px] text-slate-400 font-mono">{file || 'Modified File'}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-900 transition cursor-pointer"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        {/* Change Metrics Banner */}
        <div className="px-5 py-3 border-b border-slate-800/80 bg-slate-950/80 flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            <span className="font-mono text-emerald-400 font-bold">+{lines_added} lines</span>
            <span className="font-mono text-rose-400 font-bold">-{lines_removed} lines</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
              risk === 'LOW' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
            }`}>
              Risk: {risk}
            </span>
          </div>

          <div className="text-[11px] text-slate-400 flex items-center gap-1">
            <FaCheckCircle className="text-emerald-400" /> Preserves Architecture
          </div>
        </div>

        {/* Diff Content Viewer */}
        <div className="p-5 overflow-y-auto max-h-[350px] bg-[#060911] font-mono text-xs text-slate-300">
          {diff ? (
            <pre className="whitespace-pre-wrap leading-relaxed">
              {diff.split('\n').map((line, idx) => {
                if (line.startsWith('+') && !line.startsWith('+++')) {
                  return <div key={idx} className="bg-emerald-950/50 text-emerald-300 px-2 py-0.5">{line}</div>;
                }
                if (line.startsWith('-') && !line.startsWith('---')) {
                  return <div key={idx} className="bg-rose-950/50 text-rose-300 px-2 py-0.5">{line}</div>;
                }
                return <div key={idx} className="text-slate-400 px-2">{line}</div>;
              })}
            </pre>
          ) : (
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                <div className="text-[10px] text-slate-500 font-bold mb-1">ORIGINAL</div>
                <pre className="whitespace-pre-wrap text-slate-400">{before || 'No previous content'}</pre>
              </div>
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                <div className="text-[10px] text-emerald-400 font-bold mb-1">SUGGESTED REPAIR</div>
                <pre className="whitespace-pre-wrap text-slate-200">{after || 'No new content'}</pre>
              </div>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div className="px-5 py-3 border-t border-slate-800 bg-[#070c18] flex items-center justify-between">
          <button
            onClick={() => onAskAI?.(file)}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 cursor-pointer transition border border-slate-800"
          >
            <FaQuestionCircle className="text-cyan-400" /> Ask AI About Change
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={onReject}
              className="px-3.5 py-1.5 bg-slate-900 hover:bg-rose-950 text-rose-400 hover:text-rose-300 rounded-lg text-xs font-bold transition cursor-pointer border border-rose-500/30"
            >
              Reject
            </button>
            <button
              onClick={onAccept}
              className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-lg"
            >
              <FaCheck className="w-3 h-3" /> Accept & Apply Patch
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
