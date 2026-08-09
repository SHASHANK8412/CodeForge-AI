import React from 'react';
import { getScoreClassification } from '../../utils/qualityScore';

export default function OverallScore({ score = 96.0 }) {
  const classification = getScoreClassification(score);

  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-8 shadow-xl font-sans text-center relative overflow-hidden flex flex-col items-center justify-center">
      {/* Subtle Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 mb-6">
        Overall Quality Score
      </h3>

      {/* Circle Badge Container */}
      <div className="w-36 h-36 rounded-full border-4 border-cyan-500/40 bg-slate-900/90 flex flex-col items-center justify-center shadow-2xl shadow-cyan-500/10 mb-4">
        <span className="text-4xl font-black font-mono text-white tracking-tight">{score}</span>
        <span className="text-xs font-mono font-medium text-slate-400">/ 100</span>
      </div>

      <div className={`px-4 py-1.5 rounded-full border text-xs font-bold uppercase tracking-widest ${classification.badgeBg} ${classification.color}`}>
        {classification.label}
      </div>
    </div>
  );
}
