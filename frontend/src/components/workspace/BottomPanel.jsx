import React, { useMemo } from 'react';
import {
  FaTerminal,
  FaBug,
  FaVial,
  FaCodeBranch,
  FaTimes,
  FaPlay,
  FaExclamationTriangle,
  FaCheckCircle,
  FaFileAlt,
  FaHistory,
  FaWrench
} from 'react-icons/fa';

import AgentOrchestrationGraph from '../generation/AgentOrchestrationGraph';
import AIMissionProgress from '../generation/AIMissionProgress';

const TAB_CONFIG = [
  { id: 'terminal', label: 'Terminal', icon: FaTerminal },
  { id: 'tests', label: 'Tests', icon: FaVial },
  { id: 'problems', label: 'Problems', icon: FaBug },
  { id: 'changes', label: 'Changes', icon: FaCodeBranch },
  { id: 'graph', label: 'AI Agent Graph', icon: FaWrench },
  { id: 'mission', label: 'AI Mission', icon: FaFileAlt },
  { id: 'logs', label: 'Agent Timeline', icon: FaHistory },
];

export default function BottomPanel({
  activeTab = 'terminal',
  onTabChange,
  terminalOutput = '',
  onClearTerminal,
  problems = [],
  testResult = null,
  changes = [],
  timeline = [],
  onOpenProblem,
  onOpenDiff,
  onRunTests,
  onDebugWithAI
}) {
  const errorsCount = problems.filter((p) => p.severity === 'ERROR').length;
  const warningsCount = problems.filter((p) => p.severity === 'WARNING').length;

  return (
    <div className="bg-[#090d16] border-t border-slate-800/80 h-full flex flex-col min-h-0 select-none font-sans">
      {/* Tab Navigation Header */}
      <div className="flex items-center justify-between border-b border-slate-800/70 bg-slate-950 px-3 py-1.5 text-[11px] font-mono text-slate-300 shrink-0">
        <div className="flex items-center gap-1.5">
          {TAB_CONFIG.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            let badge = null;
            if (tab.id === 'problems' && problems.length > 0) {
              badge = (
                <span className={`ml-1 px-1.5 py-0.2 rounded-full text-[9px] font-bold ${errorsCount > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>
                  {problems.length}
                </span>
              );
            } else if (tab.id === 'changes' && changes.length > 0) {
              badge = (
                <span className="ml-1 px-1.5 py-0.2 rounded-full text-[9px] font-bold bg-cyan-500/20 text-cyan-400">
                  {changes.length}
                </span>
              );
            } else if (tab.id === 'tests' && testResult) {
              badge = (
                <span className={`ml-1 px-1.5 py-0.2 rounded-full text-[9px] font-bold ${testResult.failed > 0 ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                  {testResult.passed}/{testResult.total}
                </span>
              );
            }

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition cursor-pointer ${
                  isActive
                    ? 'bg-slate-900 text-cyan-300 font-bold border border-slate-700'
                    : 'text-slate-500 hover:text-slate-200 hover:bg-slate-900/50'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{tab.label}</span>
                {badge}
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'terminal' && (
            <button
              onClick={onClearTerminal}
              className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white text-[10px] cursor-pointer"
            >
              <FaTimes className="w-2.5 h-2.5" /> Clear
            </button>
          )}
          {activeTab === 'tests' && (
            <button
              onClick={onRunTests}
              className="flex items-center gap-1 px-2.5 py-0.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-semibold cursor-pointer"
            >
              <FaPlay className="w-2 h-2" /> Re-run Tests
            </button>
          )}
        </div>
      </div>

      {/* Tab Panels */}
      <div className="flex-1 overflow-hidden min-h-0 bg-[#070b14]">
        {/* 1. Terminal Panel */}
        {activeTab === 'terminal' && (
          <div className="h-full overflow-y-auto custom-scrollbar p-3 font-mono text-xs text-slate-200 leading-relaxed">
            {terminalOutput ? (
              terminalOutput.split('\n').map((line, idx) => (
                <div key={idx} className="whitespace-pre-wrap">
                  {line}
                </div>
              ))
            ) : (
              <div className="text-slate-500 italic">No command output available. Run tests or preview project to view console logs.</div>
            )}
          </div>
        )}

        {/* 2. Tests Panel */}
        {activeTab === 'tests' && (
          <div className="h-full overflow-y-auto custom-scrollbar p-3 space-y-3">
            {testResult ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${testResult.failed > 0 ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                      {testResult.failed > 0 ? <FaExclamationTriangle className="w-5 h-5" /> : <FaCheckCircle className="w-5 h-5" />}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">
                        {testResult.passed} / {testResult.total} Tests Passed ({testResult.failed} failed)
                      </div>
                      <div className="text-[11px] text-slate-400">Duration: {testResult.duration || 0.42}s</div>
                    </div>
                  </div>

                  {testResult.failed > 0 && (
                    <button
                      onClick={onDebugWithAI}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold shadow-lg transition cursor-pointer"
                    >
                      <FaWrench className="w-3 h-3" /> Debug with AI
                    </button>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                  <div className="font-semibold text-slate-100 mb-2">Test Runner Output</div>
                  <pre className="whitespace-pre-wrap leading-5">{testResult.output || 'Test execution completed.'}</pre>
                </div>
              </div>
            ) : (
              <div className="text-slate-500 text-xs italic">Test results not available. Click 'Re-run Tests' above.</div>
            )}
          </div>
        )}

        {/* 3. Problems Panel */}
        {activeTab === 'problems' && (
          <div className="h-full overflow-y-auto custom-scrollbar p-3 space-y-2">
            {problems.length === 0 ? (
              <div className="text-slate-500 text-xs italic">No syntax or lint problems detected in project.</div>
            ) : (
              problems.map((prob, idx) => (
                <button
                  key={idx}
                  onClick={() => onOpenProblem?.(prob)}
                  className="w-full text-left p-2.5 bg-slate-950 border border-slate-800 rounded-xl hover:border-cyan-500/40 transition flex items-center justify-between gap-3 cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${
                      prob.severity === 'ERROR' ? 'bg-rose-500/15 text-rose-400' : prob.severity === 'WARNING' ? 'bg-amber-500/15 text-amber-400' : 'bg-cyan-500/15 text-cyan-400'
                    }`}>
                      {prob.severity}
                    </span>
                    <span className="text-xs text-slate-200 font-sans">{prob.message}</span>
                  </div>
                  <span className="font-mono text-[10px] text-slate-500 shrink-0">
                    {prob.file}:{prob.line || 1}
                  </span>
                </button>
              ))
            )}
          </div>
        )}

        {/* 4. Changes Panel */}
        {activeTab === 'changes' && (
          <div className="h-full overflow-y-auto custom-scrollbar p-3 space-y-2">
            {changes.length === 0 ? (
              <div className="text-slate-500 text-xs italic">No uncommitted or snapshot file modifications. Working tree clean.</div>
            ) : (
              changes.map((ch, idx) => (
                <div
                  key={idx}
                  onClick={() => onOpenDiff?.(ch)}
                  className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between hover:border-cyan-500/40 transition cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                      ch.status === 'ADDED' ? 'bg-emerald-500/15 text-emerald-400' : ch.status === 'DELETED' ? 'bg-rose-500/15 text-rose-400' : 'bg-amber-500/15 text-amber-400'
                    }`}>
                      {ch.status === 'ADDED' ? 'A' : ch.status === 'DELETED' ? 'D' : 'M'}
                    </span>
                    <span className="font-mono text-xs text-slate-200">{ch.path}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">View Diff →</span>
                </div>
              ))
            )}
          </div>
        )}

        {/* 5. AI Agent Orchestration Graph Panel */}
        {activeTab === 'graph' && (
          <div className="h-full overflow-y-auto custom-scrollbar p-3">
            <AgentOrchestrationGraph />
          </div>
        )}

        {/* 6. AI Mission Progress Panel */}
        {activeTab === 'mission' && (
          <div className="h-full overflow-y-auto custom-scrollbar p-3">
            <AIMissionProgress />
          </div>
        )}

        {/* 7. Agent Timeline Panel */}
        {activeTab === 'logs' && (
          <div className="h-full overflow-y-auto custom-scrollbar p-3 space-y-2 font-mono text-[11px]">
            {timeline.length === 0 ? (
              <div className="text-slate-500 text-xs italic">No timeline events recorded.</div>
            ) : (
              timeline.map((ev, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2 rounded-lg bg-slate-950/60 border border-slate-900 text-slate-300">
                  <span className="text-slate-500 text-[10px] shrink-0">{ev.timestamp || '00:00:00'}</span>
                  <span className="px-1.5 py-0.5 rounded bg-slate-900 text-cyan-400 uppercase text-[9px] font-bold shrink-0">
                    {ev.agent || 'SYSTEM'}
                  </span>
                  <span className="text-slate-200 truncate">{ev.message || ev.event_type}</span>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
