import React, { useEffect, useMemo, useState } from 'react';

export default function SearchPanel({ open, onClose, files = [], onResultSelect }) {
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (open) {
      setQuery('');
    }
  }, [open]);

  const results = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return [];
    const matches = [];
    files.forEach((file) => {
      const lines = String(file.content || '').split('\n');
      lines.forEach((line, index) => {
        if (line.toLowerCase().includes(normalized)) {
          matches.push({
            file,
            lineNumber: index + 1,
            snippet: line.trim(),
          });
        }
      });
    });
    return matches.slice(0, 80);
  }, [files, query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center p-4">
      <div className="mt-16 w-full max-w-4xl bg-slate-950 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-800 bg-[#050a14]">
          <div className="text-slate-200 text-sm font-semibold">Global Search</div>
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across project files..."
            className="mt-3 w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 outline-none"
          />
        </div>
        <div className="max-h-[60vh] overflow-y-auto custom-scrollbar p-4">
          {!query.trim() ? (
            <div className="text-slate-500 italic">Type to search project files by content and filename.</div>
          ) : results.length === 0 ? (
            <div className="text-slate-500 italic">No matches found.</div>
          ) : (
            <div className="space-y-3">
              {results.map((result, idx) => (
                <button
                  key={`${result.file.path}-${result.lineNumber}-${idx}`}
                  onClick={() => onResultSelect(result.file, result.lineNumber)}
                  className="w-full text-left p-4 bg-slate-900 border border-slate-800 rounded-2xl hover:border-cyan-500/50 transition"
                >
                  <div className="flex items-center justify-between gap-2 mb-1 text-slate-300">
                    <span className="font-semibold">{result.file.path}</span>
                    <span className="text-[11px] text-slate-500">Line {result.lineNumber}</span>
                  </div>
                  <div className="text-[12px] text-slate-400 leading-snug">{result.snippet}</div>
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="px-5 py-3 border-t border-slate-800 text-[11px] text-slate-500 text-right">
          Press Esc to close.
        </div>
      </div>
    </div>
  );
}
