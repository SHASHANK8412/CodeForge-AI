import React from 'react';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';

export default function ProjectPagination({ page = 1, total = 1, pageSize = 12, onPageChange }) {
  const totalPages = Math.ceil(total / pageSize) || 1;

  if (totalPages <= 1) return null;

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className="flex items-center justify-between border-t border-slate-800/80 pt-4 font-sans text-xs select-none">
      <span className="text-slate-400 text-xs font-mono">
        Showing {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} of {total} projects
      </span>

      <div className="flex items-center gap-1.5 font-mono">
        <button
          onClick={() => page > 1 && onPageChange(page - 1)}
          disabled={page === 1}
          className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg transition disabled:opacity-40"
        >
          <FaChevronLeft className="w-3 h-3" />
        </button>

        {pages.map((p) => (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`w-8 h-8 rounded-lg border font-bold text-xs transition ${
              p === page
                ? 'bg-cyan-500 text-slate-950 border-cyan-400'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
            }`}
          >
            {p}
          </button>
        ))}

        <button
          onClick={() => page < totalPages && onPageChange(page + 1)}
          disabled={page === totalPages}
          className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-lg transition disabled:opacity-40"
        >
          <FaChevronRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}
