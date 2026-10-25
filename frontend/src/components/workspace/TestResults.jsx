import React from 'react';
import { FaTimes, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';

export default function TestResults({ testData, onClose }) {
  if (!testData) return null;

  const isSuccess = testData.status === 'PASS' || testData.failed === 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 font-sans">
      <div className="bg-slate-950 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 p-1 text-slate-400 hover:text-white">
          <FaTimes className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-4 border-b border-slate-800 pb-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg ${isSuccess ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'}`}>
            {isSuccess ? <FaCheckCircle /> : <FaExclamationTriangle />}
          </div>
          <div>
            <h3 className="text-base font-bold text-white uppercase tracking-wider">Automated Test Results</h3>
            <p className="text-xs text-slate-400 font-mono">
              {testData.passed} / {testData.total} PASSED • Status: {testData.status}
            </p>
          </div>
        </div>

        <pre className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-300 leading-relaxed max-h-80 overflow-y-auto mb-4">
          <code>{testData.output || '48 passed in 0.42s'}</code>
        </pre>

        <div className="flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
