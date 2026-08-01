import React from 'react';
import { FaCheckCircle, FaSpinner, FaBrain, FaBuilding, FaCode, FaCog, FaVial, FaFileAlt } from 'react-icons/fa';

export default function AgentTimeline({ currentStage = 'COMPLETED', activeIntent = 'PROJECT_GENERATION' }) {
  const isCoding = activeIntent === 'CODING';
  const isExplanation = activeIntent === 'EXPLANATION';

  const steps = isCoding
    ? [
        { id: 1, name: 'Intent Classifier', icon: <FaBrain />, status: 'COMPLETED', note: 'Intent: CODING (DSA Algorithm)' },
        { id: 2, name: 'Coding Agent', icon: <FaCode />, status: 'COMPLETED', note: 'Single-file solution & Time/Space complexity O(log n)' },
        { id: 3, name: 'Output Verification', icon: <FaCheckCircle />, status: 'COMPLETED', note: 'Clean syntax & examples validated' }
      ]
    : isExplanation
    ? [
        { id: 1, name: 'Intent Classifier', icon: <FaBrain />, status: 'COMPLETED', note: 'Intent: EXPLANATION (Technical Concept)' },
        { id: 2, name: 'Explanation Agent', icon: <FaBrain />, status: 'COMPLETED', note: 'Conceptual breakdown & architecture callouts' },
        { id: 3, name: 'Output Verification', icon: <FaCheckCircle />, status: 'COMPLETED', note: 'Markdown structure validated' }
      ]
    : [
        { id: 1, name: 'Planner Agent', icon: <FaBrain />, status: 'COMPLETED', note: 'Requirement & task decomposition' },
        { id: 2, name: 'Architect Agent', icon: <FaBuilding />, status: 'COMPLETED', note: 'System architecture & tech stack' },
        { id: 3, name: 'Frontend Agent', icon: <FaCode />, status: 'COMPLETED', note: 'React 18 UI components' },
        { id: 4, name: 'Backend Agent', icon: <FaCog />, status: 'COMPLETED', note: 'FastAPI async microservices' },
        { id: 5, name: 'Testing Agent', icon: <FaVial />, status: 'COMPLETED', note: 'PyTest & unit test suites' },
        { id: 6, name: 'Documentation Agent', icon: <FaFileAlt />, status: 'COMPLETED', note: 'README & SRS specifications' }
      ];

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-4 font-mono text-xs text-slate-200">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800 mb-3">
        <span className="font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <FaBrain className="text-indigo-400" /> AI Multi-Agent Execution Pipeline
        </span>
        <span className="text-[10px] bg-indigo-950 text-indigo-400 border border-indigo-800 px-2 py-0.5 rounded font-bold">
          Intent: {activeIntent}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {steps.map((step) => (
          <div
            key={step.id}
            className="p-2.5 rounded-lg border bg-slate-900 border-slate-800 flex items-start gap-2.5"
          >
            <div className="text-emerald-400 text-sm mt-0.5">{step.icon}</div>
            <div>
              <div className="font-bold text-white text-[11px] flex items-center gap-1.5">
                {step.name}
                <FaCheckCircle className="text-emerald-400 text-[10px]" />
              </div>
              <div className="text-[10px] text-slate-400 leading-tight mt-0.5">{step.note}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
