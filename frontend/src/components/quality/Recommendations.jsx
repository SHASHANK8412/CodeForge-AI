import React from 'react';
import { FaLightbulb, FaExclamationCircle, FaInfoCircle } from 'react-icons/fa';

export default function Recommendations({ recommendations = [] }) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-6 shadow-xl font-sans">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <FaLightbulb className="text-yellow-400" /> AIForge Optimization Recommendations
        </h3>
        <span className="font-mono text-xs font-bold text-slate-400">
          {recommendations.length} Actionable Items
        </span>
      </div>

      <div className="space-y-3">
        {recommendations && recommendations.length > 0 ? (
          recommendations.map((rec, idx) => {
            const isHigh = rec.priority === 'HIGH';
            const isMedium = rec.priority === 'MEDIUM';

            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border flex items-start gap-3.5 text-xs ${
                  isHigh
                    ? 'bg-rose-950/20 border-rose-500/30 text-rose-200'
                    : isMedium
                    ? 'bg-amber-950/20 border-amber-500/30 text-amber-200'
                    : 'bg-slate-900/80 border-slate-800 text-slate-300'
                }`}
              >
                {isHigh ? (
                  <FaExclamationCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                ) : (
                  <FaInfoCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                )}

                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-white text-xs">{rec.title}</span>
                    <span
                      className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
                        isHigh
                          ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                          : isMedium
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                          : 'bg-slate-900 text-slate-400 border-slate-800'
                      }`}
                    >
                      Priority: {rec.priority}
                    </span>
                  </div>
                  <p className="leading-relaxed text-slate-300">{rec.description}</p>
                </div>
              </div>
            );
          })
        ) : (
          <p className="text-xs text-slate-500 italic">No further optimization recommendations required.</p>
        )}
      </div>
    </div>
  );
}
