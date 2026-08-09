import React from 'react';
import { FaArrowRight, FaRocket } from 'react-icons/fa';

export default function CTA({ onStartBuilding, onExplore }) {
  return (
    <section className="py-20 bg-[#090d16] font-sans border-t border-slate-800/60 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/10 via-indigo-500/15 to-purple-500/10 blur-[100px] pointer-events-none" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        <div className="bg-slate-950/90 border border-slate-800 rounded-3xl p-10 sm:p-14 shadow-2xl backdrop-blur-xl">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-2xl mx-auto mb-6 shadow-xl shadow-cyan-500/20 border border-cyan-400/30">
            <FaRocket />
          </div>

          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-4">
            Turn Your Idea Into Software.
          </h2>

          <p className="text-base sm:text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Stop starting from an empty repository. Let AIForge's team of specialized agents plan, build, test, and document your next project.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={onStartBuilding}
              className="w-full sm:w-auto px-8 py-4 text-sm font-bold text-white bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 rounded-xl shadow-xl shadow-cyan-500/20 border border-cyan-400/30 flex items-center justify-center gap-2 transition-all transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
            >
              <span>Start Building</span>
              <FaArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={onExplore}
              className="w-full sm:w-auto px-7 py-4 text-sm font-semibold text-slate-300 hover:text-white bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl transition flex items-center justify-center gap-2"
            >
              <span>Explore AIForge</span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
