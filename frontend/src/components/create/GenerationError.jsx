import React from 'react';
import { FaExclamationTriangle, FaRedo } from 'react-icons/fa';

export default function GenerationError({ message, onRetry }) {
  if (!message) return null;

  return (
    <div className="bg-rose-950/60 border border-rose-800 rounded-2xl p-5 mb-6 text-rose-200 font-sans shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-rose-900/80 text-rose-300 flex items-center justify-center shrink-0 border border-rose-700">
          <FaExclamationTriangle className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-white">Generation Failed</h4>
          <p className="text-xs text-rose-300 mt-0.5">{message}</p>
        </div>
      </div>

      <button
        type="button"
        onClick={onRetry}
        className="px-4 py-2 text-xs font-bold text-white bg-rose-800 hover:bg-rose-700 border border-rose-600 rounded-lg flex items-center gap-2 transition shrink-0"
      >
        <FaRedo className="w-3 h-3" />
        <span>Try Again</span>
      </button>
    </div>
  );
}
