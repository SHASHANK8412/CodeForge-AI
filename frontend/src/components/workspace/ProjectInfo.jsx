import React from 'react';
import { FaCheckCircle, FaChevronDown, FaChevronUp, FaShieldAlt, FaVial, FaLayerGroup } from 'react-icons/fa';

export default function ProjectInfo({
  projectName = 'AIForge Project',
  qualityScore = 0.0,
  testsPassed = 0,
  totalTests = 0,
  isVerified = false,
  agentStatuses = {},
  invalidFiles = [],
  isOpen = true,
  onToggle
}) {
  const agentList = [
    { name: 'Planner', key: 'planner' },
    { name: 'Architect', key: 'architect' },
    { name: 'Frontend', key: 'frontend' },
    { name: 'Backend', key: 'backend' },
    { name: 'Database', key: 'database' },
    { name: 'Reviewer', key: 'reviewer' },
    { name: 'Testing', key: 'testing' },
    { name: 'Documentation', key: 'documentation' }
  ];

  const getAgentStatus = (agentKey) => {
    const custom = agentStatuses[agentKey];
    if (custom) return custom;

    const hasInvalidFile = invalidFiles.some((f) => {
      const path = typeof f === 'string' ? f : f.path;
      if (agentKey === 'backend' && path?.startsWith('backend/')) return true;
      if (agentKey === 'frontend' && path?.startsWith('frontend/')) return true;
      if (agentKey === 'database' && path?.startsWith('database/')) return true;
      if (agentKey === 'testing' && path?.startsWith('tests/')) return true;
      return false;
    });

    if (hasInvalidFile) return { label: 'Incomplete', color: 'text-amber-400' };
    return { label: 'Complete', color: 'text-emerald-400' };
  };

  return (
    <div className="bg-[#090d16] border-b border-slate-800/80 w-full flex flex-col font-sans shrink-0 border-slate-800/60 select-none">
      <div
        onClick={onToggle}
        className="px-3 py-2 border-b border-slate-800/80 text-[11px] font-mono font-bold uppercase tracking-wider text-white flex items-center justify-between cursor-pointer hover:bg-slate-900/60 shrink-0"
      >
        <span className="flex items-center gap-1.5 font-bold">
          <FaLayerGroup className="text-cyan-400 w-3 h-3" /> Project & Agents
        </span>
        {isOpen ? <FaChevronDown className="w-2.5 h-2.5 text-slate-500" /> : <FaChevronUp className="w-2.5 h-2.5 text-slate-500" />}
      </div>

      {isOpen && (
        <div className="p-2.5 space-y-2 text-xs overflow-y-auto max-h-[220px] custom-scrollbar shrink-0">
          {/* Quality & Test Summary */}
          <div className="grid grid-cols-2 gap-1.5 text-center">
            <div className="bg-slate-950 p-1.5 rounded-lg border border-slate-800">
              <div className="text-[9px] text-slate-400 uppercase font-semibold">Quality</div>
              <div className={`font-mono font-extrabold text-sm ${qualityScore > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
                {qualityScore > 0 ? `${qualityScore}` : 'NOT VERIFIED'}
              </div>
            </div>

            <div className="bg-slate-950 p-1.5 rounded-lg border border-slate-800">
              <div className="text-[9px] text-slate-400 uppercase font-semibold">Project Tests</div>
              <div className={`font-mono font-extrabold text-sm ${totalTests > 0 ? 'text-cyan-400' : 'text-amber-400'}`}>
                {totalTests > 0 ? `${testsPassed}/${totalTests}` : 'UNRUN'}
              </div>
            </div>
          </div>

          {/* Agents Checklist */}
          <div>
            <div className="text-[9px] font-mono uppercase tracking-wider text-slate-400 mb-1 font-bold">
              Specialized Agents
            </div>
            <div className="grid grid-cols-1 gap-1 text-[11px]">
              {agentList.map((ag, idx) => {
                const st = getAgentStatus(ag.key);
                return (
                  <div key={idx} className="flex items-center justify-between px-2 py-1 rounded bg-slate-950/80 border border-slate-800/80">
                    <span className="font-medium text-slate-300">{ag.name} Agent</span>
                    <span className={`${st.color} font-mono text-[9px] flex items-center gap-1`}>
                      <FaCheckCircle className="w-2.5 h-2.5" /> {st.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
