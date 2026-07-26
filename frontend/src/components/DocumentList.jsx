import React from 'react';
import { FaFileAlt, FaTrash, FaCheckCircle } from 'react-icons/fa';

export default function DocumentList({ documents = [], onDeleteDocument }) {
  const formatSize = (bytes) => {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 text-slate-100 shadow-xl">
      <h3 className="text-xs font-bold tracking-wide text-indigo-400 uppercase mb-4 flex items-center justify-between">
        <span>Uploaded Project Knowledge Base ({documents.length})</span>
      </h3>

      {documents.length === 0 ? (
        <div className="text-center py-6 text-slate-500 text-xs italic bg-slate-950/60 rounded-lg border border-slate-800">
          No documents uploaded yet. Upload PDF/TXT/MD files to index project knowledge.
        </div>
      ) : (
        <div className="space-y-2 max-h-60 overflow-y-auto pr-1 font-mono text-xs">
          {documents.map((doc) => (
            <div
              key={doc.filename}
              className="p-3 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between hover:border-slate-700 transition"
            >
              <div className="flex items-center gap-3 min-w-0">
                <FaFileAlt className="w-4 h-4 text-indigo-400 shrink-0" />
                <div className="min-w-0">
                  <div className="text-white font-medium truncate">{doc.filename}</div>
                  <div className="text-[10px] text-slate-500 flex items-center gap-2">
                    <span>{formatSize(doc.size_bytes)}</span>
                    <span>•</span>
                    <span>{doc.upload_time}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span className="text-[10px] text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800 flex items-center gap-1">
                  <FaCheckCircle className="w-2.5 h-2.5" /> Indexed
                </span>
                <button
                  onClick={() => onDeleteDocument(doc.filename)}
                  className="text-slate-500 hover:text-rose-400 transition p-1 cursor-pointer"
                  title="Delete Document"
                >
                  <FaTrash className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
