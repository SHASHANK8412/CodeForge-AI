import React, { useState } from 'react';
import {
  FaBug,
  FaWrench,
  FaRedo,
  FaExclamationTriangle,
  FaCheckCircle,
  FaTerminal,
  FaFileCode,
  FaChevronDown,
  FaChevronUp,
  FaLightbulb,
  FaHistory,
  FaUserShield,
  FaPaperPlane,
} from 'react-icons/fa';

export default function DebugActivityPanel({
  active = false,
  debugState = {},
  testResults = {},
  currentCycle = 1,
  maxCycles = 3,
  humanInterventionRequired = false,
  onProvideGuidance,
  onRetry,
  onProceedAnyway,
}) {
  const [showStackTrace, setShowStackTrace] = useState(false);
  const [showFixHistory, setShowFixHistory] = useState(false);
  const [guidanceInput, setGuidanceInput] = useState('');
  const [isSubmittingGuidance, setIsSubmittingGuidance] = useState(false);

  if (!active && !humanInterventionRequired && !debugState?.error_category && !testResults?.failure_category) {
    return null;
  }

  const category =
    debugState?.error_category ||
    testResults?.failure_category ||
    'TEST_ASSERTION_ERROR';

  const categoryColors = {
    IMPORT_ERROR: 'bg-indigo-900/60 text-indigo-300 border-indigo-500/40',
    SYNTAX_ERROR: 'bg-rose-900/60 text-rose-300 border-rose-500/40',
    TYPE_ERROR: 'bg-purple-900/60 text-purple-300 border-purple-500/40',
    RUNTIME_ERROR: 'bg-amber-900/60 text-amber-300 border-amber-500/40',
    TEST_ASSERTION_ERROR: 'bg-rose-950/80 text-rose-200 border-rose-600/50',
    DEPENDENCY_ERROR: 'bg-orange-900/60 text-orange-300 border-orange-500/40',
    CONFIGURATION_ERROR: 'bg-yellow-900/60 text-yellow-300 border-yellow-500/40',
    DATABASE_ERROR: 'bg-red-900/60 text-red-300 border-red-500/40',
    API_ERROR: 'bg-cyan-900/60 text-cyan-300 border-cyan-500/40',
    FRONTEND_BUILD_ERROR: 'bg-emerald-900/60 text-emerald-300 border-emerald-500/40',
    BACKEND_ERROR: 'bg-rose-900/60 text-rose-300 border-rose-500/40',
    UNKNOWN_ERROR: 'bg-slate-900/60 text-slate-300 border-slate-700/50',
  };

  const badgeStyle = categoryColors[category] || categoryColors.UNKNOWN_ERROR;
  const rootCause = debugState?.diagnostic_result?.root_cause || debugState?.debug_analysis || 'Analyzing failure cause...';
  const modifiedFiles = debugState?.files_modified || (debugState?.proposed_fix?.files_to_modify) || [];
  const stackTraces = testResults?.stack_traces || debugState?.stack_traces || [];
  const failedTests = testResults?.failed_tests || debugState?.failed_tests || [];
  const fixHistory = debugState?.fix_history || [];

  const handleSendGuidance = (e) => {
    e.preventDefault();
    if (!guidanceInput.trim()) return;
    setIsSubmittingGuidance(true);
    if (onProvideGuidance) {
      onProvideGuidance(guidanceInput);
    }
    setGuidanceInput('');
    setIsSubmittingGuidance(false);
  };

  return (
    <div className="bg-slate-900/90 border border-slate-700/70 backdrop-blur-xl rounded-2xl p-5 mb-6 text-slate-200 shadow-2xl transition-all">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            {humanInterventionRequired ? (
              <FaUserShield className="w-5 h-5 text-rose-400 animate-pulse" />
            ) : (
              <FaBug className="w-4 h-4 animate-bounce" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white tracking-wide">
                {humanInterventionRequired
                  ? 'HUMAN GUIDANCE REQUIRED'
                  : 'AUTONOMOUS DEBUG → FIX → RETEST LOOP'}
              </span>
              <span className={`px-2.5 py-0.5 text-[10px] font-mono font-bold uppercase rounded-full border ${badgeStyle}`}>
                {category}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {humanInterventionRequired
                ? `AIForge attempted ${maxCycles} fixes without test passage. Human review required.`
                : `Cycle ${currentCycle} of ${maxCycles} in progress`}
            </p>
          </div>
        </div>

        {/* Cycle Progress Tracker */}
        <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Debug Cycles:</span>
          <div className="flex gap-1">
            {Array.from({ length: maxCycles }).map((_, idx) => {
              const cycleNum = idx + 1;
              const isDone = cycleNum < currentCycle;
              const isCurrent = cycleNum === currentCycle;
              return (
                <div
                  key={idx}
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono font-bold transition-all ${
                    isDone
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50'
                      : isCurrent
                      ? 'bg-amber-500 text-slate-950 font-extrabold ring-2 ring-amber-400/40 animate-pulse'
                      : 'bg-slate-800 text-slate-500 border border-slate-700'
                  }`}
                >
                  {cycleNum}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Human Escalation Alert */}
      {humanInterventionRequired && (
        <div className="bg-rose-950/40 border border-rose-500/50 rounded-xl p-4 mb-4 text-rose-200">
          <div className="flex items-start gap-3">
            <FaExclamationTriangle className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-bold text-sm text-white">Maximum Autonomous Cycles Reached</h4>
              <p className="text-xs text-rose-300/90 mt-1 leading-relaxed">
                AIForge has performed {maxCycles} automated fix attempts, but the test suite is still reporting failures. You can provide steering instructions, review stack traces, or retry with fresh guidance.
              </p>
            </div>
          </div>

          {/* User Guidance Input Form */}
          <form onSubmit={handleSendGuidance} className="mt-3 flex gap-2">
            <input
              type="text"
              value={guidanceInput}
              onChange={(e) => setGuidanceInput(e.target.value)}
              placeholder="e.g. 'Use SQLite in-memory database instead of PostgreSQL for unit tests'"
              className="flex-1 bg-slate-950 border border-rose-500/40 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-400"
            />
            <button
              type="submit"
              disabled={isSubmittingGuidance || !guidanceInput.trim()}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-lg"
            >
              <FaPaperPlane className="w-3 h-3" /> Provide Guidance
            </button>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium flex items-center gap-1 transition-all border border-slate-700"
              >
                <FaRedo className="w-3 h-3 text-amber-400" /> Retry
              </button>
            )}
            {onProceedAnyway && (
              <button
                type="button"
                onClick={onProceedAnyway}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition-all border border-slate-700"
              >
                Proceed Anyway
              </button>
            )}
          </form>
        </div>
      )}

      {/* Grid: Diagnosis & Targeted Fix */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 text-xs">
        {/* Left: Root Cause & Failed Tests */}
        <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 font-bold text-amber-400 mb-1.5 uppercase tracking-wider text-[11px]">
              <FaLightbulb className="w-3.5 h-3.5" /> Root Cause Diagnosis
            </div>
            <p className="text-slate-300 leading-relaxed font-mono text-[11px] bg-slate-900/80 p-2 rounded border border-slate-800">
              {rootCause}
            </p>
          </div>

          {failedTests.length > 0 && (
            <div className="mt-3">
              <span className="text-[10px] text-slate-400 uppercase font-semibold">Failed Test Cases:</span>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {failedTests.map((t, i) => (
                  <span key={i} className="px-2 py-0.5 bg-rose-950/60 text-rose-300 border border-rose-800/40 rounded font-mono text-[10px]">
                    {typeof t === 'string' ? t.split('::').pop() : t?.test_name || 'test_failure'}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Targeted Patch Manifest */}
        <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-1.5 font-bold text-cyan-400 mb-1.5 uppercase tracking-wider text-[11px]">
              <FaFileCode className="w-3.5 h-3.5" /> Targeted Modifications
            </div>
            <div className="space-y-1.5">
              {modifiedFiles.length > 0 ? (
                modifiedFiles.map((file, i) => (
                  <div key={i} className="flex items-center gap-2 bg-slate-900/80 px-2.5 py-1.5 rounded border border-slate-800 font-mono text-[11px] text-cyan-200">
                    <FaCheckCircle className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                    <span className="truncate">{file}</span>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 italic text-[11px]">Identifying affected source files...</p>
              )}
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-900">
            <span>Strategy: Minimal surgical patch</span>
            <span className="text-emerald-400 font-medium">Safe Rollback Enabled</span>
          </div>
        </div>
      </div>

      {/* Collapsible Stack Trace & History */}
      <div className="space-y-2">
        {stackTraces.length > 0 && (
          <div className="border border-slate-800 rounded-xl overflow-hidden">
            <button
              onClick={() => setShowStackTrace(!showStackTrace)}
              className="w-full flex items-center justify-between px-3 py-2 bg-slate-950 hover:bg-slate-800/50 text-[11px] font-mono text-slate-400 transition-colors"
            >
              <span className="flex items-center gap-1.5">
                <FaTerminal className="w-3 h-3 text-rose-400" /> Stack Trace / Failure Evidence ({stackTraces.length})
              </span>
              {showStackTrace ? <FaChevronUp className="w-3 h-3" /> : <FaChevronDown className="w-3 h-3" />}
            </button>
            {showStackTrace && (
              <div className="p-3 bg-black/80 font-mono text-[11px] text-rose-300 max-h-48 overflow-y-auto space-y-2 border-t border-slate-900">
                {stackTraces.map((trace, idx) => (
                  <pre key={idx} className="whitespace-pre-wrap leading-relaxed">{trace}</pre>
                ))}
              </div>
            )}
          </div>
        )}

        {fixHistory.length > 0 && (
          <div className="border border-slate-800 rounded-xl overflow-hidden">
            <button
              onClick={() => setShowFixHistory(!showFixHistory)}
              className="w-full flex items-center justify-between px-3 py-2 bg-slate-950 hover:bg-slate-800/50 text-[11px] font-mono text-slate-400 transition-colors"
            >
              <span className="flex items-center gap-1.5">
                <FaHistory className="w-3 h-3 text-amber-400" /> Applied Fix History ({fixHistory.length})
              </span>
              {showFixHistory ? <FaChevronUp className="w-3 h-3" /> : <FaChevronDown className="w-3 h-3" />}
            </button>
            {showFixHistory && (
              <div className="p-3 bg-slate-950 font-mono text-[11px] text-slate-300 max-h-40 overflow-y-auto space-y-2 border-t border-slate-900">
                {fixHistory.map((item, idx) => (
                  <div key={idx} className="bg-slate-900 p-2 rounded border border-slate-800">
                    <div className="flex justify-between text-slate-400 text-[10px] mb-1">
                      <span>Cycle #{item.cycle || idx + 1}</span>
                      <span>{item.category || 'Patch'}</span>
                    </div>
                    <p className="text-white font-medium">{item.root_cause || 'Bug fix'}</p>
                    <p className="text-slate-400 text-[10px] mt-0.5">Files: {item.files_modified?.join(', ')}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
