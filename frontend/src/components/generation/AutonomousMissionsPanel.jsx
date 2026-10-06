import React, { useState } from 'react';
import {
  FaCheckCircle,
  FaHourglassHalf,
  FaClock,
  FaTimesCircle,
  FaRobot,
  FaFileCode,
  FaShieldAlt,
  FaVial,
  FaPlay,
  FaPlus
} from 'react-icons/fa';

export default function AutonomousMissionsPanel({
  missions = null,
  activeMissionId = null,
  onLaunchMission = null
}) {
  const [selectedMission, setSelectedMission] = useState(null);

  const missionList = missions || [];
  const current = selectedMission || missionList[0];

  if (!current) {
    return (
      <div className="bg-[#090d16] border border-slate-800/90 rounded-2xl p-5 font-sans text-xs text-slate-400 shadow-2xl">
        No missions yet. Missions appear here once a generation has run.
      </div>
    );
  }

  return (
    <div className="bg-[#090d16] border border-slate-800/90 rounded-2xl p-5 font-sans select-none shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <FaRobot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-white">Autonomous Mission Control</h3>
            <p className="text-xs text-slate-400">Multi-agent software engineering mission tracker & execution steps</p>
          </div>
        </div>

        <button
          onClick={() => onLaunchMission?.()}
          className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-md"
        >
          <FaPlus className="w-2.5 h-2.5" /> Launch Mission
        </button>
      </div>

      {/* Grid: Mission list on left, Step details on right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: Mission Selector Cards */}
        <div className="space-y-2.5">
          {missionList.map((m) => (
            <div
              key={m.id}
              onClick={() => setSelectedMission(m)}
              className={`p-3.5 rounded-xl border transition cursor-pointer ${
                current.id === m.id
                  ? 'bg-indigo-600/20 border-cyan-400 ring-1 ring-cyan-500/30'
                  : 'bg-slate-950 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold ${
                  m.status === 'COMPLETED' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-cyan-500/15 text-cyan-400'
                }`}>
                  {m.status}
                </span>
                <span className="text-xs font-mono font-bold text-white">{m.progress}%</span>
              </div>
              <div className="font-bold text-xs text-white truncate">{m.title}</div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 mt-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full transition-all duration-300"
                  style={{ width: `${m.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Right: Step-by-Step Execution Plan */}
        <div className="lg:col-span-2 p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div>
              <div className="text-xs font-bold text-white">{current.title}</div>
              <div className="text-[10px] text-slate-400">Step execution lifecycle</div>
            </div>
            <span className="text-xs font-mono font-bold text-cyan-400">{current.progress}% Complete</span>
          </div>

          {/* Steps Timeline */}
          <div className="space-y-2">
            {current.steps.map((st, idx) => (
              <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-900/70 border border-slate-800/80 rounded-lg text-xs">
                <div className="flex items-center gap-2.5">
                  {st.status === 'COMPLETED' ? (
                    <FaCheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : st.status === 'RUNNING' ? (
                    <FaHourglassHalf className="w-3.5 h-3.5 text-cyan-400 animate-spin shrink-0" />
                  ) : (
                    <FaClock className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                  )}
                  <span className="text-slate-200">{st.label}</span>
                </div>
                <span className="text-[10px] font-mono text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                  {st.agent}
                </span>
              </div>
            ))}
          </div>

          {/* Affected Files */}
          <div className="pt-2 border-t border-slate-800">
            <div className="text-[10px] uppercase font-mono font-bold text-slate-400 mb-1.5">Target Files:</div>
            <div className="flex flex-wrap gap-1.5">
              {current.affected_files.map((f, fIdx) => (
                <span key={fIdx} className="px-2 py-0.5 bg-slate-900 text-slate-300 rounded text-[10px] font-mono border border-slate-800 flex items-center gap-1">
                  <FaFileCode className="w-2.5 h-2.5 text-cyan-400" />
                  {f}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
